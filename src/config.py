class PipelineConfig:
    def __init__(
        self,
        paralelo=True,
        max_workers=5,
        timeout=10,
        retries=2
    ):
        self.paralelo = paralelo
        self.max_workers = max_workers
        self.timeout = timeout
        self.retries = retries
