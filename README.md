# 🌧️ Chuva × Abstenção Eleitoral – Segundo Turno 2026

Monitoramento público do **risco de chuva no horário de votação (08h–17h)** e do **impacto estimado sobre a
abstenção** no 2º turno da eleição presidencial de **25/10/2026** (Flávio Bolsonaro × Lula), por município,
UF e grande região. Projeto aberto, com fontes, timestamps, incerteza e limitações sempre visíveis.

> ⚠️ Uso informativo. Estimativas com faixa de incerteza — **não** é previsão eleitoral oficial.
> Informações oficiais: TSE, INMET e Defesa Civil.

## Links
| | URL |
|---|---|
| Dashboard interativo (Streamlit) | https://chuva-abstencao-2026.streamlit.app/ |
| Site resumido (GitHub Pages) | https://andersonsoaresdev2025.github.io/chuva-abstencao-2turno-2026/ (publicado 2026-10-25 09:52 UTC) |
| Repositório | https://github.com/andersonsoaresdev2025/chuva-abstencao-2turno-2026 |

Status detalhado: [STATUS_PUBLICACAO.md](STATUS_PUBLICACAO.md).

## Estrutura
```
dashboard/          app Streamlit (main file: dashboard/app.py) + requirements.txt
docs/               site estático (GitHub Pages), gerado por scripts/build_site.py
mcp/                servidor MCP (FastMCP, stdio) + teste
common/dados.py     leitura compartilhada dos CSVs (dashboard, site e MCP)
scripts/            atualizar_tudo.sh (orquestrador 30 min), atualizar_clima.py, atualizar_impacto.py,
                    coletar_social.py, coletar_noticias.py, build_site.py, update_and_publish.sh (atalho)
common/regras.py    regras a/b/c, efeitos por classe e ajustes por notícias (compartilhadas)
.github/workflows/atualizar.yml   GitHub Actions: atualização automática a cada 30 min
data/               dados processados (ver abaixo)
tests/              testes do dashboard (streamlit.testing AppTest)
Documento_Instrucoes_v2*.md, AGENTS.md, checklist_execucao.md   documentos do projeto
```

