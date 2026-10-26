"""Pós-eleição, passo 2: CSV, gráficos, relatório .md e resumo.json (números usados no site e no dashboard)."""
import json, re
import pandas as pd, numpy as np, statsmodels.formula.api as smf
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from pathlib import Path as _P
import os as _os
ROOT=_P(__file__).resolve().parents[2]
OUT=ROOT/"data"/"resultado_2turno"
_os.chdir(OUT)  # entradas em tse_2t/, saídas nesta pasta
REPO=str(ROOT)
d=pd.read_pickle(".base_cache.pkl"); d["chuva"]=d.precip_acum_mm; d["log_aptos"]=np.log(d.aptos_2t)
snap=json.load(open(f"{REPO}/data/impacto/atualizacoes/impacto_agora_latest.json"))
if snap.get("gerado_em_brt")!="2026-10-25 17:09 BRT": print("AVISO: snapshot não é o final de 17:09 BRT:", snap.get("gerado_em_brt"))
rn=snap["previsao_mais_noticias"]; r0=snap["previsao"]
ufc=pd.read_csv("uf_variacao.csv")
aj=pd.read_csv(f"{REPO}/data/ajustes/ajustes_impacto_noticias.csv")

def br(x,c=2,sinal=False):
    if pd.isna(x): return "n/d"
    s=f"{x:+,.{c}f}" if sinal else f"{x:,.{c}f}"
    return s.replace(",","X").replace(".",",").replace("X",".").replace("-","−")
def bi(x,sinal=False): return br(round(x),0,sinal)

# ---------------- CSV
d["ajuste_txt"]=np.where(d.ajuste_noticias=="sim","sim","não")
out=pd.DataFrame({
 "codigo_ibge":d.codigo_ibge,"codigo_tse":d.cd_tse,"municipio":d.municipio_nome,"uf":d.uf,
 "aptos_1t":d.aptos_1t,"aptos_2t":d.aptos_2t,
 "abstencao_1t":d.abst_1t,"abstencao_2t":d.abst_2t,
 "abstencao_pct_1t":d.pct_abst_1t.round(2),"abstencao_pct_2t":d.pct_abst_2t.round(2),
 "variacao_pp":d.var_pp.round(2),"variacao_media_uf_pp":d.var_uf_pp.round(2),
 "variacao_descontada_media_uf_pp":d.var_desc_uf_pp.round(2),
 "chuva_08_17h_mm_modelo":d.chuva,"chuva_usada_mm_com_ajuste":d.precip_usado_mm,
 "nivel_risco":d.nivel_risco,"nivel_risco_so_previsao":d.nivel_risco_so_previsao,
 "ajuste_noticias":d.ajuste_txt,"ajuste_nivel":d.ajuste_nivel,"ajuste_confianca":d.ajuste_confianca,
 "efeito_estimado_pp_lo":d.efeito_abst_pp_lo,"efeito_estimado_pp_mid":d.efeito_abst_pp_mid,"efeito_estimado_pp_hi":d.efeito_abst_pp_hi,
 "abstencoes_extras_estimadas_lo":d.ia_extras_lo,"abstencoes_extras_estimadas_mid":d.ia_extras_mid,"abstencoes_extras_estimadas_hi":d.ia_extras_hi,
 "efeito_classe_bot4_pp_lo":d.efeito_abstencao_pp_lo,"efeito_classe_bot4_pp_mid":d.efeito_abstencao_pp_mid,"efeito_classe_bot4_pp_hi":d.efeito_abstencao_pp_hi,
 "abstencoes_extras_classe_bot4_mid":d.abstencoes_extras_mid,
 "abstencoes_observadas_acima_media_uf_eleitores":d.abst_acima_media_uf_eleitores,
 "diferenca_observado_menos_estimado_pp":(d.var_desc_uf_pp-d.efeito_abst_pp_mid).round(2),
 "pct_flavio_1t":d.pct_flavio_1t,"pct_lula_1t":d.pct_lula_1t,
 "votos_flavio_2t":d.votos_flavio_2t,"votos_lula_2t":d.votos_lula_2t,
 "pct_flavio_2t_validos":d.pct_flavio_2t.round(2),"pct_lula_2t_validos":d.pct_lula_2t.round(2),
 "secoes_totalizadas_pct_2t":d.secoes_pct_2t,"totalizacao_tse_2t":d.totalizacao_2t,
})
out.sort_values("aptos_2t",ascending=False).to_csv("comparacao_municipios_2turno.csv",index=False,encoding="utf-8")

# ---------------- stats
def fit(f,df,w=None):
    return (smf.wls(f,df,weights=w) if w is not None else smf.ols(f,df)).fit(cov_type="HC1")
def linha(m,var,esc=10):
    b=m.params[var]*esc; lo,hi=m.conf_int().loc[var]*esc
    return br(b,3,True), f"{br(lo,3,True)} a {br(hi,3,True)}", br(m.pvalues[var],3), br(m.rsquared,3)
