# Pipeline de Coleta de Dados RGF

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Este projeto implementa uma pipeline modular para coleta automatizada de dados do **Registro Geral de Fiscalização (RGF)** da API Siconfi do Tesouro Nacional brasileiro.

## 📋 Visão Geral

A pipeline coleta dados financeiros de entes públicos (estados e municípios) relacionados à dívida consolidada, receita corrente líquida e outros indicadores fiscais, facilitando análises de endividamento público e estudos econômicos.

## 🏗️ Estrutura do Projeto

```
rgf_coleta/
├── main.py                 # Ponto de entrada com exemplos de uso
├── requirements.txt        # Dependências do projeto
├── src/
│   ├── __init__.py
│   ├── client.py           # Cliente da API Siconfi
│   ├── extract.py          # Extrator de dados por UF/município
│   ├── pipeline.py         # Orquestrador principal da pipeline
│   ├── transform.py        # Funções de transformação e filtro
│   ├── outputs.py          # Gerenciador de saídas (CSV)
│   └── config.py           # Configurações da aplicação
├── data/                   # Dados de entrada 
├── notebooks/              # Notebooks para análise exploratória
│   └── Untitled.ipynb
├── outputs/                # Arquivos CSV gerados
│   ├── municipios_simplificados_ceara_2019_2024.csv
│   ├── rgf_ceara_2019_2024.csv
│   ├── rgf_municipios_estudo.csv
│   ├── rgf_pernambuco_2019_2024.csv
│   └── rgf_ufs_atualizado.csv
└── README.md
```

## 🔧 Requisitos do Sistema

- **Python**: 3.8 ou superior
- **Memória RAM**: Mínimo 2GB (recomendado 4GB+ para grandes volumes de dados)
- **Conexão**: Internet estável para acesso à API do Tesouro Nacional
- **Espaço em disco**: ~100MB para dados processados

## 📦 Instalação e Configuração

### 1. Clonagem do Repositório

```bash
git clone <url-do-repositorio>
cd rgf_coleta
```

### 2. Instalação de Dependências

```bash
pip install -r requirements.txt
```

Ou instalar manualmente:

```bash
pip install requests>=2.28.0 pandas>=1.5.0
```

### 3. Verificação da Instalação

```bash
python -c "import requests, pandas; print('Dependências OK')"
```

## 🚀 Como Usar

### Uso Básico
```python
from src.client import SiconfiClient
from src.extract import RGFExtractor
from src.transform import RGFTransformer
from src.pipeline import RGFPipeline
from src.outputs import OutputManager
from src.config import PipelineConfig

# Inicializar componentes
client = SiconfiClient()
extractor = RGFExtractor(client)
transformer = RGFTransformer()
config = PipelineConfig(paralelo=True, max_workers=8)
pipeline = RGFPipeline(extractor, transformer, config)
output = OutputManager()

# Exemplo 1: Atualização para UFs
ufs = [22, 23, 24]  # Piauí, Ceará, Rio Grande do Norte
anos = [2023, 2024]
df_ufs = pipeline.run_ufs(ufs, anos)
output.salvar_csv(df_ufs, "rgf_ufs_atualizado")

# Exemplo 2: Estudo pontual de municípios
municipios = [2211001, 3304557]  # Teresina-PI, Rio de Janeiro-RJ
# run_municipios(municipios, anos, periodo, permitir_fallback=True)
df_mun = pipeline.run_municipios(municipios, anos, periodo=1, permitir_fallback=True)
output.salvar_csv(df_mun, "rgf_municipios_estudo")
```

### Uso Avançado com Tratamento de Erros

```python
from src.pipeline import RGFPipeline
from src.outputs import OutputManager
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)

  try:
    # Coletar dados com tratamento de erros
    client = SiconfiClient()
    extractor = RGFExtractor(client)
    transformer = RGFTransformer()
    config = PipelineConfig(paralelo=True, max_workers=8)
    pipeline = RGFPipeline(extractor, transformer, config)
    output = OutputManager()

    # Estados da região Nordeste
    ufs_nordeste = [21, 22, 23, 24, 25, 26, 27, 28, 29]
    anos = list(range(2019, 2025))

    df_resultado = pipeline.run_ufs(ufs_nordeste, anos)
    output.salvar_csv(df_resultado, "rgf_nordeste_2019_2024")

    print(f"✅ Dados coletados com sucesso: {len(df_resultado)} registros")

  except Exception as e:
    print(f"❌ Erro na coleta: {e}")
    logging.error(f"Detalhes do erro: {e}", exc_info=True)
```

