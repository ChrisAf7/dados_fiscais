import re
import unicodedata
import pandas as pd


class RGFTransformer:
    def __init__(self):
        self.variaveis_uf = {
            'DÍVIDA CONSOLIDADA - DC (I)',
            'DÍVIDA CONSOLIDADA LÍQUIDA (DCL) (III) = (I - II)',
            'Disponibilidade de Caixa',
            'Disponibilidade de Caixa Bruta',
            'RECEITA CORRENTE LÍQUIDA - RCL (IV)',
            'RECEITA CORRENTE LÍQUIDA AJUSTADA PARA CÁLCULO DOS LIMITES DE ENDIVIDAMENTO (VI) = (IV - V)',
            r'% da DC sobre a RCL AJUSTADA (I/VI)',
            r'% da DCL sobre a RCL AJUSTADA (III/VI)',
            'Precatórios Posteriores a 05/05/2000 (Não incluídos na DC)',
            'Precatórios Posteriores a 05/05/2000 (inclusive) Vencidos e Não Pagos',
            'Empréstimos',
            'Parcelamento e Renegociação de Dívidas',
            'Demais Dívidas Contratuais'
        }

        self.variaveis_municipio = {
            'DÍVIDA CONSOLIDADA - DC (I)',
            'DÍVIDA CONSOLIDADA LÍQUIDUIDA (DCL) (III) = (I - II)',
            'Disponibilidade de Caixa',
            'Disponibilidade de Caixa Bruta',
            'RECEITA CORRENTE LÍQUIDA - RCL',
            'RECEITA CORRENTE LÍQUIDA - RCL (IV)',
            'RECEITA CORRENTE LÍQUIDA AJUSTADA PARA CÁLCULO DOS LIMITES DE ENDIVIDAMENTO (VI) = (IV - V)',
            r'% da DC sobre a RCL AJUSTADA (I/VI)',
            r'% da DCL sobre a RCL AJUSTADA (III/VI)',
            'Precatórios Posteriores a 05/05/2000 (Não incluídos na DC)',
            'Precatórios Posteriores a 05/05/2000 (inclusive) Vencidos e Não Pagos'
        }

        self.rename_map = {
            'RECEITA CORRENTE LÍQUIDA - RCL': "RECEITA CORRENTE LÍQUIDA",
            'RECEITA CORRENTE LÍQUIDA - RCL (IV)': 'RECEITA CORRENTE LÍQUIDA',
            'RECEITA CORRENTE LÍQUIDA AJUSTADA PARA CÁLCULO DOS LIMITES DE ENDIVIDAMENTO (VI) = (IV - V)':
                'RECEITA CORRENTE LÍQUIDA AJUSTADA PARA CÁLCULO DOS LIMITES DE ENDIVIDAMENTO',
            '% da DCL sobre a RCL AJUSTADA (III/VI)': '% da DCL sobre a RCL AJUSTADA',
            'DÍVIDA CONSOLIDADA - DC (I)': 'DÍVIDA CONSOLIDADA',
            'DÍVIDA CONSOLIDADA LÍQUIDA (DCL) (III) = (I - II)': 'DÍVIDA CONSOLIDADA LÍQUIDA',
            'Precatórios Posteriores a 05/05/2000 (inclusive) Vencidos e Não Pagos':
                'Precatórios (inclusive) Vencidos e Não Pagos',
            'Precatórios Posteriores a 05/05/2000 (Não incluídos na DC)':
                'Precatórios (Não incluídos na DC)'
        }


    @staticmethod
    def limpar_nome_municipio(texto):
        if not isinstance(texto, str):
            return ''
        texto = re.sub(r'^Prefeitura Municipal de\s+', '', texto, flags=re.IGNORECASE)
        texto = re.sub(r'\s*-\s*[A-Z]{2}$', '', texto, flags=re.IGNORECASE)
        texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
        return texto.strip().upper()

    def filtrar(self, extracoes):

        registros = []

        if not extracoes:
            return pd.DataFrame()

        for bloco in extracoes:

            if not isinstance(bloco, dict):
                continue

            items = bloco.get("items", [])
            if not items:
                continue

            ano = bloco.get("ano")
            periodo = bloco.get("periodo")
            simplificado = bloco.get("simplificado")
            codigo = bloco.get("codigo")
            ente = bloco.get("ente")

            variaveis = (
                self.variaveis_uf if ente == "uf"
                else self.variaveis_municipio
            )

            alvo = (
                f"Até o {periodo}º Semestre"
                if simplificado
                else f"Até o {periodo}º Quadrimestre"
            )

            for item in items:
                if not isinstance(item, dict):
                    continue

                conta = item.get("conta")
                coluna = item.get("coluna")

                if conta not in variaveis:
                    continue

                if coluna != alvo:
                    continue

                registros.append({
                    "ano": ano,
                    "ente": ente,
                    "codigo": codigo,
                    "instituicao": item.get("instituicao"),
                    "conta": self.rename_map.get(conta, conta),
                    "valor": item.get("valor"),
                    "coluna": coluna
                })
        df=pd.DataFrame(registros)
        df["instituicao"]=df["instituicao"].apply(self.limpar_nome_municipio)
        return df





