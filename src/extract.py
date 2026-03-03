"""Extratores assíncronos para RGF, RREO e DCA."""
import logging
from .client import SiconfiClient

logger = logging.getLogger(__name__)


class RGFExtractor:
    """Extrai RGF para estados e municípios, com fallback simplificado."""

    def __init__(self, client: SiconfiClient):
        self.client = client

    async def extrair_uf(self, co_ibge: int, ano: int, periodo: int = 3) -> list[dict]:
        params = {
            "an_exercicio": ano,
            "in_periodicidade": "Q",
            "nr_periodo": periodo,
            "co_tipo_demonstrativo": "RGF-Anexo 02",
            "no_tipo_resultado": "Consolidado",
            "co_ente": co_ibge,
        }
        items = await self.client.get("rgf", params)
        for item in items:
            item.update({"_co_ibge": co_ibge, "_ano": ano,
                         "_periodo": periodo, "_relatorio": "RGF-UF",
                         "_simplificado": False})
        return items

    async def extrair_municipio(
        self,
        co_ibge: int,
        ano: int,
        periodo: int = 1,
        simplificado: bool = False,
    ) -> list[dict]:
        params = {
            "an_exercicio": ano,
            "in_periodicidade": "S" if simplificado else "Q",
            "nr_periodo": periodo,
            "co_tipo_demonstrativo": (
                "RGF-Anexo 03 Simplificado" if simplificado else "RGF-Anexo 03"
            ),
            "no_tipo_resultado": "Consolidado",
            "co_ente": co_ibge,
        }
        items = await self.client.get("rgf", params)
        for item in items:
            item.update({"_co_ibge": co_ibge, "_ano": ano,
                         "_periodo": periodo, "_relatorio": "RGF-Municipio",
                         "_simplificado": simplificado})
        return items

    async def extrair_municipio_com_fallback(
        self, co_ibge: int, ano: int, periodo: int = 1
    ) -> list[dict]:
        """Tenta formato completo; em caso de retorno vazio, usa simplificado."""
        items = await self.extrair_municipio(co_ibge, ano, periodo, simplificado=False)
        if not items:
            logger.info("Fallback simplificado | ibge=%s ano=%s", co_ibge, ano)
            items = await self.extrair_municipio(co_ibge, ano, 1, simplificado=True)
        return items


class RREOExtractor:
    """Extrai RREO — Receitas, Despesas, Resultado Primário e DCL."""

    # Mapa: chave amigável → (tipo_demonstrativo, tipo_resultado)
    ANEXOS = {
        "receitas":  ("RREO-Anexo 01", "Demonstrativo da Receita Orçamentária"),
        "despesas":  ("RREO-Anexo 02", "Demonstrativo da Despesa por Função"),
        "resultado": ("RREO-Anexo 06", "Demonstrativo do Resultado Primário"),
        "dcl":       ("RREO-Anexo 09", "Demonstrativo da Dívida Consolidada Líquida"),
    }

    def __init__(self, client: SiconfiClient):
        self.client = client

    async def extrair(
        self, co_ibge: int, ano: int, periodo: int, anexo: str = "receitas"
    ) -> list[dict]:
        if anexo not in self.ANEXOS:
            raise ValueError(f"Anexo inválido: '{anexo}'. Disponíveis: {list(self.ANEXOS)}")

        tipo_demo, tipo_resultado = self.ANEXOS[anexo]
        params = {
            "an_exercicio": ano,
            "in_periodicidade": "B",
            "nr_periodo": periodo,
            "co_tipo_demonstrativo": tipo_demo,
            "no_tipo_resultado": tipo_resultado,
            "co_ente": co_ibge,
        }
        items = await self.client.get("rreo", params)
        for item in items:
            item.update({"_co_ibge": co_ibge, "_ano": ano,
                         "_periodo": periodo, "_relatorio": f"RREO-{anexo}",
                         "_simplificado": False})
        return items


class DCAExtractor:
    """Extrai DCA — Declaração de Contas Anuais."""

    def __init__(self, client: SiconfiClient):
        self.client = client

    async def extrair(self, co_ibge: int, ano: int) -> list[dict]:
        params = {
            "an_exercicio": ano,
            "in_periodicidade": "A",
            "nr_periodo": 1,
            "co_tipo_demonstrativo": "DCA",
            "co_ente": co_ibge,
        }
        items = await self.client.get("dca", params)
        for item in items:
            item.update({"_co_ibge": co_ibge, "_ano": ano,
                         "_periodo": 1, "_relatorio": "DCA",
                         "_simplificado": False})
        return items