## Como rodar
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt          # dashboard + MCP + pytest
streamlit run dashboard/app.py               # dashboard local (http://localhost:8501)
python scripts/build_site.py                 # regenera docs/index.html
python mcp/chuva_mcp_server.py               # servidor MCP (stdio) – ver mcp/README.md
python -m pytest -q tests mcp/test_mcp_server.py
scripts/atualizar_tudo.sh                    # atualização completa: clima → impacto → social → notícias → site → testes → commit/push
PUBLICAR=0 scripts/atualizar_tudo.sh         # idem, sem git (só gera os arquivos)
```
`scripts/update_and_publish.sh` continua existindo, mas apenas chama `scripts/atualizar_tudo.sh` — use o orquestrador.

## Atualização automática (a cada 30 min)
**Os papéis dos Bots 0–4 são executados por estes scripts** (os bots originais não são chamados; os arquivos
originais deles ficam intactos e servem de referência "manhã" e de fallback):

| Etapa | Script | Papel | Saídas |
|---|---|---|---|
| clima | `scripts/atualizar_clima.py` | Bot 0/Bot 2 – previsão Open-Meteo horária (≈300 municípios) + avisos INMET (JSON → RSS → último cache, marcado) → risco a/b/c | `data/clima/atualizacoes/risco_chuva_{municipios,estados,regioes}_latest.csv` (+ versões `_<UTC>.csv`), `precip_horaria_latest.csv`, `inmet_avisos_latest.json`, `status_latest.json`, `resumo_latest.md` (mudanças vs manhã) |
| impacto | `scripts/atualizar_impacto.py` | Bot 4 (+ coeficiente do Bot 1) – impacto por município/UF/região e "impacto agora" | `data/impacto/atualizacoes/impacto_*_latest.csv`, `impacto_agora_latest.json` (só previsão × previsão + notícias), `impacto_agora_historico.csv` |
| social | `scripts/coletar_social.py` | sinais em redes: X (API v2, só se houver `X_BEARER_TOKEN`); Instagram via busca web pública (sem login) | `data/social/sinais_<data>_auto.csv` (coluna `rede`), `data/social/log_coleta_social.csv` |
| notícias | `scripts/coletar_noticias.py` | portais + Google Notícias RSS | `data/noticias/` |
| site | `scripts/build_site.py` | GitHub Pages | `docs/index.html` |
| testes | pytest (rede mockada) | — | — |
| git | commit → `pull --rebase` → push | — | — |

- **Onde roda:** `.github/workflows/atualizar.yml` (GitHub Actions) com `cron: '*/30 9-22 * * *'` (06h00–19h30 BRT) e
  disparo manual (`gh workflow run atualizar.yml`). O workflow roda `atualizar_tudo.sh` com `PUBLICAR=0`, faz o commit como
  `github-actions[bot]` (`pull --rebase` antes do push, `concurrency` para não sobrepor execuções) e pede o build do
  GitHub Pages pela API (push com `GITHUB_TOKEN` pode não disparar o Pages). O Streamlit Community Cloud redeploya a
  partir da `main`; o dashboard lê os `*_latest` com cache de no máximo 10 min.
- **Falhas:** nenhuma etapa derruba a execução. Se uma fonte falha, fica o último dado válido, marcado como
  desatualizado (`status_dado`, avisos no topo do dashboard e do site). Nada é inventado.
- **Logs:** `data/logs/atualizacao_<UTC>.log` por execução e uma linha de status em `STATUS_PUBLICACAO.md`.
- **Agendamento e reforço:** o workflow tem dois horários (`*/30` e `15,45`), porque o cron do GitHub Actions
  atrasa ou pula execuções em horários de pico (e costuma ignorar os primeiros horários logo após o workflow ser
  criado). Execuções agendadas com menos de 20 min desde a última atualização são puladas (limite diário do Open-Meteo).
  **Reforço independente:** a rotina de 30 min do Grok Bot roda o pipeline (`scripts/atualizar_tudo.sh`) e revisa os
  ajustes por notícias mesmo que o cron do GitHub falhe. O script não dispara o workflow (evita laços).
- **Git:** o commit inclui `data/` (com o log da execução), `docs/` e `STATUS_PUBLICACAO.md`; a saída do próprio git vai
  para `data/logs/git_ultimo.txt` (ignorado) e o `pull` usa `--rebase --autostash`.
- **Cron local alternativo:** `*/30 * * * * cd <repo> && scripts/atualizar_tudo.sh` (não rode os dois ao mesmo tempo).
Para preencher o link do Streamlit no site: `STREAMLIT_URL=https://... python scripts/build_site.py`
(ou edite a constante `STREAMLIT_URL` em `scripts/build_site.py`).

## Dados e origem (por Bot)
| Camada | Pasta | Origem | Atualização declarada |
|---|---|---|---|
| Bot 0 – Aquisição | `data/tse/2026_1turno/`, `data/maiores_colegios.csv`, `data/clima/previsoes_2026-10-25/previsao_*.csv`, `data/clima/historico/` | TSE (1º turno 2026), Open-Meteo (previsão e arquivo ERA5), IBGE | previsão coletada 25/10 ~09:01 |
| Bot 1 – Correlação | `data/correlacao/`, `data/literatura/` | Literatura internacional + 1º turno 2026 (30 maiores colégios) | 25/10 06:30–06:55 BRT |
| Bot 2 – Risco a/b/c | `data/clima/previsoes_2026-10-25/risco_chuva_*.csv` | Open-Meteo + alertas INMET | 25/10 06:35 BRT |
| Bot 3 – Redutos | `data/redutos_1turno/` | TSE 1º turno 2026 | 25/10 ~06:30 BRT |
| Bot 4 – Impacto | `data/impacto/` | Cruzamento Bots 0–3 | 25/10 09:24 BRT |
| Monitoramento social | `data/social/` | X + portais/órgãos locais públicos (curadoria) | ver `timestamp_coleta_utc` |