reg=[]
for nome,df in [("Todos (304)",d),("Só SP",d[d.uf=="SP"]),("Só PR",d[d.uf=="PR"])]:
    for lab,f in [("simples","var_desc_uf_pp ~ chuva"),("controle de porte (log aptos)","var_desc_uf_pp ~ chuva + log_aptos")]:
        for wl,w in [("não",None),("sim (aptos)",df.aptos_2t)]:
            reg.append((nome,len(df),lab,wl)+linha(fit(f,df,w),"chuva"))
mfe=fit("var_pp ~ chuva + C(uf)",d); mfew=fit("var_pp ~ chuva + C(uf)",d,d.aptos_2t)
reg.append(("Todos, efeito fixo de UF (cobertos)",len(d),"var. bruta ~ chuva + UF","não")+linha(mfe,"chuva"))
reg.append(("Todos, efeito fixo de UF (cobertos)",len(d),"var. bruta ~ chuva + UF","sim (aptos)")+linha(mfew,"chuva"))
m_s=fit("var_desc_uf_pp ~ chuva",d); m_w=fit("var_desc_uf_pp ~ chuva",d,d.aptos_2t)
m_cw=fit("var_desc_uf_pp ~ chuva + log_aptos",d,d.aptos_2t); m_c=fit("var_desc_uf_pp ~ chuva + log_aptos",d)
oe=fit("var_desc_uf_pp ~ efeito_abst_pp_mid",d); oew=fit("var_desc_uf_pp ~ efeito_abst_pp_mid",d,d.aptos_2t)
ob4=fit("var_desc_uf_pp ~ efeito_abstencao_pp_mid",d); ob4w=fit("var_desc_uf_pp ~ efeito_abstencao_pp_mid",d,d.aptos_2t)
corr_ch=np.corrcoef(d.chuva,d.var_desc_uf_pp)[0,1]; corr_e=np.corrcoef(d.efeito_abst_pp_mid,d.var_desc_uf_pp)[0,1]

bins=[-0.01,1,5,15,30,1e9]; labs=["0 a 1","1 a 5","5 a 15","15 a 30","30 ou mais"]
d["faixa"]=pd.cut(d.chuva,bins,labels=labs)
fx=[]
for f,x in d.groupby("faixa",observed=True):
    fx.append((f,len(x),bi(x.aptos_2t.sum()),br(x.chuva.mean(),1),br(x.var_pp.mean(),2,True),br(x.var_desc_uf_pp.mean(),2,True),
               br(np.average(x.var_desc_uf_pp,weights=x.aptos_2t),2,True),br(np.average(x.efeito_abst_pp_mid,weights=x.aptos),2,True),
               br(np.average(x.efeito_abstencao_pp_mid,weights=x.aptos),2,True),bi(x.ia_extras_mid.sum()),bi(x.abst_acima_media_uf_eleitores.sum(),True)))

# national
nat2=json.load(open("tse_2t/ab_2t.json"))["abr"]; brr=[a for a in nat2 if a["tpabr"]=="br"][0]["e"]
apt2,ab2=int(brr["te"]),int(brr["a"]); apt1,ab1=int(ufc.aptos_1t.sum()),int(ufc.abst_1t.sum())
uf_ex=ufc[ufc.uf!="ZZ"]; apt1x,ab1x=uf_ex.aptos_1t.sum(),uf_ex.abst_1t.sum(); apt2x,ab2x=uf_ex.aptos_2t.sum(),uf_ex.abst_2t.sum()
cov1=d.abst_1t.sum()/d.aptos_1t.sum()*100; cov2=d.abst_2t.sum()/d.aptos_2t.sum()*100

# ---------------- charts
fig,ax=plt.subplots(figsize=(9,6))
s=np.sqrt(d.aptos_2t)/25
cores={"torrencial":"#c0392b","moderada":"#e67e22","sem_chuva_relevante":"#27ae60"}
for k,g in d.groupby("nivel_risco"):
    ax.scatter(g.chuva,g.var_desc_uf_pp,s=np.sqrt(g.aptos_2t)/25,alpha=.55,c=cores.get(k,"gray"),label=k.replace("_"," "),edgecolor="k",linewidth=.3)
xs=np.linspace(0,d.chuva.max(),50)
ax.plot(xs,m_s.params.Intercept+m_s.params.chuva*xs,"k-",label=f"reta simples ({br(m_s.params.chuva*10,2,True)} p.p./10 mm)")
ax.plot(xs,m_w.params.Intercept+m_w.params.chuva*xs,"k--",label=f"reta ponderada por aptos ({br(m_w.params.chuva*10,2,True)} p.p./10 mm)")
ax.plot(xs,xs*0.07+m_s.params.Intercept,":",color="#12324f",label="inclinação do Bot 1 (0,7 p.p./10 mm), mesmo intercepto")
for _,r in d.sort_values("aptos_2t",ascending=False).head(8).iterrows():
    ax.annotate(r.municipio_nome,(r.chuva,r.var_desc_uf_pp),fontsize=7)
