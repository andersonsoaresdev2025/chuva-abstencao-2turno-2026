# Status de Publicação – Chuva × Abstenção Eleitoral (2º Turno 2026)

Última atualização: **2026-10-25 10:55 UTC / 2026-10-25 07:55 BRT**

| Entregável | Status | URL | Atualizado (UTC / BRT) | Observações |
|---|---|---|---|---|
| Repositório GitHub (público) | publicado | https://github.com/andersonsoaresdev2025/chuva-abstencao-2turno-2026 | 2026-10-25 09:51 UTC / 2026-10-25 06:51 BRT | Branch `main` |
| Site estático (GitHub Pages) | publicado (HTTP 200 verificado) | https://andersonsoaresdev2025.github.io/chuva-abstencao-2turno-2026/ | 2026-10-25 09:51 UTC / 2026-10-25 06:51 BRT | Fonte: `main` /docs; gerado por scripts/build_site.py |
| Dashboard Streamlit | publicado | https://chuva-abstencao-2026.streamlit.app/ | 2026-10-25 09:58 UTC / 2026-10-25 06:58 BRT | Streamlit Community Cloud, main, dashboard/app.py, Python 3.12 |
| Impacto estimado agora (p.p. por candidato) | publicado | dashboard (topo da Visão Geral, lê precip_horaria_latest.csv da atualização automática, cache ≤ 10 min) e seção #agora do site (valor do momento do build) | 2026-10-25 10:12 UTC / 2026-10-25 07:12 BRT | Open-Meteo com fallback para previsão Bot 0; coeficiente Bot 1; MCP `impacto_agora()` |
| MCP (stdio) | pronto local | – (roda localmente: `python mcp/chuva_mcp_server.py`) | 2026-10-25 09:51 UTC / 2026-10-25 06:51 BRT | 6 ferramentas (inclui `impacto_agora`); teste ponta a ponta passa |
| Sinais sociais (data/social) | integrado | página "Sinais Sociais" do dashboard e seção do site | 2026-10-25 09:51 UTC / 2026-10-25 06:51 BRT | Coleta 2026-10-25 09:45 UTC (35 sinais) |
| Monitoramento de notícias (data/noticias) | publicado | página "Notícias" do dashboard + quadro "Principais notícias agora" na Visão Geral + seção #noticias do site | 2026-10-25 10:22 UTC / 2026-10-25 07:22 BRT | 44 portais verificados (13 nacionais, 31 regionais); coletor `scripts/coletar_noticias.py` (RSS + Google Notícias), roda em `scripts/update_and_publish.sh` |

## Atualização automática
- **Quem executa:** os papéis dos Bots 0–4 são executados por scripts (`scripts/atualizar_clima.py`, `scripts/atualizar_impacto.py`,
  `scripts/coletar_social.py`, `scripts/coletar_noticias.py`, `scripts/build_site.py`), orquestrados por `scripts/atualizar_tudo.sh`.
- **Onde:** GitHub Actions `.github/workflows/atualizar.yml`, a cada 30 min (06h00–19h30 BRT) + disparo manual; commit como
  github-actions, build do Pages solicitado pela API; Streamlit redeploya a partir da `main`.
- **Ajustes por notícias:** `data/ajustes/ajustes_impacto_noticias.csv` (preenchido pelo Grok Bot a cada 30 min) entra no clima,
  impacto e impacto agora.
- Linha por execução abaixo; log completo em `data/logs/`.

## Rodadas do Grok Bot (30 min, dia da eleição)
- 2026-10-25 11:15 UTC / 08:15 BRT: pipeline completo rodado 2x (ok; Actions não tinha rodado desde 07:52), 105 notícias na coleta, verificação X (6 buscas) + busca web, 7 sinais novos + 5 descartados, novo ajuste por notícias em Barracão (PR, nível b, TRE-PR + CNN), Curitiba e Guaratuba mantidos. Obs.: o log da rodada fica fora do commit do orquestrador e impede o pull --rebase (push segue ok).
- 2026-10-25 10:55 UTC / 07:55 BRT: notícias coletadas (92 no consolidado), verificação X (5 buscas), 4 sinais novos + 5 descartados, ajustes por notícias ativos para Curitiba (a) e Guaratuba (b), impacto recalculado. Pipeline completo não rodado nesta rodada: código de atualização automática (atualizar_tudo.sh, workflow) estava sendo editado e ainda não commitado; só os arquivos de dados foram publicados.

## Configuração do Streamlit Community Cloud
- Repository: `andersonsoaresdev2025/chuva-abstencao-2turno-2026`
- Branch: `main`
- Main file path: `dashboard/app.py`
- Python version (Advanced settings): **3.13** (testado; 3.12 compatível)
- Dependências: `dashboard/requirements.txt` · Secrets: nenhum

## Bloqueios / pendências
- Deploy do Streamlit Community Cloud: requer login no share.streamlit.io com a conta GitHub (feito via navegador).
- Coleta no X pela API: requer o secret `X_BEARER_TOKEN` no repositório (não configurado → etapa pulada e registrada).
- Instagram: só busca web pública; buscadores bloqueiam robôs com frequência (registrado no log social).

## Atualizações automáticas (mais recente primeiro)

<!-- AUTO-STATUS:INICIO -->
- 2026-10-25 08:45 BRT (20261025_1145UTC) · clima=ok(5s) impacto=ok(1s) social=ok(10s) noticias=ok(6s) site=ok(1s) testes=ok(13s) · log: data/logs/atualizacao_20261025_1145UTC.log
- 2026-10-25 08:13 BRT (20261025_1113UTC) · clima=ok(4s) impacto=ok(1s) social=ok(0s) noticias=ok(6s) site=ok(0s) testes=ok(13s) · log: data/logs/atualizacao_20261025_1113UTC.log
- 2026-10-25 08:11 BRT (20261025_1111UTC) · clima=ok(4s) impacto=ok(0s) social=ok(1s) noticias=ok(5s) site=ok(1s) testes=ok(14s) · log: data/logs/atualizacao_20261025_1111UTC.log
- 2026-10-25 08:10 BRT (20261025_1110UTC) · clima=ok(4s) impacto=ok(1s) social=ok(0s) noticias=ok(6s) site=ok(0s) testes=ok(12s) · log: data/logs/atualizacao_20261025_1110UTC.log
- 2026-10-25 07:52 BRT (20261025_1052UTC) · clima=ok(5s) impacto=ok(0s) social=ok(1s) noticias=ok(8s) site=ok(0s) testes=ok(11s) · log: data/logs/atualizacao_20261025_1052UTC.log
- 2026-10-25 07:50 BRT (20261025_1050UTC) · clima=ok(4s) impacto=ok(1s) social=ok(0s) noticias=ok(5s) site=ok(1s) testes=ok(12s) · log: data/logs/atualizacao_20261025_1050UTC.log
<!-- AUTO-STATUS:FIM -->
