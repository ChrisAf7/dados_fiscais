"""Persistência dos dados — CSV e Parquet."""
import logging
from pathlib import Path

import pandas as pd

from .config import PipelineConfig

logger = logging.getLogger(__name__)


class OutputManager:
    def __init__(self, config: PipelineConfig | None = None):
        self.config = config or PipelineConfig()
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def salvar(self, df: pd.DataFrame, nome: str) -> None:
        """Salva nos formatos configurados. Ignora silenciosamente se vazio."""
        if df.empty:
            logger.warning("DataFrame vazio — nada salvo para '%s'.", nome)
            return

        if self.config.salvar_csv:
            path = self.output_dir / f"{nome}.csv"
            df.to_csv(path, index=False, encoding="utf-8-sig")
            logger.info("CSV salvo: %s (%d linhas)", path, len(df))

        if self.config.salvar_parquet:
            path = self.output_dir / f"{nome}.parquet"
            df.to_parquet(path, index=False, engine="pyarrow")
            logger.info("Parquet salvo: %s (%d linhas)", path, len(df))