ax.axhline(0,color="gray",lw=.5); ax.set_xlabel("Chuva 08-17h (mm, Open-Meteo, modelo)"); ax.set_ylabel("Variação da abstenção 1T→2T descontada a média da UF (p.p.)")
ax.set_title("304 municípios cobertos: chuva x variação da abstenção (tamanho = eleitorado)"); ax.legend(fontsize=7); fig.tight_layout(); fig.savefig("grafico_chuva_vs_variacao.png",dpi=150)
fig,ax=plt.subplots(figsize=(7.5,6))
ax.scatter(d.efeito_abst_pp_mid,d.var_desc_uf_pp,s=s,alpha=.55,c=d.uf.eq("SP").map({True:"#2c7fb8",False:"#999"}),edgecolor="k",linewidth=.3)
lim=[min(d.var_desc_uf_pp.min(),0)-.2,max(d.efeito_abst_pp_mid.max(),d.var_desc_uf_pp.max())+.2]
ax.plot(lim,lim,"r:",label="observado = estimado")
xe=np.linspace(0,d.efeito_abst_pp_mid.max(),20); ax.plot(xe,oe.params.Intercept+oe.params.efeito_abst_pp_mid*xe,"k-",label=f"ajuste simples (inclinação {br(oe.params.efeito_abst_pp_mid,2)})")
for _,r in d.sort_values("aptos_2t",ascending=False).head(6).iterrows():
    ax.annotate(r.municipio_nome,(r.efeito_abst_pp_mid,r.var_desc_uf_pp),fontsize=7)
ax.set_xlabel("Efeito estimado (p.p., previsão + notícias, ponto central)"); ax.set_ylabel("Observado: variação descontada a média da UF (p.p.)")
ax.set_title("Estimado x observado (azul = SP)"); ax.legend(fontsize=8); fig.tight_layout(); fig.savefig("grafico_estimado_vs_observado.png",dpi=150)

# ---------------- md
L=[]; A=L.append
def tab(cab,linhas):
    A("| "+" | ".join(cab)+" |"); A("|"+"|".join(["---"]*len(cab))+"|")
    for l in linhas: A("| "+" | ".join(str(x) for x in l)+" |")
    A("")