### Execução via Linha de Comando

```bash
# Executar exemplo principal
python main.py
```

## 🏛️ Componentes da Pipeline

### 1. Cliente da API (`SiconfiClient`)
- **Responsabilidade**: Interface com a API REST do Tesouro Nacional
- **URL base**: `https://apidatalake.tesouro.gov.br/ords/siconfi/tt/rgf`
- **Funcionalidades**:
  - Requisições HTTP GET com tratamento de erros
  - Parsing automático de respostas JSON
  - Retry automático em caso de falhas temporárias

### 2. Extrator (`RGFExtractor`)
- **Responsabilidade**: Construção de parâmetros específicos para consultas
- **Tipos suportados**:
  - **Estados (UF)**: Relatórios quadrimestrais (RGF-Anexo 02)
  - **Municípios**: Relatórios quadrimestrais ou simplificados semestrais
- **Parâmetros dinâmicos**: Ano, período, tipo de demonstrativo, ente

### 3. Pipeline (`RGFPipeline`)
- **Responsabilidade**: Orquestração da coleta para múltiplos entes e anos
- **Métodos principais**:
  - `run_ufs()`: Coleta dados de estados com período quadrimestral
  - `run_municipios()`: Coleta dados de municípios com fallback automático
- **Tratamento inteligente**: Detecta automaticamente municípios simplificados

### 4. Transformação (`transform.py`)
- **Responsabilidade**: Filtragem e padronização dos dados brutos
- **Indicadores coletados**:
  - Dívida Consolidada (DC)
  - Dívida Consolidada Líquida (DCL)
  - Receita Corrente Líquida (RCL e RCL Ajustada)
  - Percentuais de endividamento (% DC/RCL, % DCL/RCL)
  - Precatórios (vencidos e não incluídos na DC)
  - Disponibilidade de caixa (bruta e líquida)
  - Empréstimos e parcelamentos

### 5. Gerenciador de Saídas (`OutputManager`)
- **Responsabilidade**: Persistência dos dados processados
- **Formatos suportados**: CSV (extensível para outros formatos)
- **Estrutura padronizada**: Colunas consistentes e tipos de dados apropriados

## 📊 Estrutura dos Dados de Saída

Os arquivos CSV gerados seguem uma estrutura padronizada:

| Coluna | Tipo | Descrição | Exemplo |
|--------|------|-----------|---------|
| `exercicio` | int | Ano do exercício fiscal | 2024 |
| `instituicao` | str | Nome do ente público | Estado do Ceará |
| `uf` | str | Sigla da unidade federativa | CE |
| `conta` | str | Nome da variável financeira | Dívida Consolidada |
| `valor` | float | Valor numérico do indicador | 15450000.50 |

## 🎯 Casos de Uso

### 1. Monitoramento Fiscal Estadual
```python
# Coletar dados de todos os estados brasileiros
todos_ufs = list(range(11, 54))  # Códigos IBGE de 11 a 53
anos = [2024]
df_estados = pipeline.run_ufs(todos_ufs, anos)
```

### 2. Análise Municipal Comparativa
```python
# Comparar capitais brasileiras
capitais = [1100205, 1200401, 1302603, 1400100, 1501402, 1600303,
           1721000, 2111300, 2211001, 2304400, 2408102, 2507507,
           2611606, 2704302, 2800308, 2927408, 3106200, 3205309,
           3304557, 3550308, 4106902, 4205407, 4314902, 5002704,
           5103403, 5208707, 5300108]
```

### 3. Estudos Regionais
```python
# Análise da região Sudeste
sudeste = [31, 32, 33, 35]  # MG, ES, RJ, SP
anos_historico = list(range(2019, 2025))
```

## ⚠️ Tratamento de Casos Especiais

