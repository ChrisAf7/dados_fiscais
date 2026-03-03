from dataclasses import dataclass, field

@dataclass
class PipelineConfig:
    max_concurrent_requests: int = 10   # semáforo async (substitui max_workers)
    max_transform_workers: int = 4      # ProcessPoolExecutor para transformação
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay: float = 2.0
    output_dir: str = "outputs"
    salvar_csv: bool = True
    salvar_parquet: bool = True
    periodos_rgf_uf: list[int] = field(default_factory=lambda: [3])
    periodos_rgf_municipio: list[int] = field(default_factory=lambda: [1])
    periodos_rreo: list[int] = field(default_factory=lambda: [1, 2, 3, 4, 5, 6])