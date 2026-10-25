import json, csv
TS="2026-10-25T09:45:00Z"
F=["timestamp_coleta_utc","timestamp_post","cidade","uf","cidade_risco_previsto","tipo","nivel_risco_implicito","confianca","fonte","tipo_fonte","resumo","link"]
S=[
("2026-10-24T13:44:00Z","Múltiplos (1250 municípios)","SP/RJ/MG/PR/SC/MS","alerta_oficial","alto","alta","INMET (via CNN Brasil)","oficial","Aviso LARANJA de tempestade (Perigo) válido 00h–23h59 BRT de 25/10: 30–60 mm/h ou 50–100 mm/dia, ventos 60–100 km/h, granizo; risco de corte de energia, queda de árvores e alagamentos.","https://www.cnnbrasil.com.br/nacional/sudeste/inmet-alerta-para-tempestade-no-sul-sudeste-e-centro-oeste-veja-areas/"),
("n/d (emissão não exibida; vigência 25/10 00h-23h59 BRT)","Múltiplos (~2400 municípios)","BA/ES/GO/MT/MS/MG/PR/RJ/RS/SC/SP","alerta_oficial","medio","alta","INMET","oficial","Aviso AMARELO de tempestade (Perigo Potencial) válido 00h–23h59 BRT de 25/10: 20–30 mm/h ou até 50 mm/dia, ventos 40–60 km/h, granizo.","https://avisos.inmet.gov.br/56170"),
("2026-10-25T09:28:40Z","São Paulo (estado / RMSP)","SP","alerta_oficial","alto","alta","@defesacivilsp","oficial","Defesa Civil SP prevê domingo de eleição muito instável, chuva moderada a forte, raios, rajadas e risco de granizo; centro, leste do estado e RMSP com maior atenção para alagamentos e enxurradas.","https://x.com/defesacivilsp/status/2114288021990408487"),
("2026-10-25T08:09:00Z","São Paulo","SP","alagamento","medio","alta","CGE-SP","oficial","CGE colocou toda a capital (todas as zonas e marginais) em estado de ATENÇÃO para alagamentos das 03h10 às 05h10 BRT; encerrado, com chuva fraca e tempo chuvoso previsto para a manhã.","https://www.cgesp.org/v3/noticias.jsp?anoMes=2026-10"),
("2026-10-25T08:17:00Z","São Paulo","SP","alagamento","medio","alta","Folha de S.Paulo","imprensa","Bombeiros registraram na noite de sábado 10 chamados de enchente/alagamento, 6 de queda de árvore e 2 de desabamento na capital, sem feridos; estado de atenção encerrado às 5h10.","https://www1.folha.uol.com.br/cotidiano/2026/10/sao-paulo-entra-em-atencao-para-alagamentos-na-madrugada-deste-domingo-25.shtml"),
("2026-10-25T09:19:02Z","Guaratinguetá / Taubaté / Aparecida","SP","chuva","alto","alta","@defesacivilsp","oficial","06h15 BRT: chuva persiste no Vale do Paraíba (Guaratinguetá, Taubaté, Aparecida) com atenção para elevação do nível dos rios.","https://x.com/defesacivilsp/status/2114285595052613818"),
("2026-10-25T08:35:44Z","São José dos Campos / Mogi das Cruzes / Arujá","SP","chuva","medio","alta","@defesacivilsp","oficial","05h30 BRT: chuva persiste na região de São José dos Campos, Mogi das Cruzes e Arujá; atenção à elevação dos rios.","https://x.com/defesacivilsp/status/2114274698091466878"),
("2026-10-25T09:12:02Z","Bauru / Pirajuí / Avaí","SP","chuva","medio","alta","@defesacivilsp","oficial","06h05 BRT: chuva com raios e ventos na região de Bauru, Pirajuí e Avaí.","https://x.com/defesacivilsp/status/2114283833419837630"),
("2026-10-25T07:26:53Z","Campinas / Sumaré / Cosmópolis","SP","chuva","medio","alta","@defesacivilsp","oficial","04h20 BRT: chuva persiste na região de Campinas, Sumaré e Cosmópolis; atenção aos rios.","https://x.com/defesacivilsp/status/2114257374831640719"),
("2026-10-25T07:31:21Z","Sorocaba / Itu / Indaiatuba / Salto","SP","chuva","medio","alta","@defesacivilsp","oficial","04h25 BRT: chuva persiste na região de Itu, Sorocaba, Indaiatuba e Salto; atenção aos rios.","https://x.com/defesacivilsp/status/2114258496883458117"),
("2026-10-25T07:47:01Z","Piracicaba / Limeira / Rio Claro","SP","chuva","medio","alta","@defesacivilsp","oficial","04h40 BRT: chuva persiste na região de Piracicaba, Limeira e Rio Claro; atenção aos rios.","https://x.com/defesacivilsp/status/2114262441551118517"),
("2026-10-25T06:08:45Z","Santos / Cubatão / Peruíbe","SP","chuva","medio","alta","@defesacivilsp","oficial","03h05 BRT: chuva persiste na Baixada Santista (Peruíbe, Santos, Cubatão); atenção aos rios.","https://x.com/defesacivilsp/status/2114237708705091772"),
("2026-10-25T04:06:16Z","Registro / Eldorado / Iguape / Cananéia","SP","chuva","medio","alta","@defesacivilsp","oficial","00h55 BRT: chuva persiste no Vale do Ribeira; atenção à elevação dos rios.","https://x.com/defesacivilsp/status/2114206885758800045"),
("2026-10-25T01:02:12Z","Santos","SP","mobilidade","medio","alta","@CetSantos_","oficial","CET Santos (22h02 BRT de 24/10, véspera): ponto de alagamento na Praça Washington, todas as faixas alagadas mas trecho transitável.","https://x.com/CetSantos_/status/2114160563160830345"),
("2026-10-24T22:19:05Z","Iraí a Porto Mauá (rio Uruguai)","RS","alerta_oficial","alto","alta","@DefesaCivilRS","oficial","Defesa Civil RS: risco ALTO de inundação pela elevação do rio Uruguai de Iraí a Porto Mauá, válido até 19h10 de 25/10.","https://x.com/DefesaCivilRS/status/2114119515961454911"),
("2026-10-25T08:00:00Z","Noroeste do RS","RS","alagamento","medio","media","Portal Band","imprensa","Band: rios subiram no Noroeste do RS, com alagamentos, bloqueio de pontes e 8 pessoas desalojadas.","https://www.band.com.br/politica/eleicoes/chuva-no-dia-da-eleicao-muda-locais-de-votacao-e-poe-estados-em-alerta"),
("2026-10-25T00:01:02Z","Curitiba (CIC)","PR","eleitoral","alto","alta","@tribunapr (Tribuna do Paraná)","imprensa","Temporal de 96,8 mm causou alagamentos e mudança de seção eleitoral na Cidade Industrial de Curitiba (publicado 21h01 BRT de 24/10).","https://x.com/tribunapr/status/2114145173470900636"),
("2026-10-25T00:11:00Z","Curitiba","PR","eleitoral","alto","alta","Clique Paraná / Bem Paraná","imprensa","Curitiba teve 106,6 mm até 18h30 de sábado (recorde diário, Simepar); escola municipal Dario Persiano de Castro Vellozo alagou e a votação foi transferida para o CMEI Hugo Peretti (~400 m); 8 ocorrências de alagamento, alagamentos também em Pinhais.","https://cliqueparana.com.br/noticia/chuva-alaga-escola-e-transfere-local-de-votacao-em-curitiba-b0427855"),
("2026-10-25T08:00:00Z","Curitiba / Guaratuba (PR)","PR","eleitoral","medio","media","Portal Band","imprensa","TRE-PR alterou locais de votação em Curitiba e Guaratuba por impactos da chuva; ~3.700 eleitores paranaenses afetados, avisados por WhatsApp e e-Título.","https://www.band.com.br/politica/eleicoes/chuva-no-dia-da-eleicao-muda-locais-de-votacao-e-poe-estados-em-alerta"),
("2026-10-23T18:22:00Z","Barracão","PR","eleitoral","medio","alta","TRE-PR","oficial","(Contexto, 23/10) Evento meteorológico levou à realocação de ~3,2 mil eleitores da Escola Leonor Castellano para o Centro Comunitário da Igreja Católica, em frente; outras 8 mudanças no interior do PR por clima.","https://www.tre-pr.jus.br/comunicacao/noticias/2026/Outubro/evento-meteorologico-causa-alteracao-de-local-de-votacao-em-barracao"),
("2026-10-25T01:00:46Z","SC / PR / sul do MS / centro-sul de SP","SC/PR/MS/SP","alerta_oficial","alto","media","@g1","imprensa","g1: oito estados com risco de temporal no domingo de eleição; risco alto em faixa de SC, PR, sul do MS e centro-sul de SP.","https://x.com/g1/status/2114160202131866093"),
("2026-10-24T22:29:32Z","São Paulo / Rio de Janeiro","SP/RJ","chuva","alto","media","@metsul","meteorologista","MetSul: alerta de domingo com risco de chuva forte em São Paulo e no Rio de Janeiro.","https://x.com/metsul/status/2114122146998010279"),
("2026-10-25T02:21:01Z","São Paulo","SP","chuva","medio","media","@metsul","meteorologista","MetSul: satélite entre 20h e 23h BRT de sábado mostra áreas de instabilidade intensas sobre SP com chuva forte e temporais.","https://x.com/metsul/status/2114180400411005153"),
("2026-10-24T19:16:02Z","Brasil","BR","eleitoral","baixo","media","@g1","imprensa","(Contexto, véspera) Segundo o TSE, 554 seções eleitorais tiveram alteração de local entre o 1º e o 2º turno (motivos incluem estragos de chuva, obras e falta de energia).","https://x.com/g1/status/2114073447747789153"),
("2026-10-25T07:02:42Z","Duque de Caxias","RJ","chuva","medio","baixa","@crvgabrielle21","relato","Relato individual de chuva forte em Duque de Caxias por volta das 4h BRT.","https://x.com/crvgabrielle21/status/2114251289106505749"),
("2026-10-25T09:35:36Z","Rio de Janeiro (estado, sem bairro)","RJ","chuva","baixo","baixa","@vilerino","relato","Relato individual de chuva no RJ no início da manhã de votação.","https://x.com/vilerino/status/2114289766439010454"),
("2026-10-25T06:05:35Z","São Paulo (Zona Oeste)","SP","chuva","medio","baixa","@XOlirum","relato","Relato individual de granizo na Zona Oeste de São Paulo de madrugada (consistente com alerta oficial).","https://x.com/XOlirum/status/2114236913758376326"),
("2026-10-25T09:18:35Z","Interior de SP (sem cidade)","SP","chuva","medio","baixa","@CleberG78978397","relato","Relato de chuva muito forte no interior de SP às ~6h18 BRT, dificultando o deslocamento para votar.","https://x.com/CleberG78978397/status/2114285483521892575"),
("2026-10-25T06:15:10Z","Ceilândia (Brasília)","DF","mobilidade","baixo","baixa","@AngeloM02543269","relato","Relato individual de falta de energia em Ceilândia Norte na madrugada do dia de votação (não confirmado; urnas funcionam com bateria).","https://x.com/AngeloM02543269/status/2114239323935474019"),
("2026-10-25T09:06:07Z","Rio de Janeiro","RJ","chuva","medio","alta","@AlertaRio","oficial","Sistema Alerta Rio (Prefeitura) publica boletins de chuva a cada ~30 min desde a madrugada (06h04–09h06 UTC); valores em mm estão em imagem, não lidos nesta coleta.","https://x.com/AlertaRio/status/2114282347621413348"),
("2026-10-25T08:29:52Z","Rio de Janeiro (Zona Norte)","RJ","chuva","alto","media","@bilbobolselro + ~8 relatos independentes","relato","Agrupamento de relatos independentes (06h–08h30 UTC) de 'temporal'/chuva muito forte na cidade do Rio, incl. Zona Norte; consistente com aviso INMET e boletins do Alerta Rio.","https://x.com/bilbobolselro/status/2114273222740877452"),
("2026-10-25T08:32:25Z","Rio de Janeiro","RJ","mobilidade","medio","baixa","@eu_avisei_kct","relato","Relato individual de eleitora que diz não conseguir ir a pé votar por causa do temporal e busca transporte por app.","https://x.com/eu_avisei_kct/status/2114273866004484130"),
("2026-10-25T04:46:35Z","Guarulhos","SP","chuva","medio","baixa","@jeonjmart","relato","Relato individual de chuva forte contínua em Guarulhos desde as 22h BRT de sábado.","https://x.com/jeonjmart/status/2114217031390409038"),
("2026-10-25T09:04:21Z","Baixada Santista","SP","chuva","baixo","baixa","@Andrefsto / @Boni_Piccirillo","relato","Dois relatos independentes de que a chuva na Baixada Santista parou por volta das 5h BRT (sinal de melhora, contraste com alertas da madrugada).","https://x.com/Andrefsto/status/2114281902152507783"),
("2026-10-24 (hora n/d)","Mato Grosso do Sul (todas as mesorregiões, incl. Campo Grande)","MS","alerta_oficial","alto","media","INMET (via HoraMS)","imprensa","INMET elevou para LARANJA o aviso de tempestade em todo o MS para domingo 25 (0h–23h59) e segunda até 12h: 30–60 mm/h, ventos 60–100 km/h, granizo. Prefeitura de Campo Grande divulgou horários divergentes (amarelo até 22h59 de 25; laranja a partir de 23h) — conferir. (timestamp_post = data 24/10, hora não informada)","https://horams.com.br/inmet-alerta-laranja-tempestade-ms-domingo-25-eleicao/"),
]
D=[
("2026-10-24T23:12:07Z","@plocsocial (e outros)","Alegação de transferência do local de votação da ex-BBB Gizelly Bicalho de SP para o ES","Desmentido pelo TSE/408ª ZE (eleitora segue habilitada em SP)","https://x.com/plocsocial/status/2114132859552465247"),
("2026-10-25T00:35:47Z","@julyhysteric","'Metade do país' com local de votação alterado","Contradiz dado oficial (TSE: ~554 seções, <0,1%)","https://x.com/julyhysteric/status/2114153915314806966"),
("2026-10-24T20:39:27Z","@fabrinitricolor","Eleitora de SP 'transferida para Montevidéu'","Não verificável / tom sarcástico; sem evidência","https://x.com/fabrinitricolor/status/2114094442428981694"),
("2026-10-25T01:32:08Z","@dcm_noticias / @ojornaleirobr","Números divergentes de seções alteradas (394 seções/123 mil; 442 seções/139 mil)","Números inconsistentes entre si e com g1/TSE (554); aguardar fonte primária TSE","https://x.com/dcm_noticias/status/2114168096395006176"),
("2026-10-25T01:18:19Z","@gbrondi","'Forte chuva atinge SP, MG e RJ' + piada partidária (postado 3x)","Conteúdo opinativo/duplicado; info meteorológica já coberta por fontes oficiais","https://x.com/gbrondi/status/2114164619862319525"),
("2026-10-25T03:35:57Z","@jesskarolinebc / @Anayourgirl","'Curitiba está toda alagada' citando vídeo","Generalização; mídia citada sem data verificável (possível reciclagem); alagamentos reais em Curitiba já cobertos por imprensa","https://x.com/jesskarolinebc/status/2114199258018496512"),
("2026-10-25T06:24:32Z","@JuniorJotaErre2","'Rio de Janeiro sem luz', Light 'boicotando' eleitores","Generalização sem confirmação; acusação sem evidência","https://x.com/JuniorJotaErre2/status/2114241683130921350"),
("2026-10-25T06:43:26Z","@enauhtt / @mygnuts","Chuva forte em 'CG' / 'campo grande'","Local ambíguo (Campo Grande-MS, Campo Grande-RJ ou Campina Grande-PB)","https://x.com/enauhtt/status/2114246439098573126"),
("2026-10-25T07:43:25Z","@gutsspilIed","Abstenção 'vai duplicar' no Japão por chuva","Fora do escopo (exterior) e especulativo","https://x.com/gutsspilIed/status/2114261533366591586"),
("2026-10-25T08:46:16Z","@eusloane","Votação em Dublin parada por falta de energia","Fora do escopo (exterior), não verificado","https://x.com/eusloane/status/2114277349520703678"),
("2026-10-25T01:43:11Z","@grok","Respostas automáticas resumindo alertas do INMET","Resposta gerada por IA, não é fonte primária","https://x.com/grok/status/2114170876820164942"),
("2026-10-25T00:37:00Z","@eumilenaburiti","Alerta de tempestade 'neste sábado, 24'","Refere-se ao dia anterior; desatualizado","https://x.com/eumilenaburiti/status/2114154224460124247"),
("2026-10-25T01:18:28Z","@chatopalestra e dezenas de posts de mobilização","'Alerta de chuva... vá votar' (ambos os lados)","Mobilização partidária, sem informação nova/locável","https://x.com/chatopalestra/status/2114164659582390309"),
]
import unicodedata,os
def n(x): return unicodedata.normalize("NFKD",x).encode("ascii","ignore").decode().lower()
RISK=list(csv.DictReader(open("/home/box/projeto_chuva_abstencao_2026/data/clima/previsoes_2026-10-25/risco_chuva_municipios.csv",encoding="utf-8")))
def risco(cid,uf):
    m=[(r["municipio"],r["nivel_risco"]) for r in RISK if n(r["municipio"]) in n(cid) and r["uf"] in uf]
    if not m: return "n/d (fora da lista)"
    if len(m)==1: return m[0][1]
    return ";".join(f"{a}:{b}" for a,b in m)