Os timestamps exibidos no dashboard e no site são lidos **de dentro dos arquivos**.

### Tamanho dos arquivos / exclusões
- Nenhum arquivo de dados ultrapassa 50 MB; **nenhum dado foi excluído** por tamanho. Maiores:
  `data/tse/2026_1turno/votacao_municipio.csv` e `presidente_2026_municipios_long.csv` (12,6 MB cada).
- Observação: `votacao_municipio.csv` é idêntico a `presidente_2026_municipios_long.csv`, e
  `meta_por_municipio.csv` é idêntico a `abstencao_municipio.csv` (mesmo hash MD5); mantidos por compatibilidade
  com o índice original.
- Não incluídos no repositório: `.venv/`, `__pycache__/`, segredos. A pasta `data/geo/` (shapefiles IBGE)
  citada no índice original **não foi recebida** neste pacote e não é usada pelo dashboard.

## Metodologia (resumo)
1. **Risco de chuva** – classificação do projeto para 08h–17h: **a)** torrencial/tempestade/risco de alagamento
   (≥ 20–30 mm ou alertas); **b)** moderada (5–20/30 mm); **c)** sem chuva relevante (< 5 mm).
2. **Coeficientes (Bot 1)** – literatura: ≈ +0,4 a +1,0 pp de abstenção por cm de chuva; 1º turno 2026:
   diferença bruta ≈ +2,2 pp entre faixas moderada e sem chuva (reduzida após controles regionais).
   Regra prática: moderada **+0,5 a +1,2 pp**; torrencial **+1,2 a +3,0 pp**.
3. **Impacto (Bot 4)** – regra aplicada a cada local; impacto diferencial proporcional à base de votos do
   1º turno (quem tem maior base local tende a perder mais votos absolutos).
4. **Impacto estimado agora** (cards no topo da Visão Geral, `common/impacto_agora.py`, também no site e no
   MCP `impacto_agora()`):
   - Chuva acumulada de 08h até o instante do cálculo nos 15 maiores colégios com coordenadas (Open-Meteo
     `hourly=precipitation`, `timezone=America/Sao_Paulo`, cache de 15 min; o valor rotulado HH:00 é o total da
     hora anterior, então 08h–17h = rótulos 09..17 e a hora em curso entra pró-rata). Para horas já decorridas o
     Open-Meteo entrega a estimativa do modelo/nowcast, **não** medição de pluviômetro. Se a API falhar, usa-se a
     previsão do Bot 0 (CSV) pró-rata pelas horas decorridas (manhã 08–12h, tarde 12–17h).
   - Efeito na abstenção = coeficiente do Bot 1 para simulações, **0,07 p.p. por mm** (0,7 p.p./cm; faixa
     0,04–0,10) × mm acumulados. Nenhum coeficiente novo.
   - Abstenções extras = aptos × efeito; divididas entre Flávio e Lula pela votação de cada um no município no
     1º turno (suposição do Bot 4). Base nacional = votos de Flávio e Lula no 1º turno (TSE, todo o país +
     exterior). Resultado: Δ participação de cada um nos votos válidos dos dois (p.p.), efeito na margem
     (Lula − Flávio), votos perdidos e abstenção nacional extra. Municípios não cobertos = 0 (cobertura ≈ 20%
     do eleitorado).
   - Antes das 08h: projeção do dia inteiro; após 17h: estimativa final do dia. A faixa lo–hi reflete só a
     incerteza do coeficiente. **Não** é contagem de votos nem boca de urna.
