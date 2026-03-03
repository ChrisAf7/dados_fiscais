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
            "co_tipo_demonstrativo": "RGF",
            "no_anexo": "RGF-Anexo 02",
            "co_poder": "E",
            "id_ente": co_ibge,
        }
        items = await self.client.get("rgf", params)
        for item in items:
            item.update({"_co_ibge": co_ibge, "_ano": ano,
                        "_periodo": periodo, "_relatorio": "RGF-UF",
                        "_simplificado": False})
        return items

    async def extrair_municipio(
        self, co_ibge: int, ano: int, periodo: int = 1, simplificado: bool = False
    ) -> list[dict]:
        params = {
            "an_exercicio": ano,
            "in_periodicidade": "S" if simplificado else "Q",
            "nr_periodo": periodo,
            "co_tipo_demonstrativo": "RGF Simplificado" if simplificado else "RGF",
            "no_anexo": "RGF-Anexo 02",
            "co_poder": "E",
            "id_ente": co_ibge,
        }
        items = await self.client.get("rgf", params)
        for item in items:
            item.update({"_co_ibge": co_ibge, "_ano": ano,
                        "_periodo": periodo, "_relatorio": "RGF-Municipio",
                        "_simplificado": simplificado})
        return items
    
class DCAExtractor:
    """Extrai DCA para estados e municípios."""
    # Implementação similar a RGFExtractor, adaptando parâmetros e metadados
    # conforme necessário. O processo de fallback não se aplica ao DCA.
    pass

class RREOExtractor:
    pass