A("# Chuva x abstenção no 2º turno de 2026: estimativa do projeto vs resultado oficial, por município")
A("")
A("*Documento público do projeto, gerado por `scripts/pos_eleicao/gerar.py` a partir dos arquivos listados em Fontes, após a totalização final do TSE (25/10/2026, 23:26). Todos os números vêm desses arquivos. A estimativa comparada é a congelada às 17:09 BRT do dia da eleição, mantida sem alteração como registro histórico. Conclusão resumida em `CONCLUSAO.md`.*")
A("")
A("> **Atenção:** a comparação usa a variação da abstenção do 1º para o 2º turno. Essa variação NÃO é a abstenção causada pela chuva: ela mistura tudo o que mudou entre os turnos (fim das disputas estaduais e proporcionais, mobilização, feriado, eleitores no exterior etc.). Descontar a média da UF remove o que é comum ao estado inteiro, mas não isola a chuva.")
A("")
A("## 1. Método")
A("")
A(f"- **Universo:** os {len(d)} municípios cobertos pela estimativa final de 17:09 BRT (`impacto_agora_latest.json`, {snap['n_ajustes_ativos']} ajustes por notícias ativos). Todos os {len(d)} foram encontrados nos arquivos do TSE do 1º e do 2º turno; nenhum ficou de fora. Eles somam {bi(d.aptos_2t.sum())} eleitores aptos no 2º turno ({br(d.aptos_2t.sum()/apt2*100,1)}% do eleitorado nacional).")
A("- **Abstenção 1º turno:** `data/tse/2026_1turno/abstencao_municipio.csv` (ABSTENCAO_2026 / APTOS_2026). **2º turno:** arquivos oficiais `tse_2t/ab_<uf>.json` do TSE (eleição 6258, totalização final, 100% das seções), conferidos um a um com o arquivo municipal de resultado `tse_2t/municipios/<uf><cód>-c0001-e006258-u.json` (aptos e abstenção idênticos nos 304).")
A("- **Média da UF:** variação da abstenção do estado inteiro (todos os municípios, cobertos ou não): 1º turno de `abstencao_por_uf.csv`, 2º turno de `tse_2t/ab_2t.json`. **Variação descontada** = variação do município menos a da UF. **Abstenções acima/abaixo da média da UF (eleitores)** = variação descontada x aptos do 2º turno / 100.")
A("- **Chuva:** acumulado 08-17h do Open-Meteo (modelo, não pluviômetro) usado no cálculo final. A coluna \"chuva usada\" aplica o piso dos ajustes por notícias (a = 20 mm, b = 5 mm).")
A(f"- **Efeito estimado:** o número publicado no site e no dashboard (\"previsão + notícias\"): chuva usada x coeficiente do Bot 1 (0,04 / 0,07 / 0,10 p.p. por mm). Para referência, o CSV também traz o efeito por classe do Bot 4 (a: 1,2 / 2,0 / 3,0; b: 0,5 / 0,85 / 1,2; c: 0 / 0,15 / 0,4 p.p.).")
A("- **Inclinação:** regressão da variação descontada sobre a chuva (mm), sem peso e com peso pelo eleitorado, com erro-padrão robusto (HC1) e intervalo de 95%. Inclinações apresentadas em p.p. por 10 mm.")
A("- **Resultado do 2º turno por candidato:** votos e % de votos válidos de Flávio Bolsonaro (22) e Lula (13) nos arquivos municipais do TSE.")
A("")
A("## 2. Resumo nacional e por UF")
A("")
A(f"- **Abstenção nacional (TSE, inclui exterior):** {br(ab1/apt1*100,2)}% no 1º turno para {br(ab2/apt2*100,2)}% no 2º turno ({br(ab2/apt2*100-ab1/apt1*100,2,True)} p.p.). Sem o exterior: {br(ab1x/apt1x*100,2)}% para {br(ab2x/apt2x*100,2)}% ({br(ab2x/apt2x*100-ab1x/apt1x*100,2,True)} p.p.).")
A(f"- **Nos 304 municípios cobertos:** {br(cov1,2)}% para {br(cov2,2)}% ({br(cov2-cov1,2,True)} p.p.).")
A(f"- **Estimativa final do projeto (17:09 BRT, previsão + notícias):** +{br(rn['abstencao_nacional_pp']['mid'],2)} p.p. na abstenção nacional (faixa +{br(rn['abstencao_nacional_pp']['min'],2)} a +{br(rn['abstencao_nacional_pp']['max'],2)}), cerca de {bi(rn['abstencoes_extras']['mid'])} abstenções extras ({bi(rn['abstencoes_extras']['min'])} a {bi(rn['abstencoes_extras']['max'])}). Só previsão: {bi(r0['abstencoes_extras']['mid'])}. O rascunho interno anterior (não publicado) citava 523 mil e +0,33 p.p.; os valores do arquivo final são os acima.")
A(f"- **Soma das abstenções acima/abaixo da média da UF nos 304:** {bi(d.abst_acima_media_uf_eleitores.sum(),True)} eleitores (estimado: {bi(d.ia_extras_mid.sum())}). Ou seja, os municípios cobertos, em conjunto, reduziram a abstenção um pouco mais que os seus estados.")
A("")
g=d.groupby("uf").apply(lambda x: pd.Series(dict(n=len(x),apt=x.aptos_2t.sum(),ch=np.average(x.chuva,weights=x.aptos_2t),est=np.average(x.efeito_abst_pp_mid,weights=x.aptos),dem=np.average(x.var_desc_uf_pp,weights=x.aptos_2t))))
u=ufc.set_index("uf").join(g).sort_values("aptos_2t",ascending=False)
tab(["UF","Abst. 1T %","Abst. 2T %","Variação UF (p.p.)","Municípios cobertos","Aptos cobertos","Chuva média pond. (mm)","Efeito estimado pond. (p.p.)","Var. descontada pond. dos cobertos (p.p.)"],
    [(k,br(r.pct_1t),br(r.pct_2t),br(r.var_uf_pp,2,True),int(r.n) if pd.notna(r.n) else 0,bi(r.apt) if pd.notna(r.apt) else "-",br(r.ch,1) if pd.notna(r.ch) else "-",br(r.est,2,True) if pd.notna(r.est) else "-",br(r.dem,2,True) if pd.notna(r.dem) else "-") for k,r in u.iterrows()])
