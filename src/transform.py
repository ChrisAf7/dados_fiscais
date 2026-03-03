"""
Transformações de dados — executadas em paralelo via ProcessPoolExecutor.
Funções puras: recebem lista de dicts brutos, retornam DataFrame padronizado.
"""
import re
import unicodedata
import logging
import pandas as pd

logger = logging.getLogger(__name__)

# ── Variáveis de interesse por relatório ──────────────────────────────────────

VARIAVEIS_RGF_UF = {
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
    'Demais Dívidas Contratuais',
}

VARIAVEIS_RGF_MUNICIPIO = {
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
    'Precatórios Posteriores a 05/05/2000 (inclusive) Vencidos e Não Pagos',
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
    "RGF-UF":          VARIAVEIS_RGF_UF,
    "RGF-Municipio":   VARIAVEIS_RGF_MUNICIPIO,
    "RREO-receitas":   VARIAVEIS_RREO_RECEITAS,
    "RREO-despesas":   set(),
    "RREO-resultado":  VARIAVEIS_RREO_RESULTADO,
    "RREO-dcl":        VARIAVEIS_RREO_DCL,
    "DCA":             VARIAVEIS_DCA,
}

# ── Renomeações para padronizar nomes longos da API ───────────────────────────

RENAME_MAP = {
    'RECEITA CORRENTE LÍQUIDA - RCL':
        'RECEITA CORRENTE LÍQUIDA',
    'RECEITA CORRENTE LÍQUIDA - RCL (IV)':
        'RECEITA CORRENTE LÍQUIDA',
    'RECEITA CORRENTE LÍQUIDA AJUSTADA PARA CÁLCULO DOS LIMITES DE ENDIVIDAMENTO (VI) = (IV - V)':
        'RECEITA CORRENTE LÍQUIDA AJUSTADA',
    '% da DCL sobre a RCL AJUSTADA (III/VI)':
        '% da DCL sobre a RCL AJUSTADA',
    '% da DC sobre a RCL AJUSTADA (I/VI)':
        '% da DC sobre a RCL AJUSTADA',
    'DÍVIDA CONSOLIDADA - DC (I)':
        'DÍVIDA CONSOLIDADA',
    'DÍVIDA CONSOLIDADA LÍQUIDA (DCL) (III) = (I - II)':
        'DÍVIDA CONSOLIDADA LÍQUIDA',
    'DÍVIDA CONSOLIDADA LÍQUIDUIDA (DCL) (III) = (I - II)':
        'DÍVIDA CONSOLIDADA LÍQUIDA',
    'Precatórios Posteriores a 05/05/2000 (inclusive) Vencidos e Não Pagos':
        'Precatórios (inclusive) Vencidos e Não Pagos',
    'Precatórios Posteriores a 05/05/2000 (Não incluídos na DC)':
        'Precatórios (Não incluídos na DC)',
}

COLUNAS_SAIDA = [
    "exercicio", "periodo", "relatorio", "co_ibge",
    "instituicao", "uf", "conta", "valor", "simplificado",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _limpar_nome_municipio(texto: str) -> str:
    """Remove prefixo 'Prefeitura Municipal de' e sufixo '- UF', normaliza."""
    if not isinstance(texto, str):
        return ""
    texto = re.sub(r'^Prefeitura Municipal de\s+', '', texto, flags=re.IGNORECASE)
    texto = re.sub(r'\s*-\s*[A-Z]{2}$', '', texto, flags=re.IGNORECASE)
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    return texto.strip().upper()


def _coluna_alvo(periodo: int, simplificado: bool) -> str:
    """Monta o nome da coluna de período esperada pela API."""
    if simplificado:
        return f"Até o {periodo}º Semestre"
    return f"Até o {periodo}º Quadrimestre"


# ── Função principal ──────────────────────────────────────────────────────────

def transformar_lote(items: list[dict]) -> pd.DataFrame:
    """
    Transforma um lote de itens brutos da API em DataFrame padronizado.
    Função pura — segura para ProcessPoolExecutor.

    Campos internos esperados em cada item (injetados pelo extrator):
        _relatorio, _co_ibge, _ano, _periodo, _simplificado

    Returns:
        DataFrame com colunas COLUNAS_SAIDA, ou vazio se sem dados válidos.
    """
    if not items:
        return pd.DataFrame(columns=COLUNAS_SAIDA)

    # Lê metadados do primeiro item — todos do lote são do mesmo ente/ano/período
    primeiro    = items[0]
    relatorio   = primeiro.get("_relatorio", "")
    co_ibge     = primeiro.get("_co_ibge")
    ano         = primeiro.get("_ano")
    periodo     = primeiro.get("_periodo")
    simplificado = primeiro.get("_simplificado", False)

    variaveis = _VARIAVEIS_POR_RELATORIO.get(relatorio, set())
    alvo      = _coluna_alvo(periodo, simplificado)

    registros = []
    for item in items:
        conta  = item.get("conta")
        coluna = item.get("coluna")

        # Filtro 1 — apenas variáveis de interesse
        if variaveis and conta not in variaveis:
            continue

        # Filtro 2 — apenas o período correto (quadrimestre ou semestre alvo)
        if coluna != alvo:
            continue

        registros.append({
            "exercicio":   ano,
            "periodo":     periodo,
            "relatorio":   relatorio,
            "co_ibge":     co_ibge,
            "instituicao": _limpar_nome_municipio(item.get("instituicao", "")),
            "uf":          item.get("uf", ""),
            "conta":       RENAME_MAP.get(conta, conta),
            "valor":       item.get("valor"),
            "simplificado": simplificado,
        })

    if not registros:
        return pd.DataFrame(columns=COLUNAS_SAIDA)

    df = pd.DataFrame(registros)
    df["valor"]     = pd.to_numeric(df["valor"], errors="coerce")
    df["exercicio"] = pd.to_numeric(df["exercicio"], errors="coerce").astype("Int64")

    return df.dropna(subset=["conta", "valor"])[COLUNAS_SAIDA]