5. **Sinais sociais** – exibidos separadamente; não alteram automaticamente as estimativas.
6. **Regra da atualização automática (papel Bot 2):** chuva prevista na janela 08–17h ≥ 20 mm → **a**; 5–20 mm → **b**;
   < 5 mm → **c**; aviso INMET **laranja/vermelho** de chuva/tempestade vigente na janela eleva um nível. Estado/região:
   nível predominante pela fatia do eleitorado coberto. (O Bot 4 original classificava pelo total do dia ≥ 30 mm; a
   atualização usa a janela de votação.) Efeitos por classe (Bot 4): a = +2,0 (1,2–3,0) pp; b = +0,85 (0,5–1,2); c = +0,15 (0–0,4).
7. **Ajustes por notícias** (`data/ajustes/ajustes_impacto_noticias.csv`, revisado a cada 30 min a partir de notícias e
   relatos verificados): para cada município, vale o último registro; com `status=ativo`, o nível usado é
   **max(previsão, ajuste)** e, no impacto agora, a chuva usada é **max(modelo, intensidade estimada)**, sendo a intensidade
   no mínimo o piso da classe (a = 20 mm, b = 5 mm; sem intensidade, vale o piso). Pode incluir municípios fora das listas, desde que existam nos dados do TSE do
   1º turno (o impacto por candidato usa os votos desse município). Tudo aparece com o rótulo **"ajuste por notícias"**,
   fontes e confiança; os cards de impacto mostram **só previsão** e **previsão + notícias** lado a lado.

## Limitações e incerteza (explícitas)
- Cobertura climática incompleta: previsão horária para 15 maiores colégios; classificação a/b/c para 29
  municípios; interior agregado/extrapolado.
- Coeficientes imprecisos: análise cross-section (30 municípios); parte da associação é estrutural/regional.
- Impacto diferencial simplificado (sem renda, transporte, idade, motivação).
- 2º turno pode diferir do 1º; voto obrigatório no Brasil pode reduzir o efeito frente à literatura.
- Chuva ≠ alagamento: eventos extremos têm efeitos discretos não lineares.
- **As camadas Bot 2 (06:35 BRT) e Bot 4 (09:24 BRT) divergem em alguns locais** (ex.: Curitiba, MS, MG,
  região Sudeste); ambas são mostradas com seus horários, sem ajuste.
- Correlação não é causalidade.
- **Atualização automática:** cobertura de ≈300 municípios (≈54% do eleitorado); o restante de cada UF recebe o nível
  predominante dos municípios cobertos (extrapolação). O modelo Open-Meteo não é observação de pluviômetro.
- **Ajustes por notícias** dependem da cobertura da imprensa (viés para capitais e grandes cidades), têm confiança
  declarada e podem ficar defasados até a próxima revisão (30 min); só elevam o risco, nunca reduzem.
- **Redes sociais:** sem credencial da API do X, a coleta no X é pulada (registrado no log). Instagram só por busca
  web pública, sem login: os buscadores frequentemente bloqueiam robôs (HTTP 202/429), então muitas execuções não
  encontram nada — isso é registrado em `data/social/log_coleta_social.csv`. Itens do Instagram têm confiança baixa,
  exceto contas oficiais.

## Política de desinformação (sinais sociais)
- Prioridade a fontes oficiais (INMET, Defesa Civil, CGE, TREs/TSE), meteorologistas e imprensa com fonte primária.
- Relatos individuais só entram com confiança "baixa" ou quando ≥ 3 relatos independentes forem consistentes.
- Descartados: conteúdo que contradiz fonte oficial, mídia de data/local não verificável, local ambíguo,
  respostas de IA e mobilização partidária sem fato novo (registrados em `data/social/descartados_*.csv`).
- Todo sinal tem link para a fonte original e timestamps de publicação e de coleta. Nada é publicado sem ter
  sido visto na coleta. Correções são feitas removendo/reclassificando o registro na coleta seguinte.

## Licença
- **Código**: MIT ([LICENSE](LICENSE)).
- **Dados de análise** do projeto: CC BY 4.0 ([LICENSE-DATA.md](LICENSE-DATA.md)).
- **Dados de origem pública** (TSE, INMET, Open-Meteo, IBGE) mantêm seus termos originais.

---
Última revisão deste README: 25/10/2026.
