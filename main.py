"""
Ponto de entrada da pipeline de dados fiscais.
Execute: python main.py
"""
import asyncio
import logging

from src.config import PipelineConfig
from src.outputs import OutputManager
from src.pipeline import RGFPipeline
from src.repository import MunicipioRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


async def main():
    config = PipelineConfig(
        max_concurrent_requests=12,
        max_transform_workers=4,
        salvar_csv=True,
        salvar_parquet=True,
    )
    output = OutputManager(config)
    repo   = MunicipioRepository()

    async with RGFPipeline(config) as p:

        anos = list(range(2019, 2025))
        ufs_nordeste = [21, 22, 23, 24, 25, 26, 27, 28, 29]

        # ── 1. RGF — Estados do Nordeste ─────────────────────────────────────
        df = await p.run_ufs(ufs_nordeste, anos)
        output.salvar(df, "rgf_ufs_nordeste_2019_2024")

        # ── 2. RGF — Todos os municípios do Ceará ────────────────────────────
        df = await p.coletar_estado_recente("Ceará", anos, repo)
        output.salvar(df, "rgf_municipios_ceara_recente")

        # ── 3. RGF — Municípios específicos com fallback ──────────────────────
        municipios = [2304400, 2611606, 2927408]   # Fortaleza, Recife, Salvador
        df = await p.run_municipios(municipios, anos, periodo=1)
        output.salvar(df, "rgf_capitais_ne_2019_2024")

        # ── 4. RREO — Receitas do Ceará ───────────────────────────────────────
        df = await p.run_rreo([23], anos, anexo="receitas")
        output.salvar(df, "rreo_receitas_ce_2019_2024")

        # ── 5. RREO — Resultado primário do Nordeste ──────────────────────────
        df = await p.run_rreo(ufs_nordeste, anos, anexo="resultado")
        output.salvar(df, "rreo_resultado_nordeste_2019_2024")

        # ── 6. DCA — Balanço anual do Ceará ───────────────────────────────────
        df = await p.run_dca([23], anos)
        output.salvar(df, "dca_ceara_2019_2024")

        # ── 7. Atualização completa da base de municípios ─────────────────────
        df = await p.atualizar_base_anual([2024], repo)
        output.salvar(df, "rgf_todos_municipios_2024")


if __name__ == "__main__":
    asyncio.run(main())