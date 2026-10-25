# Revisão da Literatura: Precipitação e Abstenção/Comparecimento Eleitoral
**Bot 1 – Correlação Científica e Histórica**  
**Projeto:** Chuva × Abstenção Eleitoral – Segundo Turno 2026  
**Data/hora da síntese:** 2026-10-25 ~06:40 (Brasília)  
**Fonte prioritária de meta-análise:** Damsbo-Svendsen & Hansen (2023), *Electoral Studies*

---

## 1. Principais achados internacionais (meta-análises e estudos robustos)

### Meta-análise de 34 estudos (Damsbo-Svendsen & Hansen, 2023)
- **Consenso dominante:** a grande maioria dos estudos encontra associação **negativa** entre precipitação no dia da eleição e turnout (comparecimento).
- **Efeito médio não ponderado:** ≈ **−0,82 pontos percentuais (pp) por centímetro** de chuva.
- **Estimativa ponderada (excluindo dois outliers positivos):** ≈ **−0,42 pp por cm**.
- Estudo próprio dos autores (Dinamarca, painel individual validado + dados meteorológicos de alta resolução): **−0,95 pp por cm** de chuva. Efeito até 6× maior entre eleitores jovens/marginais.
- Sol/clima agradável aumenta o comparecimento.

### Outros estudos de referência
| Estudo | Contexto | Efeito estimado | Observações |
|--------|----------|-----------------|-------------|
| Gomez, Hansford & Krause (vários) | EUA | ~ −1 pp por polegada (~ −0,4 pp/cm) | Clássico; efeito partidário em alguns desenhos |
| Fujiwara et al. (2016) | EUA | ~0,6 pp de abstenção adicional por ~10 mm | Benchmark usado em estudos brasileiros |
| González (2026) | Argentina (voto obrigatório) | −0,08 pp por mm de chuva no horário de votação | Efeito persiste mesmo com obrigatoriedade; sem viés partidário detectado |
| Persson et al. (Suécia) | Suécia (alto turnout) | Efeito nulo ou muito fraco | Contextos de alto engajamento e baixo custo de votação atenuam o efeito |

**Conclusão da literatura internacional:** chuva no dia da eleição eleva o custo de votar (mobilidade, desconforto, risco) e reduz o comparecimento de forma modesta, porém electoralmente relevante em disputas apertadas. O efeito é maior sobre eleitores de baixa propensão (jovens, baixa renda, menos engajados).

---

## 2. Evidência brasileira e latino-americana

- Estudos específicos de chuva × abstenção em eleições presidenciais brasileiras ainda são escassos na literatura acadêmica indexada.
- **Estudo recente (Calafate, Costa & Pessoa, 2026):** seca extrema (baixa vazão de rios) aumenta abstenção em ~0,6 pp em comunidades dependentes de transporte fluvial (dados de seções eleitorais 2010–2024). Efeito concentrado e comparável em magnitude a ~10 mm de chuva no benchmark americano.
- Menções pontuais em relatórios do TSE e na imprensa associam chuvas intensas locais a mudanças de locais de votação e possíveis impactos em abstenção (ex.: Porto Velho 2024, Curitiba 2026).
- A literatura brasileira sobre abstenção enfatiza mais fatores estruturais (idade, escolaridade, distância até o local de votação, obrigatoriedade) do que clima. O clima aparece como fator circunstancial de custo.

**Implicação para o Brasil (voto obrigatório):** o efeito da chuva tende a ser **menor** do que em sistemas de voto voluntário, mas **não nulo**, especialmente em áreas de difícil acesso, periferias urbanas com alagamentos e entre eleitores de baixa propensão.

---

## 3. Tamanhos de efeito típicos adotados como referência neste projeto

Para estimativas de impacto (Bot 4 e dashboard), recomendamos usar intervalos conservadores derivados da literatura:

| Cenário de chuva (dia da eleição) | Efeito esperado na abstenção | Fonte / racional |
|-----------------------------------|------------------------------|------------------|
| < 5 mm (sem chuva relevante) | Referência (0) | — |
| 5–20 mm (moderada) | +0,3 a +1,0 pp | ~0,5–1,0 × efeito por cm |
| ≥ 20–30 mm ou alerta de tempestade/alagamento | +1,0 a +2,5 pp (ou mais localmente) | Efeito acumulado + risco de mobilidade |

**Efeito por cm de precipitação (referência central):** **0,5 a 1,0 pp de aumento na abstenção**.

---

## 4. Limitações da literatura (transparência)

- Grande parte dos estudos é de países de voto voluntário e clima temperado.
- Poucos estudos usam desenho causal forte (ex.: variação espacial fina + efeitos fixos de unidade geográfica).
- Efeitos partidos (viés) aparecem em alguns contextos (EUA) e não em outros (Argentina).
- Não captura bem eventos extremos de alagamento/deslizamento que fecham seções ou isolam comunidades.
- Correlação ≠ causalidade em desenhos puramente cross-sectionais.

---

## 5. Referências principais

1. Damsbo-Svendsen, S. & Hansen, K. M. (2023). When the election rains out and how bad weather excludes marginal voters from turning out. *Electoral Studies*, 81, 102573.  
2. González, F. A. I. (2026). Rain, temperature, and votes: Weather effects on electoral participation in Argentina.  
3. Calafate, V., Costa, F. & Pessoa, J. P. (2026). Climate Barriers to Democratic Participation (Brasil, seca/rios).  
4. Fujiwara, T. et al. (2016) e literatura clássica de weather & turnout (Gomez et al.).

**Nota adicional (integrada de Bot 0):** análise preliminar de seções eleitorais × ERA5 no 1º turno 2026 (Arvor) reporta associação bruta de +2,11 pp de abstenção onde chuva >5 mm nas horas de votação; efeito se reduz dentro do município. Consistente com o padrão encontrado nesta análise dos maiores colégios.

**Timestamp de coleta da literatura:** 2026-10-25 (manhã).  
**Status:** utilizável para o dashboard e para o Bot 4 a partir das 08h00.
