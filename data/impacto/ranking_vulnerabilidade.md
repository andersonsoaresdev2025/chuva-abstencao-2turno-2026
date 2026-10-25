# Ranking de Vulnerabilidade – Chuva × Abstenção
**Bot 4 – Impacto Diferencial e Síntese**  
**Atualizado em:** 2026-10-25 09:25 BRT  
**Fontes:** Bot 0 (clima) + Bot 1 (coeficientes) + Bot 3 (redutos)  
**Escopo:** 15 maiores colégios com previsão detalhada + agregação estadual/regional.

> **Nota:** Coeficientes de efeito na abstenção agora calibrados com a saída do Bot 1 (literatura + análise do 1º turno 2026). Classificação de risco usa o padrão oficial do projeto.

## 1. Municípios Críticos (Alta ou Média vulnerabilidade)

| Rank | Município | UF | Aptos | Nível Risco | Efeito Abst. mid (pp) | Faixa (pp) | Mais prejudicado | Vulnerabilidade |
|------|-----------|----|-------|-------------|-----------------------|------------|------------------|-----------------|
| 1 | SÃO PAULO | SP | 9,145,124 | torrencial | 2.0 | 1.2–3.0 | Lula (maior base local) | Alta |
| 2 | RIO DE JANEIRO | RJ | 4,952,612 | torrencial | 2.0 | 1.2–3.0 | Flávio Bolsonaro (maior base local) | Alta |
| 3 | GUARULHOS | SP | 948,908 | torrencial | 2.0 | 1.2–3.0 | Flávio Bolsonaro (maior base local) | Alta |
| 4 | CAMPINAS | SP | 873,613 | torrencial | 2.0 | 1.2–3.0 | Flávio Bolsonaro (maior base local) | Alta |
| 5 | SÃO BERNARDO DO CAMPO | SP | 626,647 | torrencial | 2.0 | 1.2–3.0 | Lula (maior base local) | Alta |
| 6 | BELO HORIZONTE | MG | 1,966,966 | moderada | 0.85 | 0.5–1.2 | Flávio Bolsonaro (maior base local) | Média |
| 7 | CURITIBA | PR | 1,415,148 | moderada | 0.85 | 0.5–1.2 | Flávio Bolsonaro (maior base local) | Média |
| 8 | PORTO ALEGRE | RS | 1,064,200 | moderada | 0.85 | 0.5–1.2 | Lula (maior base local) | Média |

## 2. Estados com maior exposição

| UF | Aptos | Peso % | Nível Risco | Efeito mid (pp) | Mais prejudicado | Vulnerabilidade |
|----|-------|--------|-------------|-----------------|------------------|-----------------|
| SP | 34,122,892 | 21.5 | torrencial | 1.5 | Flávio Bolsonaro (maior base) | Alta |
| RJ | 12,857,648 | 8.1 | moderada | 0.9 | Flávio Bolsonaro (maior base) | Média |
| PR | 8,613,657 | 5.4 | moderada | 0.7 | Flávio Bolsonaro (maior base) | Média |
| RS | 8,522,545 | 5.4 | moderada | 0.6 | Flávio Bolsonaro (maior base) | Média |

## 3. Regiões

| Região | Aptos | Peso % | Nível | Efeito mid | Mais prejudicado |
|--------|-------|--------|-------|------------|------------------|
| Sudeste | 66,344,562 | 41.8 | moderada | 1.1 | Flávio Bolsonaro (maior base) |
| Nordeste | 43,511,237 | 27.4 | sem_chuva_relevante | 0.12 | Lula (maior base) |
| Sul | 22,870,853 | 14.4 | moderada | 0.65 | Flávio Bolsonaro (maior base) |
| Norte | 13,101,175 | 8.3 | sem_chuva_relevante | 0.15 | Flávio Bolsonaro (maior base) |
| Centro-Oeste | 12,001,141 | 7.6 | sem_chuva_relevante | 0.15 | Flávio Bolsonaro (maior base) |

---
**Coeficientes utilizados (Bot 1 – regra prática):**
- Moderada (5–20 mm): **+0,5 a +1,2 pp** (mid ≈ 0,85)
- Torrencial / tempestade / alagamento (≥20–30 mm): **+1,2 a +3,0 pp** (mid ≈ 2,0)
- Sem chuva relevante: efeito residual baixo (0–0,4 pp)

**Vulnerabilidade:**
- **Alta**: risco torrencial + grande colégio eleitoral
- **Média**: risco moderado
- **Baixa**: sem chuva relevante

Arquivos de dados: `impacto_municipios.csv`, `impacto_estados.csv`, `impacto_regioes.csv`
