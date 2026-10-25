# Síntese Executiva – Correlação Chuva × Abstenção
**Bot 1 | Projeto “Chuva × Abstenção Eleitoral – Segundo Turno 2026”**  
**Versão utilizável:** 2026-10-25 06:50 (Brasília) — atualizada 06:55 com dados históricos Bot 0  
**Para uso imediato no dashboard e pelo Bot 4**

---

## Resposta direta às perguntas do projeto

### 1. Existe correlação entre precipitação no dia da eleição e abstenção?
**Sim.**  
A literatura internacional (meta-análise de 34 estudos) mostra associação negativa consistente entre chuva e comparecimento. No 1º turno de 2026, nos 30 maiores colégios eleitorais, municípios com mais chuva em 4 de outubro apresentaram, em média, taxas de abstenção mais altas.

### 2. Qual a magnitude típica do efeito?
- **Literatura (referência principal):** +0,4 a +1,0 ponto percentual de abstenção **por centímetro** de chuva no dia da eleição.
- **Observado no 1º turno 2026 (maiores cidades, bruto):** diferença de cerca de **+2,2 pp** entre a faixa “sem chuva relevante” (<5 mm) e a faixa “moderada” (5–20 mm).
- **Análise preliminar independente (Arvor / seções × ERA5, citada por Bot 0):** associação bruta de +2,11 pp onde chuva >5 mm nas horas de votação; efeito se reduz fortemente dentro do município (+0,26 pp, IC inclui zero).
- **Após controles regionais (nossa análise):** o efeito se reduz, mas permanece positivo (impreciso por amostra pequena).

**Regra prática adotada pelo projeto:**
- Chuva moderada (5–20 mm) → expectativa de **+0,5 a +1,2 pp** na abstenção.
- Chuva torrencial / tempestade / risco de alagamento (≥20–30 mm) → expectativa de **+1,2 a +3,0 pp** (podendo ser maior em áreas de vulnerabilidade).

### 3. O efeito sobrevive a controles geográficos?
Parcialmente. Parte da associação observada no 1º turno é explicada por diferenças estruturais entre regiões (Nordeste costuma ter menos chuva e abstenção estruturalmente mais baixa). Ainda assim, a literatura com desenhos mais robustos (efeitos fixos, variação dentro da mesma unidade geográfica) confirma que o efeito da chuva existe independentemente da geografia.

### 4. Correlação ≠ Causalidade
Sim. A análise do 1º turno é correlacional e cross-sectional. Não prova que a chuva *causou* o aumento da abstenção naquele dia. Outros fatores (mobilização partidária, clima político, logística) também operam. Usamos a literatura e o padrão empírico como **melhor estimativa disponível** para o monitoramento de hoje, declarando a incerteza.

---

## Como usar estes números hoje (25/10/2026)

1. **Classificação de risco do projeto (manter):**
   - a) Torrencial / tempestade / alagamento (≥20–30 mm ou alertas)
   - b) Moderada (5–20/30 mm)
   - c) Sem chuva relevante (<5 mm)

2. **Impacto estimado na abstenção (intervalo):**
   - Moderada → +0,5 a +1,2 pp
   - Torrencial → +1,2 a +3,0 pp

3. **Tradução em votos (ordem de grandeza):**
   - Em um município com 1 milhão de aptos, +1 pp de abstenção ≈ **10 mil votos a menos**.
   - Em São Paulo capital (~9,1 mi aptos), +1 pp ≈ **91 mil votos**.

4. **Quem é mais afetado (literatura):** eleitores jovens, de baixa renda e de baixa propensão a votar. Em áreas com risco de alagamento ou transporte precário o efeito pode ser amplificado.

---

## Limitações (transparência máxima)

- Dados de precipitação do 1º turno cobrem prioritariamente os maiores colégios.
- Um único dia de eleição limita a capacidade de isolar o efeito causal.
- O voto obrigatório no Brasil atenua (mas não elimina) o efeito da chuva em comparação com países de voto voluntário.
- Eventos extremos (fechamento de seções, isolamentos) podem gerar impactos maiores do que a relação linear média.
- Histórico de precipitação em dias de eleição (2014–2022 + 2026_1T) disponível para 6 capitais (Bot 0); 2026_1T foi um dos dias mais chuvosos do conjunto nessas cidades (média 8,6 mm).

---

## Arquivos disponíveis em `/home/workdir/artifacts/data/correlacao/`

| Arquivo | Conteúdo |
|---------|----------|
| `literatura_resumo.md` | Revisão da literatura + tamanhos de efeito de referência |
| `analise_1turno_2026.csv` | Dados município a município (30 maiores) + faixa de chuva |
| `resumo_por_faixa_chuva.csv` | Agregados por faixa de precipitação |
| `coeficientes_e_resultados.md` | Tabelas de coeficientes, regressões e interpretação técnica |
| `sintese_executiva.md` | Este documento (didático e transparente) |

**Status:** primeira versão utilizável pronta antes das 08h00.  
Pode alimentar o Bot 4 e o dashboard imediatamente.

---
*Bot 1 – Correlação Científica e Histórica*  
*Projeto Chuva × Abstenção Eleitoral – Segundo Turno 2026*
