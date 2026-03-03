"""
Transformações de dados — executadas em paralelo via ProcessPoolExecutor.
Funções puras: recebem lista de dicts brutos, retornam DataFrame padronizado.
"""
import logging
import pandas as pd

logger = logging.getLogger(__name__)

# ── Variáveis de interesse por relatório ──────────────────────────────────────

VARIAVEIS_RGF = {
    "Dívida Consolidada - DC",
    "Dívida Consolidada Líquida - DCL",
    "Receita Corrente Líquida - RCL",
    "Receita Corrente Líquida Ajustada - RCLA",
    "% da DC sobre a RCL",
    "% da DCL sobre a RCL",
    "Precatórios Vencidos e Não Pagos",
    "Disponibilidade de Caixa Bruta",
    "Disponibilidade de Caixa Líquida",
    "Empréstimos e Financiamentos",
    "Parcelamentos de Dívidas",
}

VARIAVEIS_RREO_RECEITAS = {
    "RECEITAS CORRENTES",
    "RECEITAS DE CAPITAL",
    "RECEITA TRIBUTÁRIA",
    "RECEITA DE TRANSFERÊNCIAS CONSTITUCIONAIS E LEGAIS",
    "TOTAL DAS RECEITAS",
}

VARIAVEIS_RREO_RESULTADO = {
    "RESULTADO PRIMÁRIO",
    "META DE RESULTADO PRIMÁRIO",
    "RESULTADO NOMINAL",
}

VARIAVEIS_RREO_DCL = {
    "Dívida Consolidada Líquida - DCL",
    "Receita Corrente Líquida - RCL",
    "% da DCL sobre a RCL",
}

VARIAVEIS_DCA = {
    "Ativo Total",
    "Passivo Total",
    "Patrimônio Líquido",
    "Resultado Patrimonial",
}

_VARIAVEIS_POR_RELATORIO: dict[str, set[str]] = {
    "RGF-UF":          VARIAVEIS_RGF,
    "RGF-Municipio":   VARIAVEIS_RGF,
    "RREO-receitas":   VARIAVEIS_RREO_RECEITAS,
    "RREO-despesas":   set(),               # sem filtro — trazer tudo
    "RREO-resultado":  VARIAVEIS_RREO_RESULTADO,
    "RREO-dcl":        VARIAVEIS_RREO_DCL,
    "DCA":             VARIAVEIS_DCA,
}

COLUNAS_SAIDA = [
    "exercicio", "periodo", "relatorio", "co_ibge",
    "instituicao", "uf", "conta", "valor", "simplificado",
]


def transformar_lote(items: list[dict]) -> pd.DataFrame:
    """
    Transforma um lote de itens brutos em DataFrame padronizado.
    Função pura — segura para ProcessPoolExecutor.

    Args:
        items: lista de dicts retornados pelo extrator (campos _* internos)

    Returns:
        DataFrame com colunas COLUNAS_SAIDA, ou vazio se sem dados válidos.
    """
    if not items:
        return pd.DataFrame(columns=COLUNAS_SAIDA)

    df = pd.DataFrame(items)
    relatorio = df["_relatorio"].iloc[0]
    variaveis = _VARIAVEIS_POR_RELATORIO.get(relatorio, set())

    coluna_conta = _detectar_coluna_conta(df)
    if coluna_conta and variaveis:
        df = df[df[coluna_conta].isin(variaveis)]

    if df.empty:
        return pd.DataFrame(columns=COLUNAS_SAIDA)

    return _padronizar(df, coluna_conta, relatorio)


def _detectar_coluna_conta(df: pd.DataFrame) -> str | None:
    for candidata in ("ds_conta", "no_conta", "co_conta", "conta"):
        if candidata in df.columns:
            return candidata
    return None


def _padronizar(df: pd.DataFrame, coluna_conta: str | None, relatorio: str) -> pd.DataFrame:
    mapa = {
        "_co_ibge":      "co_ibge",
        "_relatorio":    "relatorio",
        "_simplificado": "simplificado",
        "an_exercicio":  "exercicio",
        "nr_periodo":    "periodo",
        "no_ente":       "instituicao",
        "sg_uf":         "uf",
        "vl_conta":      "valor",
    }
    if coluna_conta:
        mapa[coluna_conta] = "conta"

    df = df.rename(columns={k: v for k, v in mapa.items() if k in df.columns})

    for col in COLUNAS_SAIDA:
        if col not in df.columns:
            df[col] = None

    df["relatorio"]   = relatorio
    df["valor"]       = pd.to_numeric(df["valor"], errors="coerce")
    df["exercicio"]   = pd.to_numeric(df["exercicio"], errors="coerce").astype("Int64")
    df["simplificado"] = df["simplificado"].fillna(False).astype(bool)

    return df[COLUNAS_SAIDA].dropna(subset=["conta", "valor"])