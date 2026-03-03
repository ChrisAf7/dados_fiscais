"""
Pipeline principal — coleta 100% assíncrona + transformação paralela.
"""
import asyncio
import logging
from concurrent.futures import ProcessPoolExecutor
from typing import Iterable

import pandas as pd
from tqdm import tqdm

from .client import SiconfiClient
from .config import PipelineConfig
from .extract import RGFExtractor, RREOExtractor, DCAExtractor
from .transform import transformar_lote

logger = logging.getLogger(__name__)


class RGFPipeline:

    def __init__(self, config: PipelineConfig | None = None):
        self.config = config or PipelineConfig()
        self._client: SiconfiClient | None = None
        self._executor: ProcessPoolExecutor | None = None

    async def __aenter__(self) -> "RGFPipeline":
        self._client = SiconfiClient(
            max_concurrent=self.config.max_concurrent_requests,
            timeout_seconds=self.config.timeout_seconds,
            max_retries=self.config.max_retries,
            retry_delay=self.config.retry_delay,
            request_delay=self.config.request_delay,
        )
        await self._client.__aenter__()
        self._executor = ProcessPoolExecutor(
            max_workers=self.config.max_transform_workers
        )
        return self

    async def __aexit__(self, *_) -> None:
        await self._client.__aexit__(None, None, None)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._executor.shutdown, True)

    # ── RGF — UFs ─────────────────────────────────────────────────────────────

    async def run_ufs(
        self,
        ufs: Iterable[int],
        anos: Iterable[int],
        periodos: Iterable[int] | None = None,
    ) -> pd.DataFrame:
        periodos = list(periodos or self.config.periodos_rgf_uf)
        ext = RGFExtractor(self._client)
        tarefas = [
            ext.extrair_uf(uf, ano, periodo)
            for ano in anos
            for uf in ufs
            for periodo in periodos
        ]
        return await self._executar(tarefas, desc="RGF UFs")

    # ── RGF — Municípios ──────────────────────────────────────────────────────

    async def run_municipios(
        self,
        municipios: Iterable[int],
        anos: Iterable[int],
        periodo: int = 1,
        permitir_fallback: bool = True,
    ) -> pd.DataFrame:
        ext = RGFExtractor(self._client)
        tarefas = [
            ext.extrair_municipio_com_fallback(mun, ano, periodo)
            if permitir_fallback
            else ext.extrair_municipio(mun, ano, periodo)
            for ano in anos
            for mun in municipios
        ]
        return await self._executar(tarefas, desc="RGF Municípios")

    async def run_municipios_recente(
        self,
        municipios: Iterable[int],
        anos: Iterable[int],
        periodos: tuple[int, ...] = (3, 2, 1),
    ) -> pd.DataFrame:
        ext = RGFExtractor(self._client)
        tarefas = [
            self._buscar_mais_recente(ext, mun, list(anos), list(periodos))
            for mun in municipios
        ]
        return await self._executar(tarefas, desc="RGF Municípios (recente)")

    async def _buscar_mais_recente(
        self,
        ext: RGFExtractor,
        municipio: int,
        anos: list[int],
        periodos: list[int],
    ) -> list[dict]:
        for ano in sorted(anos, reverse=True):
            for periodo in periodos:
                for simplificado in (False, True):
                    items = await ext.extrair_municipio(
                        municipio, ano, periodo, simplificado
                    )
                    if items:
                        return items
        return []

    async def coletar_estado_recente(
        self,
        nome_uf: str,
        anos: Iterable[int],
        repo,
    ) -> pd.DataFrame:
        municipios = repo.get_by_uf(nome_uf)
        return await self.run_municipios_recente(municipios, list(anos))

    async def atualizar_base_anual(
        self,
        anos: Iterable[int],
        repo,
    ) -> pd.DataFrame:
        municipios = repo.get_all()
        return await self.run_municipios(municipios, list(anos))

    # ── RREO ──────────────────────────────────────────────────────────────────

    async def run_rreo(
        self,
        entes: Iterable[int],
        anos: Iterable[int],
        anexo: str = "receitas",
        periodos: Iterable[int] | None = None,
    ) -> pd.DataFrame:
        periodos = list(periodos or self.config.periodos_rreo)
        ext = RREOExtractor(self._client)
        tarefas = [
            ext.extrair(ente, ano, periodo, anexo)
            for ano in anos
            for ente in entes
            for periodo in periodos
        ]
        return await self._executar(tarefas, desc=f"RREO {anexo}")

    # ── DCA ───────────────────────────────────────────────────────────────────

    async def run_dca(
        self,
        entes: Iterable[int],
        anos: Iterable[int],
    ) -> pd.DataFrame:
        ext = DCAExtractor(self._client)
        tarefas = [
            ext.extrair(ente, ano)
            for ano in anos
            for ente in entes
        ]
        return await self._executar(tarefas, desc="DCA")

    # ── Interno ───────────────────────────────────────────────────────────────

    async def _executar(
        self, tarefas: list, desc: str = "Coletando"
    ) -> pd.DataFrame:
        logger.info("[%s] Iniciando %d requisições...", desc, len(tarefas))

        # Progresso manual — mais estável que tqdm_asyncio.gather
        resultados = []
        with tqdm(total=len(tarefas), desc=desc) as barra:
            for coro in asyncio.as_completed(tarefas):
                try:
                    resultado = await coro
                    resultados.append(resultado)
                except Exception as e:
                    logger.warning("Tarefa falhou: %s", e)
                finally:
                    barra.update(1)
            # DEBUG TEMPORÁRIO

        lotes = [r for r in resultados if r]

        if not lotes:
            logger.warning("[%s] Nenhum dado coletado.", desc)
            return pd.DataFrame()

        logger.info("[%s] Transformando %d lotes em paralelo...", desc, len(lotes))
        loop = asyncio.get_running_loop()
        futures = [
            loop.run_in_executor(self._executor, transformar_lote, lote)
            for lote in lotes
        ]
        dfs = await asyncio.gather(*futures)

        df_final = pd.concat(
            [d for d in dfs if not d.empty], ignore_index=True
        )
        logger.info("[%s] Concluído: %d registros.", desc, len(df_final))
        return df_final