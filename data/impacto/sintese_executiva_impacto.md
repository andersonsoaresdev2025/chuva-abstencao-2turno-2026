# Síntese Executiva de Impacto – Chuva × Abstenção Eleitoral
**Segundo Turno 2026 | Flávio Bolsonaro × Lula**  
**Bot 4 – Impacto Diferencial e Síntese**  
**Horário da última atualização:** 2026-10-25 09:25 BRT  
**Status:** Versão 1.1 – agora consumindo coeficientes do Bot 1

---

## 1. Visão geral do Brasil

No dia 25 de outubro de 2026, o principal foco de risco de chuva relevante durante o horário de votação (08h–17h) concentra-se no **Centro-Sul**, especialmente na **Região Metropolitana de São Paulo** e no **Rio de Janeiro**.

- **Sudeste** (≈41,8% do eleitorado): risco **moderado a alto**, puxado por SP e RJ.
- **Sul** (≈14,4%): risco moderado (Curitiba e Porto Alegre).
- **Nordeste, Norte e Centro-Oeste**: previsão de chuva fraca ou ausente nos principais centros → risco baixo de impacto significativo na abstenção via clima.

A magnitude do efeito foi calibrada com a saída do **Bot 1** (literatura + análise empírica do 1º turno 2026 nos 30 maiores colégios).

## 2. Onde a chuva deve impactar mais

### Municípios de atenção prioritária

| Município | Precip. dia (mm) | Janela 08-17h (mm) | Nível | Efeito estimado na abstenção |
|-----------|------------------|--------------------|-------|------------------------------|
| Guarulhos/SP | ~63 | ~39 | Torrencial | +1,2 a +3,0 pp |
| São Paulo/SP | ~57 | ~27 | Torrencial | +1,2 a +3,0 pp |
| Rio de Janeiro/RJ | ~39 | ~27 | Torrencial | +1,2 a +3,0 pp |
| Campinas/SP | ~34 | ~16 | Torrencial | +1,2 a +3,0 pp |
| São Bernardo do Campo/SP | ~72 | ~10 | Torrencial | +1,2 a +3,0 pp |
| Curitiba/PR | ~20 | ~15 | Moderada | +0,5 a +1,2 pp |
| Porto Alegre/RS | ~16 | ~8 | Moderada | +0,5 a +1,2 pp |
| Belo Horizonte/MG | ~6 | ~2,5 | Moderada | +0,5 a +1,2 pp |

Demais grandes centros (Salvador, Fortaleza, Recife, Brasília, Manaus, Goiânia, Belém): efeito esperado desprezível.

### Estados mais expostos
1. **São Paulo** – risco torrencial na capital e ABC Paulista (maior colégio do país).
2. **Rio de Janeiro** – risco alto na capital.
3. **Paraná e Rio Grande do Sul** – risco moderado nas capitais.

## 3. Quais candidatos tendem a ser mais afetados

A chuva eleva a abstenção de forma **ampla**. O impacto diferencial nesta versão é estimado de forma simplificada (proporcional à base de votos do 1º turno). Não modelamos ainda heterogeneidade por renda ou perfil de mobilidade.

**Padrões observados:**
- **São Paulo capital** e **São Bernardo**: Lula tinha vantagem no 1º turno → tende a perder mais votos absolutos sob chuva forte (se o efeito for uniforme).
- **Rio de Janeiro capital**, **Guarulhos** e **Campinas**: Flávio à frente → maior exposição relativa de Flávio em votos absolutos.
- Agregado estadual de SP, PR e RS: Flávio tem vantagem estrutural; risco de chuva nessas áreas pode reduzir um pouco sua margem em votos absolutos.
- **Nordeste** (reduto de Lula): tempo bom previsto → pouco impacto climático esperado.

**Conclusão política provisória:**  
Não há evidência, nesta versão, de um viés climatico sistemático e forte favorecendo um dos candidatos em escala nacional. O efeito mais relevante é o **aumento localizado da abstenção** em grandes municípios competitivos do Centro-Sul, onde as margens do 1º turno foram relativamente apertadas.

## 4. Principais limitações e incertezas

1. **Cobertura climática**: previsão detalhada disponível apenas para 15 maiores centros. Interior e municípios menores não quantificados.
2. **Coeficientes do Bot 1**: baseados em literatura + análise cross-section do 1º turno (amostra dos 30 maiores). Efeito “puro” após controles geográficos é positivo mas impreciso. Usamos a regra prática recomendada pelo Bot 1.
3. **Impacto diferencial simplificado**: assume efeito proporcional à base de votos. Não captura possíveis diferenças de propensão a votar sob chuva por perfil socioeconômico.
4. **Dados de 1º turno**: transferência de votos e comportamento de abstenção no 2º turno podem diferir.
5. Esta é uma versão da manhã. Deve ser atualizada com observações reais de precipitação e eventuais novas previsões.

**Transparência:** Todos os efeitos são **estimativas** com faixa de incerteza. Não são previsões determinísticas. O objetivo é informar o acompanhamento público com a melhor síntese possível a partir dos dados disponíveis.

## 5. Arquivos gerados / atualizados

- `impacto_municipios.csv` – 15 municípios prioritários (coeficientes Bot 1)
- `impacto_estados.csv` – 27 UFs + DF
- `impacto_regioes.csv` – 5 grandes regiões
- `ranking_vulnerabilidade.md`
- Este arquivo: `sintese_executiva_impacto.md`

**Pronto para consumo pelo dashboard e pelo site público.**

---
*Documento gerado pelo Bot 4 | Projeto Chuva × Abstenção Eleitoral – Segundo Turno 2026 | Versão 1.1*