corr_uf=np.corrcoef(u.dropna().est,u.dropna().var_uf_pp)[0,1]
A(f"No nível estadual não aparece efeito da chuva: a correlação entre o efeito estimado ponderado da UF e a variação da UF é {br(corr_uf,2,True)} (UFs com município coberto, exterior fora). AP, RR, AC e AM tiveram as maiores altas de abstenção sem chuva relevante estimada, o que indica fatores não ligados à chuva, não analisados aqui.")
A("")
A("## 3. Faixas de chuva (08-17h, mm)")
A("")
tab(["Faixa (mm)","n","Aptos","Chuva média","Variação média (p.p.)","Var. descontada, média simples","Var. descontada, média pond.","Efeito estimado pond. (projeto)","Efeito por classe Bot 4 pond.","Abst. extras estimadas","Abst. observadas acima da média da UF"],fx)
A("Na média simples, a variação descontada sobe com a chuva (municípios sem chuva tiveram queda maior de abstenção que o seu estado). Na média ponderada pelo eleitorado o padrão é fraco e não monotônico: a faixa de 15 a 30 mm, que reúne São Paulo e Rio de Janeiro, fica abaixo de zero.")
A("")
A("## 4. Inclinação (p.p. por 10 mm de chuva)")
A("")
tab(["Amostra","n","Modelo","Peso por eleitorado","Inclinação","IC 95%","p-valor","R²"],reg)
A(f"- **Sem peso:** {br(m_s.params.chuva*10,3,True)} p.p. por 10 mm (IC 95% {br(m_s.conf_int().loc['chuva'][0]*10,3,True)} a {br(m_s.conf_int().loc['chuva'][1]*10,3,True)}), estatisticamente diferente de zero. Correlação chuva x variação descontada: {br(corr_ch,2)}.")
A(f"- **Ponderado por eleitorado:** {br(m_w.params.chuva*10,3,True)} (IC {br(m_w.conf_int().loc['chuva'][0]*10,3,True)} a {br(m_w.conf_int().loc['chuva'][1]*10,3,True)}), não distinguível de zero; com controle de porte, {br(m_cw.params.chuva*10,3,True)} (IC {br(m_cw.conf_int().loc['chuva'][0]*10,3,True)} a {br(m_cw.conf_int().loc['chuva'][1]*10,3,True)}), no limite da significância. As grandes cidades pesam muito e divergem entre si (Rio de Janeiro bem abaixo da média do RJ; Guarulhos bem acima da média de SP).")
A(f"- **SP (n = {int((d.uf=='SP').sum())}):** inclinação positiva e significativa nas versões sem peso e com controle de porte. **PR (n = {int((d.uf=='PR').sum())}):** sem relação detectável (IC amplo, em torno de zero). Outras UFs têm n pequeno demais para um subconjunto confiável.")
A("")
A("## 5. Coeficiente estimado (Bot 1) x implícito")
A("")
A(f"- **Coeficiente usado pelo projeto:** 0,07 p.p. por mm (0,7 p.p. por 10 mm; faixa 0,04 a 0,10).")
A(f"- **Implícito (sem peso):** {br(m_s.params.chuva,4)} p.p. por mm, cerca de {br(m_s.params.chuva/0.07*100,0)}% do coeficiente do Bot 1; o IC 95% ({br(m_s.conf_int().loc['chuva'][0],4)} a {br(m_s.conf_int().loc['chuva'][1],4)}) fica abaixo até do limite inferior do Bot 1 (0,04).")
A(f"- **Implícito (ponderado):** {br(m_w.params.chuva,4)} p.p. por mm (IC {br(m_w.conf_int().loc['chuva'][0],4,True)} a {br(m_w.conf_int().loc['chuva'][1],4)}); com controle de porte, {br(m_cw.params.chuva,4)}.")
A(f"- **Regressão observado sobre estimado** (ideal = inclinação 1): sem peso {br(oe.params.efeito_abst_pp_mid,2)} (IC {br(oe.conf_int().loc['efeito_abst_pp_mid'][0],2)} a {br(oe.conf_int().loc['efeito_abst_pp_mid'][1],2)}); ponderado {br(oew.params.efeito_abst_pp_mid,2)} (IC {br(oew.conf_int().loc['efeito_abst_pp_mid'][0],2,True)} a {br(oew.conf_int().loc['efeito_abst_pp_mid'][1],2)}). Para o efeito por classe do Bot 4: {br(ob4.params.efeito_abstencao_pp_mid,2)} sem peso e {br(ob4w.params.efeito_abstencao_pp_mid,2)} ponderado. Correlação estimado x observado: {br(corr_e,2)}.")
A("")
A("![Chuva x variação descontada](grafico_chuva_vs_variacao.png)")
A("")
A("![Estimado x observado](grafico_estimado_vs_observado.png)")
A("")
A("## 6. Cidades em destaque")
A("")
def ficha(r):
    est=f"{br(r.efeito_abst_pp_mid,2,True)} p.p. ({br(r.efeito_abst_pp_lo,2)} a {br(r.efeito_abst_pp_hi,2)}), {bi(r.ia_extras_mid)} abstenções extras"
    A(f"### {r.municipio_nome} ({r.uf})")
    A("")
    tab(["Indicador","Valor"],[
      ("Aptos 2º turno",bi(r.aptos_2t)),("Abstenção 1T → 2T",f"{br(r.pct_abst_1t)}% → {br(r.pct_abst_2t)}% ({br(r.var_pp,2,True)} p.p.)"),
      ("Variação da UF",f"{br(r.var_uf_pp,2,True)} p.p."),("Variação descontada a média da UF",f"{br(r.var_desc_uf_pp,2,True)} p.p. ({bi(r.abst_acima_media_uf_eleitores,True)} eleitores)"),
      ("Chuva 08-17h (modelo / usada)",f"{br(r.chuva,1)} mm / {br(r.precip_usado_mm,1)} mm"),("Nível de risco (só previsão → final)",f"{r.nivel_risco_so_previsao} → {r.nivel_risco}"),
      ("Ajuste por notícias",("sim, nível "+str(r.ajuste_nivel)+", confiança "+str(r.ajuste_confianca)) if r.ajuste_noticias=="sim" else "não"),
      ("Efeito estimado (projeto)",est),("Efeito por classe Bot 4 (mid)",f"{br(r.efeito_abstencao_pp_mid,2,True)} p.p."),
      ("Observado menos estimado",f"{br(r.var_desc_uf_pp-r.efeito_abst_pp_mid,2,True)} p.p."),
      ("2º turno (votos válidos)",f"Flávio {br(r.pct_flavio_2t)}% ({bi(r.votos_flavio_2t)}) · Lula {br(r.pct_lula_2t)}% ({bi(r.votos_lula_2t)})"),
      ("1º turno (Flávio / Lula)",f"{br(r.pct_flavio_1t)}% / {br(r.pct_lula_1t)}%")])
    if r.ajuste_noticias=="sim":
        a=aj[(aj.codigo_ibge==r.codigo_ibge)&(aj.status=="ativo")]
        if len(a):
            ev=str(a.iloc[-1].evidencia).replace("—","-").replace("|"," ")
            A(f"*Evidência registrada (ajustes_impacto_noticias.csv, {a.iloc[-1].timestamp_brt}):* {ev[:400]}{'...' if len(ev)>400 else ''}")
            A("")
