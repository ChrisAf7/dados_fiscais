class RGFExtractor:
    def __init__(self, client):
        self.client = client

    def extrair_uf(self, uf, ano, periodo=3):
        params = {
            "an_exercicio": ano,
            "in_periodicidade": "Q",
            "nr_periodo": periodo,
            "co_tipo_demonstrativo": "RGF",
            "no_anexo": "RGF-Anexo 02",
            "co_poder":"E",
            "id_ente": uf
        }
        return self.client.fetch(params)

    def extrair_municipio(self, municipio, ano, periodo=1, simplificado=False):
        if simplificado:
            params = {
                "an_exercicio": ano,
                "in_periodicidade": "S",
                "nr_periodo": periodo,
                "co_tipo_demonstrativo": "RGF Simplificado",
                "no_anexo": "RGF-Anexo 02",
                "co_poder":"E",
                "id_ente": municipio
            }
        else:
            params = {
                "an_exercicio": ano,
                "in_periodicidade": "Q",
                "nr_periodo": periodo,
                "co_tipo_demonstrativo": "RGF",
                "no_anexo": "RGF-Anexo 02",
                "co_poder":"E",
                "id_ente": municipio
            }

        return self.client.fetch(params)
    

