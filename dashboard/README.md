# Dashboard – Chuva × Abstenção Eleitoral (2º Turno 2026)

Dashboard Streamlit público, interativo e didático. Veja o README da raiz do repositório para o contexto completo.

## Rodar localmente (a partir da raiz do repositório)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
```
Os dados são lidos de `data/` com caminhos relativos ao repositório (via `common/dados.py`).

## Páginas
1. **Visão Geral** – KPIs, municípios críticos, mensagem principal, últimos sinais sociais.
2. **Risco de Chuva** – previsão horária Open-Meteo (Bot 0/4) e classificação a/b/c com alertas INMET (Bot 2), por município, UF e região.
3. **Impacto na Abstenção** – efeito em pp (mid + faixa) e ordem de grandeza em abstenções.
4. **Redutos e Diferencial** – base do 1º turno (TSE/Bot 3) e exposição por candidato.
5. **Sinais Sociais** – `data/social/sinais_*.csv` + `resumo_*.md` (opcional; funciona sem a pasta).
6. **Metodologia e Limitações** – fontes, timestamps, coeficientes, limitações e política de sinais sociais.

## Streamlit Community Cloud
- Repositório: `andersonsoaresdev2025/chuva-abstencao-2turno-2026` · Branch: `main`
- Main file path: `dashboard/app.py` · Python: 3.13 (testado; 3.12 também compatível)
- Dependências: `dashboard/requirements.txt` (o Cloud procura primeiro na pasta do main file).
