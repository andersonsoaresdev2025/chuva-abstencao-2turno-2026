# Conclusão: estimativa do projeto x resultado oficial do 2º turno (25/10/2026)

*Resumo do relatório `comparacao_municipios_2turno.md` (mesma pasta). Todos os números vêm de `comparacao_municipios_2turno.csv` e `resumo.json`, gerados por `scripts/pos_eleicao/` a partir dos arquivos oficiais do TSE e da estimativa final do projeto.*

> **Registro histórico.** A estimativa comparada é a publicada no dia da eleição e congelada às **17:09 BRT** (`data/impacto/atualizacoes/impacto_agora_latest.json`). Ela **não foi alterada** depois do resultado, e o coeficiente do modelo também não. A revisão do coeficiente proposta abaixo é apenas uma sugestão para discussão.

## O que foi comparado

- **Universo:** os 304 municípios cobertos pela estimativa final, todos encontrados nos arquivos do TSE dos dois turnos. Somam 85.908.193 eleitores aptos no 2º turno (54,1% do eleitorado nacional).
- **Medida observada:** variação da abstenção do 1º para o 2º turno em cada município, descontada a variação média da UF.
- **Abstenção nacional:** 21,08% no 1º turno e 19,22% no 2º turno (−1,87 p.p.). Nos 304 municípios cobertos: 20,76% para 18,60% (−2,17 p.p.).
- **Estimativa final (17:09 BRT, previsão + notícias):** +0,34 p.p. na abstenção nacional (faixa +0,19 a +0,48), cerca de 538.510 abstenções extras (307.720 a 769.300). Somando os 304 municípios, as abstenções observadas acima ou abaixo da média de cada UF dão −187.621 eleitores.

## Principais conclusões

1. **A direção é compatível com o modelo.** Onde choveu mais, a abstenção caiu menos que a média do estado. Sem peso por eleitorado, a inclinação é de **+0,22 p.p. por 10 mm** de chuva (IC 95%: +0,14 a +0,31; erro-padrão robusto HC1).

2. **A magnitude ficou em cerca de um terço da usada.** O coeficiente implícito é de **0,022 p.p. por mm** (IC 0,014 a 0,031), contra **0,07 p.p./mm** usado na estimativa (32% do valor). Regredindo o observado sobre o estimado, a inclinação é 0,33 (0,20 a 0,45) sem peso; a correlação entre estimado e observado é de 0,24.

3. **Com peso pelo eleitorado, o efeito não se distingue de zero.** A inclinação ponderada é de +0,08 p.p. por 10 mm (IC −0,17 a +0,34). Com controle por porte do município, fica em +0,18 (IC +0,002 a +0,35), no limite da significância. Com efeito fixo de UF, a inclinação some (+0,03 sem peso, −0,08 com peso). Ou seja: o sinal depende muito de quais municípios pesam mais.

4. **As grandes capitais contradizem o modelo.** São Paulo (17,1 mm) tinha estimativa de +1,20 p.p. e ficou 0,30 p.p. **abaixo** da média de SP. Rio de Janeiro (23,1 mm) tinha +1,62 p.p. estimado e ficou 1,46 p.p. abaixo da média do RJ. Como essas duas cidades concentram muito eleitorado, elas dominam o total nacional estimado. Guarulhos (15,3 mm) foi o caso que bateu: +1,07 estimado e +1,06 observado. Belo Horizonte (−0,45 observado x +0,35 estimado), Campinas (+0,13 x +1,75) e Curitiba (+0,33 x +1,40) ficaram acima ou próximos da média, mas bem abaixo do estimado.

5. **Os 7 municípios com 30 mm ou mais ficaram todos acima da média da UF, mas bem abaixo do estimado.** Mogi Guaçu (61,3 mm), São José dos Campos (55,1), Pouso Alegre (48,1), Guaratinguetá (46,2), Pindamonhangaba (36,9), Ubatuba (33,5) e Itatiba (31,6): média observada de +0,57 p.p. acima da UF, contra +3,13 p.p. estimados em média.

6. **Os ajustes por notícias tiveram resultado misto.** Dos 9 municípios ajustados, 6 ficaram acima da média da UF (Prudentópolis +2,00 p.p., Barracão +1,54, Itapevi +0,77, Curitiba +0,33, Campinas +0,13, Guaratuba +0,13) e 3 abaixo (Belo Horizonte −0,45, São Domingos −1,04, Águas de Chapecó −0,78). O estimado ficou acima do observado em 7 dos 9. Somados, os ajustados tinham 44.810 abstenções extras estimadas, contra −835 observadas em relação à média da UF. Com apenas 9 casos, não dá para dizer que os ajustes melhoraram a estimativa.

7. **Barracão: a evidência é anterior ao dia da eleição.** O ajuste de Barracão (PR) se apoiou em registro de um temporal de 23/10, não de chuva no domingo da votação. O resultado acima da média da UF ali não pode ser atribuído à chuva do dia 25.

## Limitações

- **A variação 1º→2º turno não é abstenção causada pela chuva.** Ela mistura tudo o que mudou entre os turnos (fim das disputas estaduais e proporcionais, segundos turnos estaduais, mobilização, perfil de renda). Descontar a média da UF remove só o que é comum ao estado. A média da UF inclui o próprio município, o que puxa a variação descontada das capitais para zero (São Paulo tem 26,8% do eleitorado de SP; o Rio de Janeiro, 38,5% do RJ).
- **Chuva do modelo Open-Meteo**, não de pluviômetro: um único valor por município, sem distribuição dentro da cidade.
- **Amostra não aleatória:** os 304 municípios são os maiores colégios mais os ajustados por notícias; os resultados não valem para municípios pequenos.
- **Um único dia de eleição:** muita incerteza.
- **Correlação espacial:** os intervalos de confiança assumem independência entre municípios, o que a chuva (que atinge regiões inteiras) viola; os intervalos reais são mais largos.
- Prudentópolis e Águas de Chapecó têm registro às 17:15 no CSV de ajustes, mas já aparecem ativos no snapshot de 17:09; vale o snapshot.

## Proposta de revisão do coeficiente (sugestão para discussão)

*Não aplicada. A estimativa do dia da eleição e o coeficiente de 0,07 p.p./mm permanecem como registro histórico.*

- Reduzir o coeficiente para **cerca de 0,02 p.p. por mm** (faixa de cerca de 0,01 a 0,03, o intervalo sem peso), abaixo da faixa de literatura usada pelo Bot 1 (0,04 a 0,10).
- Rever o efeito por classe do Bot 4: na faixa de 15 a 30 mm ele previa cerca de +2 p.p., e o observado ponderado foi negativo (−0,24 p.p.).
- Avaliar aplicar o efeito só acima de um limiar de chuva e tratar as grandes capitais com cautela.
- Validar com uma referência de comparecimento esperado melhor que o 1º turno (por exemplo, o 2º turno de 2022 por município, ou controle por disputas estaduais) antes de adotar qualquer novo valor.

## Documentos

- Relatório completo: [`comparacao_municipios_2turno.md`](comparacao_municipios_2turno.md) e [`comparacao_municipios_2turno.pdf`](comparacao_municipios_2turno.pdf)
- Dados por município (304 linhas): [`comparacao_municipios_2turno.csv`](comparacao_municipios_2turno.csv)
- Números-chave: [`resumo.json`](resumo.json) · variação por UF: [`uf_variacao.csv`](uf_variacao.csv)
- Fontes e reprodução: [`README.md`](README.md)
