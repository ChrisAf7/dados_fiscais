from pathlib import Path

class OutputManager:
    def __init__(self, base_path="outputs"):
        self.base = Path(base_path)

    def salvar_csv(self, df, nome):
        caminho = self.base / f"{nome}.csv"
        df.to_csv(caminho, index=False)
        return caminho
