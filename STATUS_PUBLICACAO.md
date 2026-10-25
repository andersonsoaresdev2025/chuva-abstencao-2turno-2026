# Status de Publicação – Chuva × Abstenção Eleitoral (2º Turno 2026)

Última atualização: **2026-10-25 10:12 UTC / 2026-10-25 07:12 BRT**

| Entregável | Status | URL | Atualizado (UTC / BRT) | Observações |
|---|---|---|---|---|
| Repositório GitHub (público) | publicado | https://github.com/andersonsoaresdev2025/chuva-abstencao-2turno-2026 | 2026-10-25 09:51 UTC / 2026-10-25 06:51 BRT | Branch `main` |
| Site estático (GitHub Pages) | publicado (HTTP 200 verificado) | https://andersonsoaresdev2025.github.io/chuva-abstencao-2turno-2026/ | 2026-10-25 09:51 UTC / 2026-10-25 06:51 BRT | Fonte: `main` /docs; gerado por scripts/build_site.py |
| Dashboard Streamlit | publicado | https://chuva-abstencao-2026.streamlit.app/ | 2026-10-25 09:58 UTC / 2026-10-25 06:58 BRT | Streamlit Community Cloud, main, dashboard/app.py, Python 3.12 |
| Impacto estimado agora (p.p. por candidato) | publicado | dashboard (topo da Visão Geral, recalcula a cada 5 min, chuva em cache 15 min) e seção #agora do site (valor do momento do build) | 2026-10-25 10:12 UTC / 2026-10-25 07:12 BRT | Open-Meteo com fallback para previsão Bot 0; coeficiente Bot 1; MCP `impacto_agora()` |
| MCP (stdio) | pronto local | – (roda localmente: `python mcp/chuva_mcp_server.py`) | 2026-10-25 09:51 UTC / 2026-10-25 06:51 BRT | 6 ferramentas (inclui `impacto_agora`); teste ponta a ponta passa |
| Sinais sociais (data/social) | integrado | página "Sinais Sociais" do dashboard e seção do site | 2026-10-25 09:51 UTC / 2026-10-25 06:51 BRT | Coleta 2026-10-25 09:45 UTC (35 sinais) |

## Configuração do Streamlit Community Cloud
- Repository: `andersonsoaresdev2025/chuva-abstencao-2turno-2026`
- Branch: `main`
- Main file path: `dashboard/app.py`
- Python version (Advanced settings): **3.13** (testado; 3.12 compatível)
- Dependências: `dashboard/requirements.txt` · Secrets: nenhum

## Bloqueios / pendências
- Deploy do Streamlit Community Cloud: requer login no share.streamlit.io com a conta GitHub (feito via navegador).
- Após o deploy: `STREAMLIT_URL=<url> scripts/update_and_publish.sh "Link do dashboard"` e atualizar esta tabela e o README.
