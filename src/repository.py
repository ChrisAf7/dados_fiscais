import pandas as pd

class MunicipioRepository:
    def __init__(self, path="data/codigo_municipios.xlsx"):
        self.df = pd.read_excel(path)

    def get_by_uf(self, nome_uf):
        return (
            self.df[self.df["Nome_UF"] == nome_uf]["Código Município Completo"]
            .astype(int)
            .tolist()
        )

    def get_all(self):
        return self.df["Código Município Completo"].astype(int).tolist()



