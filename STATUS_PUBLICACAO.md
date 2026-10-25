# Status de Publicação – Chuva × Abstenção Eleitoral (2º Turno 2026)

Última atualização: **2026-10-25 10:55 UTC / 2026-10-25 07:55 BRT**

| Entregável | Status | URL | Atualizado (UTC / BRT) | Observações |
|---|---|---|---|---|
| Repositório GitHub (público) | publicado | https://github.com/andersonsoaresdev2025/chuva-abstencao-2turno-2026 | 2026-10-25 09:51 UTC / 2026-10-25 06:51 BRT | Branch `main` |
| Site estático (GitHub Pages) | publicado (HTTP 200 verificado) | https://andersonsoaresdev2025.github.io/chuva-abstencao-2turno-2026/ | 2026-10-25 09:51 UTC / 2026-10-25 06:51 BRT | Fonte: `main` /docs; gerado por scripts/build_site.py |
| Dashboard Streamlit | publicado | https://chuva-abstencao-2026.streamlit.app/ | 2026-10-25 09:58 UTC / 2026-10-25 06:58 BRT | Streamlit Community Cloud, main, dashboard/app.py, Python 3.12 |
| Impacto estimado agora (p.p. por candidato) | publicado | dashboard (topo da Visão Geral, recalcula a cada 5 min, chuva em cache 15 min) e seção #agora do site (valor do momento do build) | 2026-10-25 10:12 UTC / 2026-10-25 07:12 BRT | Open-Meteo com fallback para previsão Bot 0; coeficiente Bot 1; MCP `impacto_agora()` |
| MCP (stdio) | pronto local | – (roda localmente: `python mcp/chuva_mcp_server.py`) | 2026-10-25 09:51 UTC / 2026-10-25 06:51 BRT | 6 ferramentas (inclui `impacto_agora`); teste ponta a ponta passa |
| Sinais sociais (data/social) | integrado | página "Sinais Sociais" do dashboard e seção do site | 2026-10-25 09:51 UTC / 2026-10-25 06:51 BRT | Coleta 2026-10-25 09:45 UTC (35 sinais) |
| Monitoramento de notícias (data/noticias) | publicado | página "Notícias" do dashboard + quadro "Principais notícias agora" na Visão Geral + seção #noticias do site | 2026-10-25 10:22 UTC / 2026-10-25 07:22 BRT | 44 portais verificados (13 nacionais, 31 regionais); coletor `scripts/coletar_noticias.py` (RSS + Google Notícias), roda em `scripts/update_and_publish.sh` |

## Rodadas do Grok Bot (30 min, dia da eleição)
- 2026-10-25 10:55 UTC / 07:55 BRT: notícias coletadas (92 no consolidado), verificação X (5 buscas), 4 sinais novos + 5 descartados, ajustes por notícias ativos para Curitiba (a) e Guaratuba (b), impacto recalculado. Pipeline completo não rodado nesta rodada: código de atualização automática (atualizar_tudo.sh, workflow) estava sendo editado e ainda não commitado; só os arquivos de dados foram publicados.

## Configuração do Streamlit Community Cloud
- Repository: `andersonsoaresdev2025/chuva-abstencao-2turno-2026`
- Branch: `main`
- Main file path: `dashboard/app.py`
- Python version (Advanced settings): **3.13** (testado; 3.12 compatível)
- Dependências: `dashboard/requirements.txt` · Secrets: nenhum

## Bloqueios / pendências
- Deploy do Streamlit Community Cloud: requer login no share.streamlit.io com a conta GitHub (feito via navegador).
- Após o deploy: `STREAMLIT_URL=<url> scripts/update_and_publish.sh "Link do dashboard"` e atualizar esta tabela e o README.
