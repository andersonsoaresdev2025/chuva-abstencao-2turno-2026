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
scripts/            build_site.py e update_and_publish.sh
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
scripts/update_and_publish.sh "mensagem"     # rebuild + testes + commit + push
```
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
