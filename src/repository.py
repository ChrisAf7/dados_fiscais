"""Repositório de municípios — leitura e filtragem do cadastro IBGE."""
import logging
from functools import lru_cache

import pandas as pd

logger = logging.getLogger(__name__)


class MunicipioRepository:
    """
    Carrega e filtra o cadastro de municípios a partir de um arquivo Excel.

    Colunas esperadas:
        - 'Código Município Completo': código IBGE de 7 dígitos
        - 'Nome_UF': nome por extenso da UF (ex: 'Ceará')
        - 'UF': sigla da UF (ex: 'CE')  — opcional
    """

    def __init__(self, path: str = "data/codigo_municipios.xlsx"):
        self._df = pd.read_excel(path, dtype={"Código Município Completo": int})
        logger.info("Repositório carregado: %d municípios.", len(self._df))

    @lru_cache(maxsize=64)
    def get_by_uf(self, nome_uf: str) -> list[int]:
        """Retorna códigos IBGE dos municípios de uma UF (pelo nome)."""
        mask = self._df["Nome_UF"].str.strip().str.lower() == nome_uf.strip().lower()
        resultado = self._df.loc[mask, "Código Município Completo"].tolist()
        if not resultado:
            logger.warning("Nenhum município encontrado para UF='%s'.", nome_uf)
        return resultado

    @lru_cache(maxsize=1)
    def get_all(self) -> list[int]:
        """Retorna todos os códigos IBGE."""
        return self._df["Código Município Completo"].tolist()

    def get_by_codigos(self, codigos: list[int]) -> pd.DataFrame:
        """Retorna DataFrame filtrado por lista de códigos IBGE."""
        return self._df[self._df["Código Município Completo"].isin(codigos)].copy()