# Status de Publicação – Chuva × Abstenção Eleitoral (2º Turno 2026)

Última atualização: **2026-10-25 13:15 UTC / 2026-10-25 10:15 BRT**

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
- 2026-10-25 13:15 UTC / 10:15 BRT: pipeline completo rodado (ok, commit cdce023), verificação X (5 chamadas) + busca web/Instagram, 5 sinais novos + 5 descartados. Sem ajuste novo nem revogação (Curitiba a, Guaratuba b, Barracão b, Itapevi a). Monitorando Campinas (TRE-SP confirma escola alagada, votação normal) e Ribeirão Preto/Matão (escola alagada, falta de energia, urnas em bateria; fonte única).
- 2026-10-25 12:47 UTC / 09:47 BRT: pipeline completo rodado (ok, commit 7c9f8d3), verificação X (4 chamadas) + busca web (g1 regional, CBN, TRE-PR), 6 sinais novos + 6 descartados. Sem ajuste novo nem revogação; Barracão (PR) mantido em b com confiança rebaixada para média (nota do TRE-PR é de 23/10, temporal de sexta). Monitorando Jaú, Itapetininga, Bauru e Campinas (SP: 82–112 mm, alagamentos, sem efeito relatado na votação). Impacto agora (com ajustes, 1,77 h): margem +0,016 p.p. a favor de Lula, abstenção nacional +0,063 p.p. (~100 mil abstenções extras).
- 2026-10-25 12:20 UTC / 09:20 BRT: pipeline completo rodado 2x (ok; antes e depois do ajuste), verificação X (2 buscas) + busca web, 4 sinais novos + 3 descartados, novo ajuste por notícias em Itapevi (SP, nível a, transferência emergencial TRE-SP por alagamento; g1, Terra, Band). Curitiba a, Guaratuba b, Barracão b mantidos. Impacto agora (com ajustes, 1,24 h): margem +0,012 p.p. a favor de Lula, abstenção nacional +0,047 p.p.
- 2026-10-25 11:50 UTC / 08:50 BRT: pipeline completo rodado (ok; Actions não tinha rodado desde 08:13), verificação X (7 chamadas) + busca web, 4 sinais novos + 4 descartados, sem ajuste novo nem revogação (Curitiba a, Guaratuba b, Barracão b mantidos). Impacto agora cresce só pelo tempo decorrido (0,75 h; margem +0,006 p.p. a favor de Lula com ajustes).
- 2026-10-25 13:47 UTC / 10:47 BRT: pipeline completo rodado 2x (ok), verificação X (5 buscas) + busca web, 4 sinais novos + 4 descartados, novo ajuste por notícias em Itupeva (SP, nível a, confiança média; CNN Brasil citando TRE-SP: 2 locais transferidos por alagamento). Ajustes ativos: Curitiba, Guaratuba, Barracão, Itapevi, Itupeva.
- 2026-10-25 11:15 UTC / 08:15 BRT: pipeline completo rodado 2x (ok; Actions não tinha rodado desde 07:52), 105 notícias na coleta, verificação X (6 buscas) + busca web, 7 sinais novos + 5 descartados, novo ajuste por notícias em Barracão (PR, nível b, TRE-PR + CNN), Curitiba e Guaratuba mantidos. Obs.: o log da rodada fica fora do commit do orquestrador e impede o pull --rebase (push segue ok).
- 2026-10-25 10:55 UTC / 07:55 BRT: notícias coletadas (92 no consolidado), verificação X (5 buscas), 4 sinais novos + 5 descartados, ajustes por notícias ativos para Curitiba (a) e Guaratuba (b), impacto recalculado. Pipeline completo não rodado nesta rodada: código de atualização automática (atualizar_tudo.sh, workflow) estava sendo editado e ainda não commitado; só os arquivos de dados foram publicados.