foco=[3550308,3304557,3518800,3509502,3106200,4106902]
for c in foco: ficha(d[d.codigo_ibge==c].iloc[0])
A("### Municípios com ajuste por notícias (9)")
A("")
aa=d[d.ajuste_noticias=="sim"].sort_values("aptos_2t",ascending=False)
tab(["Município","UF","Aptos","Confiança","Chuva modelo / usada (mm)","Estimado (p.p.)","Observado descontado (p.p.)","Abst. extras estimadas","Abst. acima da média da UF"],
    [(r.municipio_nome,r.uf,bi(r.aptos_2t),r.ajuste_confianca,f"{br(r.chuva,1)} / {br(r.precip_usado_mm,1)}",br(r.efeito_abst_pp_mid,2,True),br(r.var_desc_uf_pp,2,True),bi(r.ia_extras_mid),bi(r.abst_acima_media_uf_eleitores,True)) for _,r in aa.iterrows()])
for _,r in aa.iterrows():
    if r.codigo_ibge not in foco: ficha(r)
pos=(aa.var_desc_uf_pp>0).sum()
A(f"Resumo dos ajustes: {pos} de 9 municípios ajustados tiveram abstenção acima da média do seu estado; estimado somado {bi(aa.ia_extras_mid.sum())} abstenções extras, observado acima da média da UF somado {bi(aa.abst_acima_media_uf_eleitores.sum(),True)} (Belo Horizonte puxa para baixo).")
A("")
A("## 7. Municípios com 30 mm ou mais")
A("")
t=d[d.chuva>=30].sort_values("chuva",ascending=False)
tab(["Município","UF","Aptos","Chuva (mm)","Variação (p.p.)","Var. descontada (p.p.)","Estimado (p.p.)","Observado menos estimado"],
    [(r.municipio_nome,r.uf,bi(r.aptos_2t),br(r.chuva,1),br(r.var_pp,2,True),br(r.var_desc_uf_pp,2,True),br(r.efeito_abst_pp_mid,2,True),br(r.var_desc_uf_pp-r.efeito_abst_pp_mid,2,True)) for _,r in t.iterrows()])
A(f"{len(t)} municípios; {(t.var_desc_uf_pp>0).sum()} tiveram abstenção acima da média da UF, mas em todos o observado ficou abaixo do estimado (média observada {br(t.var_desc_uf_pp.mean(),2,True)} p.p. contra estimado {br(t.efeito_abst_pp_mid.mean(),2,True)} p.p.).")
A("")
A("## 8. Maiores erros (observado descontado menos estimado, p.p.)")
A("")
d["erro"]=d.var_desc_uf_pp-d.efeito_abst_pp_mid
for tit,x in [("Observado muito ABAIXO do estimado (o modelo superestimou)",d.nsmallest(10,"erro")),("Observado muito ACIMA do estimado (o modelo subestimou)",d.nlargest(10,"erro"))]:
    A(f"**{tit}**"); A("")
    tab(["Município","UF","Aptos","Chuva usada (mm)","Estimado","Observado descontado","Erro"],
        [(r.municipio_nome,r.uf,bi(r.aptos_2t),br(r.precip_usado_mm,1),br(r.efeito_abst_pp_mid,2,True),br(r.var_desc_uf_pp,2,True),br(r.erro,2,True)) for _,r in x.iterrows()])
