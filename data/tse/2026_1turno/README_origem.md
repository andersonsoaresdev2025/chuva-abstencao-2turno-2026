# Dados TSE – 1º Turno Eleições 2026 (Presidente)

**Data/hora do download (Bot 0):** 2026-10-25 ~09:00 UTC-3 (Brasília)

## Fonte primária
- Sistema de Divulgação de Resultados do TSE: https://resultados.tse.jus.br
- Portal de Dados Abertos do TSE: https://dadosabertos.tse.jus.br/dataset/resultados-2026
- Dados processados e organizados a partir de coleta oficial (JSON do sistema de totalização) disponibilizados em repositório público de auditoria:  
  https://github.com/tatipara/eleicao_2026_1turno  
  (script que baixa diretamente os arquivos oficiais de divulgação do TSE e exporta CSVs limpos)

## Arquivos nesta pasta

| Arquivo | Descrição | Linhas approx. |
|---------|-----------|----------------|
| `votacao_municipio.csv` | Votação nominal por município × candidato (long format). Colunas principais: uf, cd_tse, cd_ibge, municipio, numero, candidato, partido, votos, pct_validos, st (situação) | ~69k |
| `presidente_2026_municipios_wide.csv` | Mesma votação em formato wide (uma coluna por candidato) | ~5.7k |
| `abstencao_municipio.csv` (= meta_por_municipio.csv) | Eleitorado apto, comparecimento, abstenção, votos LULA/BOLSONARO/outros/brancos-nulos 2026 + comparativos 2022 por município | ~5.7k |
| `abstencao_por_uf.csv` | Resumo de abstenção por UF | 29 |
| `meta_por_municipio.csv` | Cópia integral do arquivo de metadados/resumo (inclui variáveis de cenário 2º turno) | ~5.7k |

## Campos-chave de abstenção (`abstencao_municipio.csv`)
- `APTOS_2026`: eleitores aptos
- `COMPARECIMENTO_2026`: votos apurados (comparecimento)
- `ABSTENCAO_2026`: abstenção absoluta
- `PCT_ABSTENCAO_2026`: percentual de abstenção
- Também contém resultados 2022 e 2026 para Lula/Bolsonaro e indicadores derivados

## Observações
- Totalização final do 1º turno: 100% das seções (atualizado ~05/10/2026 12:51).
- Abstenção nacional 1º turno ~21%.
- Códigos de município: CD_MUNICIPIO (TSE) e cd_ibge disponíveis nos arquivos de votação.
- Para dados oficiais brutos adicionais (seção, zona, BU etc.) consultar diretamente o dataset “Resultados - 2026” no portal de dados abertos do TSE.

## Licença
Dados oficiais do TSE – uso público conforme política de dados abertos da Justiça Eleitoral (Creative Commons Attribution nos conjuntos do portal).