### Municípios Simplificados
- **Cenário**: Municípios que não possuem relatório quadrimestral completo
- **Solução**: Fallback automático para versão simplificada semestral
- **Identificação**: Retornados na lista `simplificados` pelo método `run_municipios()`

### Períodos de Referência
| Tipo | Período | Descrição |
|------|---------|-----------|
| Estados | 3º Quadrimestre | Dados acumulados até dezembro |
| Municípios | 1º Quadrimestre | Dados até abril (relatório completo) |
| Municípios Simplificados | 1º Semestre | Dados até junho (versão simplificada) |

## 🔍 Troubleshooting

### Problemas Comuns

#### 1. Erro de Conexão
```
requests.exceptions.ConnectionError: HTTPSConnectionPool...
```
**Solução**: Verificar conexão com internet e tentar novamente.

#### 2. Dados Não Encontrados
```
ValueError: Possivelmente simplificado
```
**Solução**: Normal - município será processado como simplificado automaticamente.

#### 3. Rate Limiting da API
**Sintomas**: Muitas requisições falhando com HTTP 429
**Solução**: Adicionar delays entre requisições ou reduzir volume.

#### 4. Memory Error
**Sintomas**: `MemoryError` em grandes volumes de dados
**Solução**: Processar em lotes menores ou aumentar memória RAM.

### Validação dos Dados

```python
# Verificar integridade dos dados coletados
def validar_dados(df):
    assert not df.empty, "DataFrame vazio"
    assert 'valor' in df.columns, "Coluna 'valor' ausente"
    assert df['valor'].dtype in ['float64', 'int64'], "Tipo incorreto para valores"
    print(f"✅ Dados válidos: {len(df)} registros")

validar_dados(df_resultado)
```

## 📈 Limitações e Considerações

- **Disponibilidade**: Dados sujeitos à publicação pelo Tesouro Nacional
- **Atualização**: Relatórios publicados mensalmente/trimestralmente
- **Rate Limiting**: API possui limites de requisição
- **Dados Históricos**: Formatos podem variar entre anos
- **Cobertura**: Nem todos os municípios possuem dados disponíveis
- **Precisão**: Valores sujeitos a revisões posteriores

## 🛠️ Desenvolvimento

### Estrutura Modular
- **Separação de responsabilidades**: Cada módulo tem função específica
- **Testabilidade**: Componentes independentes e mockáveis
- **Extensibilidade**: Fácil adição de novos indicadores ou fontes

### Adicionando Novos Indicadores

1. **Localizar** no `transform.py` o conjunto `variaveis`
2. **Adicionar** o nome exato do indicador como aparece na API
3. **Testar** com dados reais

```python
# Exemplo: Adicionar novo indicador
novos_indicadores = {
    'Novo Indicador Financeiro',
    'Outro Indicador Relevante'
}
variaveis.update(novos_indicadores)
```

### Estendendo para Novos Relatórios

1. **Criar** método no `RGFExtractor` para o novo tipo
2. **Definir** parâmetros específicos da API
3. **Atualizar** `RGFPipeline` com novo método de orquestração

### Testes e Qualidade

```python
# Estrutura recomendada para testes
def test_api_connection():
    client = SiconfiClient()
    # Testar conectividade

def test_data_transformation():
    # Testar funções de transformação
    pass

def test_pipeline_execution():
    # Testar pipeline completa
    pass
```

## 🤝 Contribuição

1. **Fork** o projeto
2. **Crie** uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. **Commit** suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. **Push** para a branch (`git push origin feature/nova-funcionalidade`)
5. **Abra** um Pull Request

### Diretrizes de Código
- Seguir PEP 8 para estilo Python
- Adicionar docstrings às funções
- Incluir testes para novas funcionalidades
- Atualizar documentação quando necessário

## 📄 Licença

Este projeto está licenciado sob a [MIT License](LICENSE) - veja o arquivo LICENSE para detalhes.

## 📞 Suporte

Para questões, bugs ou sugestões:

1. Verifique os [issues](https://github.com/seu-usuario/rgf_coleta/issues) existentes
2. Abra um novo issue com descrição detalhada
3. Inclua logs de erro e código para reprodução

---

**Última atualização**: Janeiro 2026