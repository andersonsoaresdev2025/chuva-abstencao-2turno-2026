# Monitoramento social: chuva × votação (25/10/2026)

As saídas ficam nesta pasta, com o carimbo `YYYYMMDD_HHMMUTC`:
- `sinais_<stamp>.csv/.json`: sinais mantidos. Campos: timestamp_coleta_utc, timestamp_post, cidade, uf, **cidade_risco_previsto** (a/b/c do CSV do Bot 2, ou "n/d"), tipo (chuva/alagamento/mobilidade/eleitoral/alerta_oficial), nivel_risco_implicito (baixo/medio/alto), confianca (baixa/media/alta), fonte, tipo_fonte (oficial/meteorologista/imprensa/relato), resumo, link.
- `descartados_<stamp>.csv`: itens descartados, com o motivo (desinformação, local ambíguo, fora do escopo, desatualizado, IA, mobilização partidária).
- `resumo_<stamp>.md`: resumo em pt-BR (alertas em vigor, sinais por região, ranking de risco, limitações).
- `build_<stamp>.py`: script que gerou os arquivos. Os sinais são curados à mão: o script só serializa e cruza com `risco_chuva_municipios.csv`. Para a próxima coleta, copie o script, troque `TS` e as listas `S`/`D`.

## Rotina horária (repetir a cada ~60 min durante a votação, 8h–17h BRT)
X MCP (namespace `x`, ~12–15 chamadas por ciclo; limite de 30/min e 1000/dia). Em todas as buscas use `start_time` = horário da última coleta, `max_results=25` e `expansions=author_id`.
1. `search_posts_all`, geral, por relevância:
   `(chuva OR tempestade OR alagamento OR temporal OR enchente) (eleição OR urna OR votação OR "seção eleitoral" OR "2º turno" OR "segundo turno" OR votar) lang:pt -is:retweet`
2. Contas oficiais, por data:
   `(from:defesacivilsp OR from:DefesaCivilRS OR from:DefesaCivilPR OR from:defesacivilsc OR from:AlertaRio OR from:OperacoesRio OR from:CetSantos_ OR from:TSEjusbr OR from:TREPR OR from:TRERJ OR from:TRESP OR from:metsul OR from:climatempo OR from:inmet OR from:g1 OR from:tribunapr) -is:retweet`
3. Cidades prioritárias (risco a), da Grande SP:
   `(chuva OR alagamento OR alagada OR temporal OR "queda de árvore" OR "sem energia") (Guarulhos OR "Santo André" OR "São Bernardo" OR Osasco OR ABC OR "São Paulo" OR Campinas) lang:pt -is:retweet`
4. Cidades prioritárias do Rio, Curitiba e Campo Grande:
   `(chuva OR alagamento OR temporal OR "sem luz" OR bolsão) ("São Gonçalo" OR "Nova Iguaçu" OR "Duque de Caxias" OR Baixada OR "Rio de Janeiro" OR Curitiba OR "Campo Grande") lang:pt -is:retweet`
5. Seções afetadas:
   `(TRE OR TSE OR "seção eleitoral" OR "local de votação" OR "zona eleitoral") (chuva OR temporal OR alagamento OR "sem energia" OR transferida OR fila) lang:pt -is:retweet`
6. Relatos no local:
   `(chovendo OR chuva OR alagad OR temporal) (votar OR votei OR fila OR "local de votação" OR urna OR seção) lang:pt -is:retweet -is:reply` (por data)
7. `get_posts_counts_recent`, com a consulta do item 1 e `granularity=hour`, para medir o volume. Linha de base: 57 posts entre 06h00 e 06h41 BRT.
8. `search_news` com `chuva eleição segundo turno Brasil` (`max_age_hours=6`).

Fontes web (WebSearch/WebFetch):
- INMET: https://alertas2.inmet.gov.br / https://avisos.inmet.gov.br / https://portal.inmet.gov.br
- CGE SP: https://www.cgesp.org/v3/noticias.jsp
- Defesa Civil RS: https://www.defesacivil.rs.gov.br ; SC: https://www.defesacivil.sc.gov.br/categoria/alerta/
- TRE-PR: https://www.tre-pr.jus.br/comunicacao/noticias
- Buscas: "<cidade> alagamento votação hoje", "TRE <UF> seção transferida chuva", "Defesa Civil <cidade> alerta 25 outubro"

## Critérios
- **Confiança alta**: órgão oficial ou imprensa com fonte oficial. **Média**: imprensa/meteorologista sem fonte primária, ou ≥3 relatos independentes consistentes. **Baixa**: relato individual.
- **Descartar**: o que contradiz uma fonte oficial (ex.: desmentido do TSE), mídia de data não verificável, local ambíguo, itens do exterior, respostas de IA e mobilização partidária sem fato novo.
- Nunca registrar post, link ou número que não tenha sido visto na coleta.
