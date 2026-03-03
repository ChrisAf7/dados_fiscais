import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)

class RGFPipeline:
    def __init__(self, extractor,transformer,config):
        self.extractor = extractor
        self.config = config
        self.transformer = transformer

    def _task_uf(self, uf, ano):
        return self.extractor.extrair_uf(uf, ano)

    def run_ufs(self, ufs, anos):
        tarefas = [(uf, ano) for ano in anos for uf in ufs]
        resultados = []

        if self.config.paralelo:
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                futures = [executor.submit(self._task_uf, uf, ano) for uf, ano in tarefas]

                for future in as_completed(futures):
                    try:
                        resultados.append(future.result())
                    except Exception as e:
                        print(f"Erro na tarefa: {e}")
        else:
            for uf, ano in tarefas:
                resultados.append(self._task_uf(uf, ano))

        return self.transformer.filtrar(resultados, uf=True, periodo=3)

    def _task_municipio(self, municipio, ano, periodo, permitir_fallback=True):

        # Tentativa 1: formato normal (Q)
        try:
            items = self.extractor.extrair_municipio(
                municipio,
                ano,
                periodo=periodo,
                simplificado=False
            )

            if items:
                return {
                    "ente": "municipio",
                    "codigo": municipio,
                    "ano": ano,
                    "periodo": periodo,
                    "simplificado": False,
                    "items": items
                }

        except Exception as e:
            print(f"Erro em {municipio}, {ano}, normal:", e)


        # Tentativa 2: formato simplificado (S), se autorizado
        if permitir_fallback:
            try:
                items = self.extractor.extrair_municipio(
                    municipio,
                    ano,
                    periodo=periodo,
                    simplificado=True
                )

                if items:
                    return {
                        "ente": "municipio",
                        "codigo": municipio,
                        "ano": ano,
                        "periodo": periodo,
                        "simplificado": True,
                        "items": items
                    }

            except Exception as e:
                print(f"Erro em {municipio}, {ano}, simplificado:", e)



        return None


    def run_municipios(self, municipios, anos, periodo, permitir_fallback=True):

        tarefas = [(m, a) for a in anos for m in municipios]
        resultados = []

        if self.config.paralelo:
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                futures = [
                    executor.submit(
                        self._task_municipio,
                        mun,
                        ano,
                        periodo,
                        permitir_fallback
                    )
                    for mun, ano in tarefas
                ]

                for future in tqdm(
                    as_completed(futures),
                    total=len(futures),
                    desc="Processando municípios"
                ):
                    try:
                        res = future.result()
                        if res and res.get("items"):
                            resultados.append(res)

                    except Exception as e:
                        logger.error(f"Erro inesperado: {e}")

        else:
            for mun, ano in tqdm(tarefas, desc="Processando municípios"):
                res = self._task_municipio(
                    mun,
                    ano,
                    periodo,
                    permitir_fallback
                )
                if res and res.get("items"):
                    resultados.append(res)

        df = self.transformer.filtrar(resultados)

        return df


    def extrair_periodo_mais_recente(self, municipio, anos, periodos=(3,2,1)):
        for ano in sorted(anos, reverse=True):
            for periodo in periodos:
                for simplificado in (False, True):
                    try:
                        items = self.extractor.extrair_municipio(
                            municipio,
                            ano,
                            periodo=periodo,
                            simplificado=simplificado
                        )

                        if items:
                            return {
                                "ente": "municipio",
                                "codigo": municipio,
                                "ano": ano,
                                "periodo": periodo,
                                "simplificado": simplificado,
                                "items": items
                            }

                    except Exception:
                        continue

        return None


    def _task_municipio_recente(self, municipio, anos):
        return self.extrair_periodo_mais_recente(municipio, anos)

    def run_municipios_recente(self, municipios, anos):

        tarefas = municipios
        resultados = []

        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = [
                executor.submit(self._task_municipio_recente, mun, anos)
                for mun in tarefas
            ]

            for future in tqdm(as_completed(futures), total=len(futures), desc="Buscando dados mais recentes"):
                res = future.result()

                if res:
                    resultados.append(res)
                    
        df = self.transformer.filtrar(
            resultados,
        )

        return df
    
    def coletar_estado_recente(self, estado_nome, anos, repo):
        """Coleta os dados mais recentes para todos os municípios de um estado específico."""
        municipios = repo.get_by_uf(estado_nome)
        return self.run_municipios_recente(municipios, anos)
        

    def _task_municipio_periodos(
        self,
        municipio,
        ano,
        periodo_normal,
        periodo_simplificado,
        usar_fallback=True
    ):
        # Primeiro tenta formato normal
        try:
            items = self.extractor.extrair_municipio(
                municipio,
                ano,
                periodo=periodo_normal,
                simplificado=False
            )

            if items:
                return items

        except Exception:
            pass

        # Se permitido, tenta fallback no simplificado
        if usar_fallback:
            try:
                return self.extractor.extrair_municipio(
                    municipio,
                    ano,
                    periodo=periodo_simplificado,
                    simplificado=True
                )
            except Exception:
                return None

        return None



    def atualizar_base_anual(self, anos,repo):
        """Pipeline pensada para atualização periódica"""
        municipios = repo.get_all()
        return self.run_municipios(municipios, anos)