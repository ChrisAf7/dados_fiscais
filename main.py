from src.client import SiconfiClient
from src.extract import RGFExtractor
from src.transform import RGFTransformer
from src.pipeline import RGFPipeline
from src.config import PipelineConfig
from src.outputs import OutputManager
from src.repository import MunicipioRepository
import pandas as pd

# Configuração do pipeline

client = SiconfiClient()
extractor = RGFExtractor(client)
transformer = RGFTransformer()
repo=MunicipioRepository()
output=OutputManager()
config = PipelineConfig(
    paralelo=True,
    max_workers=8
)

pipeline = RGFPipeline(extractor, transformer, config)

df=pipeline.coletar_estado_recente("Rondônia",[2024,2025],repo)
output.salvar_csv(df, "Rondônia_recente")
