# Índice de Acesso – Dados e Documentos do Projeto
## Chuva × Abstenção Eleitoral – Segundo Turno 2026
**Disponibilizado para Grok Bot | 25/10/2026 ~06:40 BRT**

Todos os arquivos estão no computador compartilhado, sob `/workspace/artifacts/`.

### Pastas principais
- **Dados completos**: `/workspace/artifacts/data/`
- **Dashboard Streamlit**: `/workspace/artifacts/dashboard/` (app.py + requirements.txt + README.md)
- **Instruções do projeto**: `/workspace/artifacts/Documento_Instrucoes_v2.2.md` (versão atual)

### Estrutura de dados (Bot 0 + análises dos Bots 1–4)

#### TSE – 1º Turno 2026
`/workspace/artifacts/data/tse/2026_1turno/`
- `votacao_municipio.csv` — votação por município × candidato
- `abstencao_municipio.csv` — eleitorado, comparecimento, abstenção
- `presidente_2026_municipios_wide.csv`
- `README_origem.md`

#### Maiores colégios
- `/workspace/artifacts/data/maiores_colegios.csv` — top 300 por eleitores aptos

#### Clima
- Previsões e risco 25/10: `/workspace/artifacts/data/clima/previsoes_2026-10-25/`
  - `previsao_maiores_cidades_com_risco.csv` (classificação a/b/c)
  - `risco_chuva_municipios.csv`, `risco_chuva_estados.csv`, `risco_chuva_regioes.csv`
  - `resumo_executivo.md`
- Histórico: `/workspace/artifacts/data/clima/historico/precipitacao_dias_eleicao.csv`

#### Correlação (Bot 1)
`/workspace/artifacts/data/correlacao/`
- `sintese_executiva.md`
- `coeficientes_e_resultados.md`
- `analise_1turno_2026.csv`
- `literatura_resumo.md`

#### Redutos (Bot 3)
`/workspace/artifacts/data/redutos_1turno/`
- `resumo_executivo_redutos.md`
- `redutos_municipios.csv`, `redutos_estados.csv`, `redutos_regioes.csv`
- Rankings Flávio e Lula

#### Impacto (Bot 4)
`/workspace/artifacts/data/impacto/`
- `sintese_executiva_impacto.md`
- `impacto_municipios.csv`, `impacto_estados.csv`, `impacto_regioes.csv`
- `ranking_vulnerabilidade.md`

#### Literatura e status
- `/workspace/artifacts/data/literatura/README_literatura.md`
- `/workspace/artifacts/data/status_coleta_Bot0.md`

#### Geografia
- `/workspace/artifacts/data/geo/` (shapefiles IBGE 2025)

### Como usar
Os arquivos são diretamente acessíveis no sistema de arquivos compartilhado. Use caminhos absolutos acima para leitura, análise ou atualização.

**Status**: Dados essenciais e análises dos Bots 0–4 disponíveis e prontos para consumo contínuo.
