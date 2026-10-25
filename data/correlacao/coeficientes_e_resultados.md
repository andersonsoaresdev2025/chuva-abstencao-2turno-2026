# Coeficientes e Resultados Empíricos – 1º Turno 2026
**Bot 1 | Projeto Chuva × Abstenção Eleitoral – 2º Turno 2026**  
**Atualizado:** 2026-10-25 ~06:45 (Brasília)

---

## 1. Dados utilizados

| Fonte | Conteúdo | Cobertura |
|-------|----------|-----------|
| TSE (Bot 0) | Abstenção, comparecimento, aptos e votação por município | Todos os municípios (~5.700) |
| Open-Meteo Archive (ERA5) | Precipitação diária observada (mm) em 04/10/2026 | 30 maiores colégios eleitorais (prioridade) |
| Classificação de risco do projeto | <5 mm / 5–20 mm / ≥20 mm | Aplicada |

**Data da eleição do 1º turno:** 4 de outubro de 2026.  
**Abstenção nacional observada:** ≈ 21,08%.

---

## 2. Análise descritiva – 30 maiores municípios

### 2.1 Médias de abstenção por faixa de precipitação

| Faixa de chuva (04/10/2026) | N municípios | Média % abstenção | % abstenção ponderada por aptos | Precipitação média (mm) | Total de aptos |
|-----------------------------|--------------|-------------------|---------------------------------|--------------------------|----------------|
| Sem chuva relevante (< 5 mm) | 19 | 18,43% | **19,83%** | 2,0 mm | 19,7 milhões |
| Moderada (5–20 mm) | 10 | 20,89% | **22,01%** | 9,1 mm | 18,5 milhões |
| Torrencial (> 20 mm) | 1 (Porto Alegre) | 23,99% | 23,99% | 21,2 mm | 1,1 milhão |

Diferença bruta (moderada vs. sem chuva relevante): **+2,18 pp** (ponderada).

### 2.2 Correlação bruta (cross-section dos 30 maiores)

- Pearson **r = 0,55** (p = 0,0016)
- Spearman **ρ = 0,54** (p = 0,002)
- Regressão linear simples:  
  `PCT_ABSTENÇÃO ≈ 17,70 + 0,347 × precip_mm`  
  → **≈ +3,5 pp por centímetro** de chuva  
  → R² ≈ 0,30

### 2.3 Controles geográficos

| Modelo | Coeficiente (pp por mm) | p-valor | Interpretação |
|--------|--------------------------|---------|---------------|
| Sem controle | +0,347 | 0,002 | Associação positiva clara |
| Efeitos fixos de Região | +0,168 | 0,206 | Efeito reduzido pela metade; perde significância |
| Efeitos fixos de UF | +0,344 | 0,688 | Magnitude similar, mas poucos graus de liberdade (muitas UFs com 1 obs.) |

**Conclusão empírica do 1º turno (maiores colégios):**  
Há associação positiva entre precipitação e abstenção. Parte relevante da associação é explicada por diferenças regionais estruturais (Nordeste: menos chuva + abstenção historicamente menor; Sul/Sudeste: mais chuva + abstenção mais alta). O efeito “puro” da chuva, após controles geográficos, é positivo mas impreciso neste recorte.

---

## 3. Coeficientes recomendados para o Bot 4 e o dashboard

Com base na literatura internacional + evidência empírica do 1º turno, adotamos os seguintes parâmetros de referência (intervalos):

| Intensidade de chuva no horário de votação | Efeito esperado na taxa de abstenção | Fonte principal |
|--------------------------------------------|--------------------------------------|-----------------|
| < 5 mm | 0 (referência) | — |
| 5–20 mm | **+0,4 a +1,2 pp** | Literatura (0,5–1 pp/cm) + diferença observada 1º turno |
| ≥ 20–30 mm ou alerta de tempestade/alagamento | **+1,2 a +3,0 pp** (localmente pode ser maior) | Literatura + casos extremos + risco de mobilidade |

**Coeficiente central sugerido para simulações:**  
**+0,7 pp de abstenção por centímetro de precipitação no dia da eleição** (intervalo razoável: 0,4 – 1,0 pp/cm).

---

## 4. Limitações explícitas desta análise empírica

1. **Amostra restrita** aos 30 maiores colégios (prioridade operacional). Não cobre a totalidade dos municípios.
2. **Desenho cross-sectional** de um único dia: não isola causalidade.
3. **Confounding geográfico forte:** regiões com mais chuva no dia também diferem em estrutura socioeconômica e cultura eleitoral.
4. Dados de precipitação são pontuais (centroide da cidade); chuva é espacialmente heterogênea.
5. Não captura efeitos de **alagamento, fechamento de seções ou interrupção de transporte** (que podem gerar saltos discretos na abstenção).
6. O voto é obrigatório no Brasil → o efeito médio tende a ser menor do que em países de voto voluntário.

**Portanto:** a associação existe e tem magnitude electoralmente relevante em disputas apertadas, mas **não deve ser interpretada como efeito causal preciso** sem desenho mais robusto (efeitos fixos de município + múltiplas eleições + dados de precipitação de alta resolução).

---

## 5. Arquivos gerados

- `analise_1turno_2026.csv` — município a município (30 maiores) com precip + abstenção + faixa
- `resumo_por_faixa_chuva.csv` — agregados por faixa de risco
- Este arquivo (`coeficientes_e_resultados.md`)

**Status:** pronto para consumo pelo Bot 4 e pelo dashboard a partir das 08h00.
