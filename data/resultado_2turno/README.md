# Resultado oficial do 2º turno x estimativa do projeto (pós-eleição)

Comparação, município a município, entre a estimativa de efeito da chuva na abstenção publicada no dia da eleição (25/10/2026) e o resultado oficial do TSE.

- **Conclusão:** [`CONCLUSAO.md`](CONCLUSAO.md)
- **Relatório completo:** [`comparacao_municipios_2turno.md`](comparacao_municipios_2turno.md) e [`comparacao_municipios_2turno.pdf`](comparacao_municipios_2turno.pdf) (11 páginas)
- **Página pública:** https://andersonsoaresdev2025.github.io/chuva-abstencao-2turno-2026/resultado_2turno.html
- **Dashboard:** https://chuva-abstencao-2026.streamlit.app/ (página "Resultado oficial × estimativa")

> A estimativa do dia da eleição ficou **congelada às 17:09 BRT** e é mantida sem alteração como registro histórico (as atualizações automáticas foram encerradas às 17:10 BRT de 25/10/2026). O coeficiente do modelo não foi alterado.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `comparacao_municipios_2turno.csv` | 304 linhas, uma por município coberto (decimal com ponto, UTF-8, ordenado por aptos do 2º turno). Abstenção 1T/2T, variação, variação da UF, variação descontada, chuva do modelo e chuva usada (com piso dos ajustes), ajuste por notícias, efeito estimado (lo/mid/hi), abstenções extras estimadas, efeito por classe do Bot 4, abstenções observadas acima da média da UF, votos e % de Flávio Bolsonaro e Lula. |
| `resumo.json` | Números-chave (nacional, inclinações com IC, faixas de chuva, capitais, ajustados, municípios com 30 mm ou mais). É a fonte usada pelo site e pelo dashboard. |
| `uf_variacao.csv` | Abstenção por UF nos dois turnos e variação (média da UF usada no desconto). |
| `grafico_chuva_vs_variacao.png`, `grafico_estimado_vs_observado.png` | Gráficos do relatório. |
| `tse_2t/ab_2t.json`, `tse_2t/ab_<uf>.json` | Arquivos oficiais de abstenção do TSE (2º turno), nacional/UF e por município. |
| `tse_2t/municipios/*-u.json` | Resultado oficial por município (Presidente) dos 304 municípios. |

## Fontes

- **TSE, 2º turno (eleição 6258, totalização final, 100% das seções):**
  - Abstenção: `https://resultados.tse.jus.br/oficial/ele2026/6258/dados/{uf}/{uf}-e006258-ab.json` (o arquivo `br/br-e006258-ab.json` foi salvo como `ab_2t.json`).
  - Resultado municipal: `https://resultados.tse.jus.br/oficial/ele2026/6258/dados/{uf}/{uf}{código TSE com 5 dígitos}-c0001-e006258-u.json` (Flávio Bolsonaro = 22, Lula = 13).
  - Página pública: https://resultados.tse.jus.br
- **TSE, 1º turno:** `data/tse/2026_1turno/abstencao_municipio.csv` e `abstencao_por_uf.csv` (origem em `data/tse/2026_1turno/README_origem.md`).
- **Estimativa final do projeto (snapshot de 17:09 BRT):** `data/impacto/atualizacoes/impacto_agora_latest.json` (previsão + notícias, 9 ajustes ativos) e `data/impacto/atualizacoes/impacto_municipios_latest.csv`.
- **Ajustes por notícias:** `data/ajustes/ajustes_impacto_noticias.csv`.
- **Chuva:** acumulado 08-17h do Open-Meteo usado no snapshot final (modelo, não pluviômetro).

Os arquivos brutos do TSE somam cerca de 6 MB e estão versionados em `tse_2t/`. Para baixá-los de novo: `python scripts/pos_eleicao/baixar_tse.py`.

## Como reproduzir

```bash
pip install -r scripts/pos_eleicao/requirements.txt   # statsmodels, matplotlib, weasyprint, markdown
python scripts/pos_eleicao/montar.py   # junta 1T, 2T e estimativa (cache local, ignorado pelo git)
python scripts/pos_eleicao/gerar.py    # CSV, gráficos, relatório .md e resumo.json
python scripts/pos_eleicao/pdf.py      # PDF
```

Os scripts leem os arquivos `*_latest` de `data/impacto/` e avisam se o snapshot não for o final de 17:09 BRT.

## Método em uma linha

Variação da abstenção 1º→2º turno em cada município, menos a variação da UF inteira, comparada à chuva de 08-17h e ao efeito estimado; regressões sem e com peso pelo eleitorado, erro-padrão robusto HC1, IC de 95%. Essa variação **não** é a abstenção causada pela chuva; veja as limitações em `CONCLUSAO.md`.
