import requests

class SiconfiClient:
    BASE_URL = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/rgf"

    def fetch(self, params: dict):
        response = requests.get(self.BASE_URL, params=params)
        response.raise_for_status()
        return response.json()["items"]
