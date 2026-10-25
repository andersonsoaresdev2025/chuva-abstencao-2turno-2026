# Status da Coleta – Bot 0 (Aquisição e Organização)
**Projeto:** Chuva × Abstenção Eleitoral – Segundo Turno 2026  
**Atualização:** 2026-10-25 ~06:20 BRT (antes das 08h00)  
**Versão status:** 1.1

## ✅ Concluído

### 1. TSE – 1º Turno 2026 (PRIORIDADE MÁXIMA) — PRONTO
`/home/workdir/artifacts/data/tse/2026_1turno/`
- `votacao_municipio.csv` (long, ~12 MB)
- `abstencao_municipio.csv` (eleitorado, comparecimento, abstenção %)
- `presidente_2026_municipios_wide.csv`
- `abstencao_por_uf.csv`
- `README_origem.md`

### 2. Maiores colégios
- `/home/workdir/artifacts/data/maiores_colegios.csv` — top 300 por APTOS_2026

### 3. Geografia IBGE 2025
`/home/workdir/artifacts/data/geo/`
- Shapefiles: `BR_Municipios_2025.zip`, `BR_UF_2025.zip` + `uf_shp/` descompactado

### 4. Previsão 25/10/2026 (Open-Meteo)
`/home/workdir/artifacts/data/clima/previsoes_2026-10-25/`
- `previsao_maiores_cidades.csv`
- `previsao_maiores_cidades_com_risco.csv` ← **com classificação a/b/c do projeto**

**Risco alto (classe a ≥20 mm) nos maiores colégios:**
| Município              | Precip. prevista | Classe |
|------------------------|------------------|--------|
| São Bernardo do Campo  | ~72 mm           | a) Torrencial |
| Guarulhos              | ~62 mm           | a) Torrencial |
| São Paulo              | ~57 mm           | a) Torrencial |
| Campinas               | ~34 mm           | a) Torrencial |
| Rio de Janeiro         | ~39 mm           | a) Torrencial |
| Curitiba               | ~20 mm           | a/b limite |
| Porto Alegre           | ~16 mm           | b) Moderada |

Centro-Sul (SP, RJ, PR, RS) concentra risco elevado no horário de votação.

### 5. Histórico de precipitação (dias de eleição)
`/home/workdir/artifacts/data/clima/historico/precipitacao_dias_eleicao.csv`
- Cidades: SP, RJ, BH, Brasília, Curitiba, Porto Alegre
- Datas: 2014 (1T/2T), 2018 (1T/2T), 2022 (1T/2T), 2026_1T
- Fonte: Open-Meteo Archive (ERA5)

### 6. Literatura
`/home/workdir/artifacts/data/literatura/README_literatura.md`
- Meta-análise Damsbo-Svendsen & Hansen (2023) — −0,95 p.p./cm
- Gomez et al. (2007) clássico EUA
- Nota sobre análise preliminar 1º turno 2026 (Arvor)

## Estrutura atual
```
data/
├── tse/2026_1turno/          ← utilizável pelos bots
├── clima/
│   ├── historico/precipitacao_dias_eleicao.csv
│   └── previsoes_2026-10-25/ (com classificação de risco)
├── geo/                      (shapefiles IBGE)
├── literatura/
├── maiores_colegios.csv
└── status_coleta_Bot0.md
```

## Limitações registradas
- GeoJSON leve de municípios não gerado (shapefile ~227 MB disponível; geopandas não instalado no sandbox).
- Histórico limitado às 6 maiores capitais (expansão possível sob demanda).
- Dados por seção eleitoral não baixados (volume; município suficiente para início).
- Literatura: índice + links (PDFs completos sob paywall).

**Bot 0:** Dados essenciais para monitoramento do dia (TSE 1T + previsão com risco + maiores colégios + histórico básico + literatura) estão disponíveis **antes das 08h00**.  
Próximos bots (especialmente Bot 2 e Bot 1) podem consumir imediatamente.