- 2026-10-25 14:20 UTC / 11:20 BRT: pipeline completo rodado 2× (11:14 e 11:16 BRT, tudo ok); verificação X (3 buscas) + web/Instagram público; 4 sinais novos + 4 descartados; ajuste Itupeva (SP) elevado para confiança alta (2ª fonte: Terra/TRE-SP, 3.722 eleitores); 5 ajustes ativos; impacto recalculado e publicado.
- 2026-10-25 14:50 UTC / 11:50 BRT: pipeline completo rodado 2× (11:41 e 11:43 BRT, tudo ok); verificação X (2 buscas) + web; 7 sinais novos + 4 descartados; novos ajustes São Domingos (SC, b, alta; TRE-SC, 621 eleitores) e Campinas (SP, a, média; escola alagada em Sousas); 7 ajustes ativos; impacto recalculado e publicado.
- 2026-10-25 19:15 UTC / 16:15 BRT: pipeline completo rodado (16:12 BRT, tudo ok); verificação X (6 buscas) + web; 3 sinais novos + 6 descartados; sem novos ajustes nem revogações; 7 ajustes ativos; impacto recalculado e publicado.
- 2026-10-25 18:45 UTC / 15:45 BRT: pipeline completo rodado 2× (15:37 BRT e 15:40 BRT após ajuste, tudo ok); verificação X (3 buscas) + web; 4 sinais novos + 5 descartados; ajuste Belo Horizonte (MG) atualizado (segue b, confiança alta: Itatiaia relata seções de uma escola destelhada transferidas); 7 ajustes ativos; impacto recalculado e publicado.
- 2026-10-25 18:15 UTC / 15:15 BRT: pipeline completo rodado 2× (15:11 BRT e 15:13 BRT após ajuste, tudo ok); verificação X (6 buscas) + web; 5 sinais novos + 5 descartados; NOVO ajuste Belo Horizonte (MG) → b (média: chuva forte observada pela Defesa Civil, queda de energia em local de votação; modelo havia rebaixado para c); 7 ajustes ativos; corrigida linha CSV malformada (link do Terra com vírgula) em sinais_consolidado e sinais_20261025_1420UTC; impacto recalculado e publicado.
- 2026-10-25 17:45 UTC / 14:45 BRT: pipeline completo rodado (14:39 BRT, tudo ok); verificação X (6 buscas + 1 notícias) + web/Instagram; 2 sinais novos + 4 descartados; sem novos ajustes nem revogações; 6 ajustes ativos; INMET sem mudança (7 avisos); impacto agora: Flávio -0,023 pp (c/ notícias), abstenção nacional +0,248 pp; publicado.
- 2026-10-25 17:15 UTC / 14:15 BRT: pipeline completo rodado (14:11 BRT, tudo ok); verificação X (6 buscas) + web; 4 sinais novos + 4 descartados; sem novos ajustes nem revogações; 6 ajustes ativos; INMET sem mudança (7 avisos); impacto agora: Flávio -0,022 pp (c/ notícias), abstenção nacional +0,220 pp; publicado.
- 2026-10-25 16:45 UTC / 13:45 BRT: pipeline completo rodado (13:37 BRT, tudo ok); verificação X (6 buscas) + web; 5 sinais novos + 4 descartados; sem novos ajustes nem revogações; 6 ajustes ativos; INMET sem mudança (7 avisos); impacto sem alteração; publicado.
- 2026-10-25 16:15 UTC / 13:15 BRT: pipeline completo rodado (13:13 BRT, tudo ok); verificação X (3 buscas) + web; 4 sinais novos + 3 descartados; sem novos ajustes nem revogações; 6 ajustes ativos; impacto agora: Flávio -0,018 pp (c/ notícias), abstenção nacional +0,170 pp.
- 2026-10-25 15:45 UTC / 12:45 BRT: pipeline completo rodado (12:41 BRT, tudo ok); verificação X (5 buscas) + web; 2 sinais novos + 4 descartados; sem novos ajustes nem revogações; 6 ajustes ativos; impacto recalculado e publicado.
- 2026-10-25 15:20 UTC / 12:20 BRT: pipeline completo rodado 2× (12:14 BRT e após ajuste); verificação X (5 buscas) + web; 5 sinais novos + 4 descartados; ajuste Itupeva (SP) REVOGADO (TRE-SP suspendeu a transferência após a água baixar; g1/CNN); 6 ajustes ativos; impacto recalculado e publicado.
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
- 2026-10-25 16:41 BRT (20261025_1941UTC) · clima=ok(5s) impacto=ok(1s) social=ok(0s) noticias=ok(28s) site=ok(1s) consistencia=ok(0s) testes=ok(16s) · log: data/logs/atualizacao_20261025_1941UTC.log
- 2026-10-25 16:12 BRT (20261025_1912UTC) · clima=ok(5s) impacto=ok(1s) social=ok(0s) noticias=ok(27s) site=ok(1s) consistencia=ok(0s) testes=ok(16s) · log: data/logs/atualizacao_20261025_1912UTC.log
- 2026-10-25 15:39 BRT (20261025_1839UTC) · clima=ok(5s) impacto=ok(1s) social=ok(0s) noticias=ok(26s) site=ok(1s) consistencia=ok(0s) testes=ok(16s) · log: data/logs/atualizacao_20261025_1839UTC.log
- 2026-10-25 15:37 BRT (20261025_1837UTC) · clima=ok(5s) impacto=ok(0s) social=ok(1s) noticias=ok(27s) site=ok(0s) consistencia=ok(1s) testes=ok(16s) · log: data/logs/atualizacao_20261025_1837UTC.log
- 2026-10-25 15:13 BRT (20261025_1813UTC) · clima=ok(4s) impacto=ok(0s) social=ok(2s) noticias=ok(23s) site=ok(1s) consistencia=ok(0s) testes=ok(16s) · log: data/logs/atualizacao_20261025_1813UTC.log
- 2026-10-25 15:11 BRT (20261025_1811UTC) · clima=ok(5s) impacto=ok(0s) social=ok(1s) noticias=ok(25s) site=ok(0s) consistencia=ok(1s) testes=ok(16s) · log: data/logs/atualizacao_20261025_1811UTC.log
- 2026-10-25 14:39 BRT (20261025_1739UTC) · clima=ok(4s) impacto=ok(1s) social=ok(0s) noticias=ok(22s) site=ok(0s) consistencia=ok(1s) testes=ok(15s) · log: data/logs/atualizacao_20261025_1739UTC.log
- 2026-10-25 14:11 BRT (20261025_1711UTC) · clima=ok(5s) impacto=ok(1s) social=ok(10s) noticias=ok(22s) site=ok(0s) consistencia=ok(1s) testes=ok(16s) · log: data/logs/atualizacao_20261025_1711UTC.log
- 2026-10-25 13:37 BRT (20261025_1637UTC) · clima=ok(4s) impacto=ok(1s) social=ok(10s) noticias=ok(20s) site=ok(0s) consistencia=ok(1s) testes=ok(16s) · log: data/logs/atualizacao_20261025_1637UTC.log
- 2026-10-25 13:13 BRT (20261025_1613UTC) · clima=ok(5s) impacto=ok(1s) social=ok(1s) noticias=ok(19s) site=ok(0s) consistencia=ok(0s) testes=ok(16s) · log: data/logs/atualizacao_20261025_1613UTC.log
- 2026-10-25 12:41 BRT (20261025_1541UTC) · clima=ok(5s) impacto=ok(1s) social=ok(1s) noticias=ok(16s) site=ok(1s) consistencia=ok(0s) testes=ok(16s) · log: data/logs/atualizacao_20261025_1541UTC.log
- 2026-10-25 12:15 BRT (20261025_1515UTC) · clima=ok(5s) impacto=ok(1s) social=ok(0s) noticias=ok(15s) site=ok(1s) consistencia=ok(0s) testes=ok(16s) · log: data/logs/atualizacao_20261025_1515UTC.log
<!-- AUTO-STATUS:FIM -->