lo10=d.nsmallest(10,"erro"); hi10=d.nlargest(10,"erro")
A(f"Entre os 10 casos em que o modelo mais superestimou, {(lo10.precip_usado_mm>=20).sum()} tinham 20 mm ou mais de chuva usada (erro ligado ao coeficiente alto); os demais ({', '.join(lo10[lo10.precip_usado_mm<20].municipio_nome)}) tiveram, com no máximo {br(lo10[lo10.precip_usado_mm<20].precip_usado_mm.max(),1)} mm, queda de abstenção bem maior que a do estado, o que aponta para fatores locais não ligados à chuva. Os 10 casos em que o modelo mais subestimou tinham no máximo {br(hi10.precip_usado_mm.max(),1)} mm de chuva usada: ali o desvio não vem da chuva modelada (exceções possíveis: Prudentópolis e Barracão, com relatos de problemas de acesso).")
A("")
A("## 9. O que isso sugere para o modelo")
A("")
A(f"1. **Direção confirmada, magnitude bem menor.** Mais chuva está associada a abstenção relativamente maior (sem peso, {br(m_s.params.chuva*10,2,True)} p.p. por 10 mm), mas o coeficiente implícito ({br(m_s.params.chuva,3)} p.p./mm) é cerca de um terço do usado (0,07) e fica abaixo da faixa do Bot 1 (0,04 a 0,10). Uma recalibração (sugestão para discussão) para algo em torno de 0,02 p.p./mm, com faixa de cerca de 0,01 a 0,03 (o IC sem peso), seria coerente com estes dados, com a ressalva de que é um único dia e uma medida indireta.")
A(f"2. **Efeito por classe do Bot 4 alto demais.** Na faixa de 15 a 30 mm o efeito por classe estimava cerca de +2 p.p.; o observado ponderado foi negativo. A classe 'a' (+2,0 p.p.) não se sustenta como efeito médio.")
A("3. **Grandes cidades dominam o total e divergem.** O resultado ponderado é instável: Rio de Janeiro (23,1 mm) ficou 1,46 p.p. abaixo da média do RJ e São Paulo (17,1 mm) 0,30 p.p. abaixo da média de SP, enquanto Guarulhos (15,3 mm) ficou 1,06 p.p. acima. O total nacional de abstenções extras fica muito sensível a poucas capitais.")
A("4. **Ajustes por notícias: resultado misto.** 6 de 9 municípios ajustados ficaram acima da média da UF (maiores desvios: Prudentópolis +2,00 p.p., Barracão +1,54, Itapevi +0,77); Belo Horizonte (-0,45), São Domingos (-1,04, apesar da transferência de 621 eleitores) e Águas de Chapecó (-0,78) ficaram abaixo. Em Barracão a evidência registrada se refere a um temporal de 23/10, não ao dia da eleição. Com n = 9, não dá para concluir que os ajustes melhoraram a estimativa; em todos, exceto Prudentópolis e Barracão, o estimado ficou acima do observado.")
A("5. **Para o próximo uso:** reduzir o coeficiente, aplicar o efeito só acima de um limiar de chuva, e validar com uma referência de comparecimento esperado melhor que o 1º turno (ex.: 2º turno de 2022 por município, ou controle por disputas estaduais).")
A("")
A("## 10. Limitações")
A("")
A("- A variação 1T→2T não é a abstenção causada pela chuva; descontar a média da UF não controla disputas locais, segundo turno estadual, perfil de renda nem mobilização.")
A(f"- A média da UF inclui o próprio município; nas UFs dominadas pela capital (ex.: a capital tem {br(d[d.codigo_ibge==3550308].aptos_2t.iloc[0]/ufc.set_index("uf").loc["SP","aptos_2t"]*100,1)}% do eleitorado de SP e o Rio de Janeiro {br(d[d.codigo_ibge==3304557].aptos_2t.iloc[0]/ufc.set_index("uf").loc["RJ","aptos_2t"]*100,1)}% do RJ) isso puxa a variação descontada para zero.")
A("- Chuva é estimativa do modelo Open-Meteo (não pluviômetro), uma série por município, sem distribuição dentro da cidade.")
A("- Os 304 municípios não são uma amostra aleatória (maiores colégios + ajustes); os resultados não valem para municípios pequenos.")
A("- Um único dia de eleição: muita incerteza; os intervalos de confiança assumem independência entre municípios, o que a chuva (espacialmente correlacionada) viola.")
A(f"- O eleitorado apto difere levemente entre os turnos (soma dos cobertos: {bi(d.aptos_1t.sum())} no 1T, {bi(d.aptos_2t.sum())} no 2T); as porcentagens usam o apto de cada turno.")
A("- O rascunho interno anterior (não publicado) trazia números um pouco diferentes (faixas com n = 95/80/82/40/7 e inclinação +0,285 p.p. por 10 mm). Este documento recalculou tudo a partir dos arquivos oficiais (abstenção do 1º turno do arquivo TSE e do 2º turno dos JSON por UF); as faixas aqui usam a chuva do snapshot final, e os números deste documento substituem os do rascunho.")
A("- Dois ajustes (Prudentópolis e Águas de Chapecó) têm registro às 17:15 no CSV de ajustes, mas já aparecem como ativos no snapshot de 17:09; o valor usado aqui é o do snapshot.")
A("")
A("## 11. Fontes")
A("")
A("- TSE, Divulgação de Resultados, eleição 6258 (2º turno, Presidente): https://resultados.tse.jus.br/oficial/ele2026/6258/dados/ (abstenção `<uf>/<uf>-e006258-ab.json` e resultado municipal `<uf>/<uf><código>-c0001-e006258-u.json`, totalização de 25/10/2026). Página pública: https://resultados.tse.jus.br")
A("- 1º turno (TSE): `data/tse/2026_1turno/abstencao_municipio.csv` e `abstencao_por_uf.csv` (origem em `README_origem.md`).")
A("- Estimativas finais (17:09 BRT): `data/impacto/atualizacoes/impacto_agora_latest.json` e `impacto_municipios_latest.csv`.")
A("- Ajustes por notícias: `data/ajustes/ajustes_impacto_noticias.csv`.")
A("- Repositório: https://github.com/andersonsoaresdev2025/chuva-abstencao-2turno-2026")
A("- Dados derivados deste documento: `comparacao_municipios_2turno.csv` (uma linha por município, 304 linhas), `resumo.json` (números-chave usados no site e no dashboard) e os arquivos brutos do TSE em `tse_2t/`.")
txt="\n".join(L).replace("—","-")
open("comparacao_municipios_2turno.md","w").write(txt)
print("ok", len(txt))