rows=[]
for s_ in S:
    d=dict(timestamp_coleta_utc=TS,timestamp_post=s_[0],cidade=s_[1],uf=s_[2],cidade_risco_previsto=risco(s_[1],s_[2]))
    d.update(dict(zip(F[5:],s_[3:])))
    rows.append(d)
OUT="/home/box/projeto_chuva_abstencao_2026/data/social"; os.makedirs(OUT,exist_ok=True); os.chdir(OUT)
stamp="20261025_0945UTC"
with open(f"sinais_{stamp}.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=F); w.writeheader(); w.writerows(rows)
desc=[dict(timestamp_coleta_utc=TS,timestamp_post=d[0],fonte=d[1],alegacao=d[2],motivo_descarte=d[3],link=d[4]) for d in D]
with open(f"descartados_{stamp}.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(desc[0].keys())); w.writeheader(); w.writerows(desc)
json.dump({"timestamp_coleta_utc":TS,"janela":"2026-10-24T18:00Z a 2026-10-25T09:45Z (itens da véspera marcados como contexto)","sinais":rows,"descartados":desc,
 "volume_x_por_hora_query_principal":"ver README; pico 274 posts/h às 01-02h UTC; 57 posts entre 09:00-09:41 UTC"},
 open(f"sinais_{stamp}.json","w",encoding="utf-8"),ensure_ascii=False,indent=2)
print(len(rows),len(desc))