# ---------------- resumo.json (fonte única dos números do site e do dashboard)
def ci(m,v,esc=1.0):
    lo,hi=m.conf_int().loc[v]; return {"b":float(m.params[v]*esc),"lo":float(lo*esc),"hi":float(hi*esc),"p":float(m.pvalues[v]),"r2":float(m.rsquared)}
inc=[]
for nome,df in [("todos",d),("SP",d[d.uf=="SP"]),("PR",d[d.uf=="PR"])]:
    for lab,f in [("simples","var_desc_uf_pp ~ chuva"),("controle_porte","var_desc_uf_pp ~ chuva + log_aptos")]:
        for wl,w in [(False,None),(True,df.aptos_2t)]:
            inc.append({"amostra":nome,"n":int(len(df)),"modelo":lab,"ponderado":wl,**ci(fit(f,df,w),"chuva",10)})
faixas=[]
for f,x in d.groupby("faixa",observed=True):
    faixas.append({"faixa_mm":str(f),"n":int(len(x)),"aptos":int(x.aptos_2t.sum()),"chuva_media_mm":float(x.chuva.mean()),
      "variacao_media_pp":float(x.var_pp.mean()),"var_desc_media_simples_pp":float(x.var_desc_uf_pp.mean()),
      "var_desc_media_pond_pp":float(np.average(x.var_desc_uf_pp,weights=x.aptos_2t)),
      "efeito_estimado_pond_pp":float(np.average(x.efeito_abst_pp_mid,weights=x.aptos)),
      "efeito_classe_bot4_pond_pp":float(np.average(x.efeito_abstencao_pp_mid,weights=x.aptos)),
      "abst_extras_estimadas":int(round(x.ia_extras_mid.sum())),"abst_acima_media_uf":int(round(x.abst_acima_media_uf_eleitores.sum()))})
def mun(r):
    return {"codigo_ibge":int(r.codigo_ibge),"municipio":r.municipio_nome,"uf":r.uf,"aptos_2t":int(r.aptos_2t),
            "abst_pct_1t":float(r.pct_abst_1t),"abst_pct_2t":float(r.pct_abst_2t),"variacao_pp":float(r.var_pp),
            "variacao_uf_pp":float(r.var_uf_pp),"var_desc_uf_pp":float(r.var_desc_uf_pp),"chuva_mm":float(r.chuva),
            "chuva_usada_mm":float(r.precip_usado_mm),"ajuste_noticias":r.ajuste_noticias,
            "ajuste_confianca":None if pd.isna(r.ajuste_confianca) else str(r.ajuste_confianca),
            "estimado_pp":float(r.efeito_abst_pp_mid),"abst_extras_estimadas":int(round(r.ia_extras_mid)),
            "abst_acima_media_uf":int(round(r.abst_acima_media_uf_eleitores))}
caps=[3550308,3304557,3518800,3509502,3106200,4106902]
resumo={
 "gerado_por":"scripts/pos_eleicao/gerar.py","fonte_2t":"TSE, eleição 6258, totalização final 25/10/2026",
 "snapshot_estimativa":snap.get("gerado_em_brt"),"n_municipios":int(len(d)),"aptos_cobertos_2t":int(d.aptos_2t.sum()),
 "pct_eleitorado_coberto":float(d.aptos_2t.sum()/apt2*100),
 "abst_nacional_pct_1t":float(ab1/apt1*100),"abst_nacional_pct_2t":float(ab2/apt2*100),
 "abst_cobertos_pct_1t":float(cov1),"abst_cobertos_pct_2t":float(cov2),
 "estimativa_abst_nacional_pp":rn["abstencao_nacional_pp"],"estimativa_abst_extras":rn["abstencoes_extras"],
 "soma_abst_acima_media_uf":int(round(d.abst_acima_media_uf_eleitores.sum())),
 "inclinacoes_pp_por_10mm":inc,
 "coef_bot1_pp_por_mm":0.07,"coef_implicito_simples":ci(m_s,"chuva"),"coef_implicito_ponderado":ci(m_w,"chuva"),
 "coef_implicito_ponderado_porte":ci(m_cw,"chuva"),
 "obs_sobre_estimado_simples":ci(oe,"efeito_abst_pp_mid"),"obs_sobre_estimado_ponderado":ci(oew,"efeito_abst_pp_mid"),
 "corr_chuva_var_desc":float(corr_ch),"corr_estimado_observado":float(corr_e),
 "faixas_chuva":faixas,
 "capitais_destaque":[mun(d[d.codigo_ibge==c].iloc[0]) for c in caps],
 "ajustados":[mun(r) for _,r in d[d.ajuste_noticias=="sim"].sort_values("aptos_2t",ascending=False).iterrows()],
 "chuva_30mm_ou_mais":[mun(r) for _,r in d[d.chuva>=30].sort_values("chuva",ascending=False).iterrows()],
}
json.dump(resumo,open("resumo.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("resumo.json ok")
