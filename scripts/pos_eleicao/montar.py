"""Pós-eleição, passo 1: junta TSE 1º turno, TSE 2º turno (tse_2t/) e as estimativas finais de 17:09 BRT."""
import json, glob, os
import pandas as pd, numpy as np
from pathlib import Path as _P
import os as _os
ROOT=_P(__file__).resolve().parents[2]
OUT=ROOT/"data"/"resultado_2turno"
_os.chdir(OUT)  # entradas em tse_2t/, saídas nesta pasta
REPO=str(ROOT/"data")
def fl(x): return float(str(x).replace(",", "."))
# 2T abstention per municipality (ab_<uf>.json)
rows=[]
for f in glob.glob("tse_2t/ab_??.json"):
    uf=os.path.basename(f)[3:5].upper()
    for a in json.load(open(f))["abr"]:
        if a.get("tpabr")!="mun": continue
        e=a["e"]; rows.append({"uf":uf,"cd_tse":int(a["cdabr"]),"aptos_2t":int(e["te"]),"comp_2t":int(e["c"]),"abst_2t":int(e["a"]),"pct_abst_2t_tse":fl(e["pan"]),"secoes_pct_2t":fl(a["s"]["pstn"])})
ab2=pd.DataFrame(rows)
# UF 2T
ufr=[]
for a in json.load(open("tse_2t/ab_2t.json"))["abr"]:
    e=a["e"]; ufr.append({"uf":a["cdabr"].upper(),"tp":a["tpabr"],"aptos_2t":int(e["te"]),"abst_2t":int(e["a"])})
uf2=pd.DataFrame(ufr)
uf1=pd.read_csv(f"{REPO}/tse/2026_1turno/abstencao_por_uf.csv",encoding="utf-8-sig")[["SG_UF","QT_ELEITOR_ELEICAO_FEDERAL","ABSTENCAO"]].rename(columns={"SG_UF":"uf","QT_ELEITOR_ELEICAO_FEDERAL":"aptos_1t","ABSTENCAO":"abst_1t"})
ufc=uf1.merge(uf2[uf2.tp=="uf"],on="uf",how="outer")
ufc["pct_1t"]=ufc.abst_1t/ufc.aptos_1t*100; ufc["pct_2t"]=ufc.abst_2t/ufc.aptos_2t*100; ufc["var_uf_pp"]=ufc.pct_2t-ufc.pct_1t
ufc.to_csv("uf_variacao.csv",index=False)
print(uf2.tp.unique(), len(ufc), ufc[ufc.pct_2t.isna()|ufc.pct_1t.isna()])
# 1T municipal
m1=pd.read_csv(f"{REPO}/tse/2026_1turno/abstencao_municipio.csv",encoding="utf-8-sig")[["SG_UF","CD_MUNICIPIO","NM_MUNICIPIO","APTOS_2026","ABSTENCAO_2026","PCT_ABSTENCAO_2026"]]
m1.columns=["uf","cd_tse","nm_tse","aptos_1t","abst_1t","pct_abst_1t_tse"]
# estimates
est=pd.read_csv(f"{REPO}/impacto/atualizacoes/impacto_municipios_latest.csv")
snap=json.load(open(f"{REPO}/impacto/atualizacoes/impacto_agora_latest.json"))
lst=pd.DataFrame(snap["previsao_mais_noticias"]["municipios_lista"])
lst0=pd.DataFrame(snap["previsao"]["municipios_lista"])[["codigo_ibge","efeito_abst_pp_mid","abst_extras_mid"]].rename(columns={"efeito_abst_pp_mid":"ia_so_prev_mid","abst_extras_mid":"ia_so_prev_extras"})
d=est.merge(lst[["codigo_ibge","precip_acum_mm","precip_ajuste_mm","precip_usado_mm","efeito_abst_pp_lo","efeito_abst_pp_mid","efeito_abst_pp_hi","abst_extras_mid"]].rename(columns={"abst_extras_mid":"ia_extras_mid"}),on="codigo_ibge",how="left").merge(lst0,on="codigo_ibge",how="left")
d=d.merge(m1,on=["uf","cd_tse"],how="left").merge(ab2,on=["uf","cd_tse"],how="left")
# 2T candidate results
def cand(uf,cd):
    j=json.load(open(f"tse_2t/municipios/{uf.lower()}{cd:05d}-c0001-e006258-u.json"))
    out={"te_u":int(j["e"]["te"]),"a_u":int(j["e"]["a"]),"totalizacao_2t":f"{j['dt']} {j['ht']}"}
    for ag in j["carg"][0]["agr"]:
        for p in ag["par"]:
            for c in p["cand"]:
                k="flavio" if c["n"]=="22" else "lula" if c["n"]=="13" else c["n"]
                out[f"votos_{k}_2t"]=int(c["vap"]); out[f"pct_{k}_2t"]=fl(c["pvapn"])
    return out
c=pd.DataFrame([cand(u,int(k)) for u,k in zip(d.uf,d.cd_tse)])
d=pd.concat([d.reset_index(drop=True),c],axis=1)
assert (d.te_u==d.aptos_2t).all() and (d.a_u==d.abst_2t).all(), "u.json vs ab mismatch"
d["pct_abst_1t"]=d.abst_1t/d.aptos_1t*100
d["pct_abst_2t"]=d.abst_2t/d.aptos_2t*100
d["var_pp"]=d.pct_abst_2t-d.pct_abst_1t
d=d.merge(ufc[["uf","var_uf_pp","pct_1t","pct_2t"]].rename(columns={"pct_1t":"uf_pct_1t","pct_2t":"uf_pct_2t"}),on="uf",how="left")
d["var_desc_uf_pp"]=d.var_pp-d.var_uf_pp
d["abst_acima_media_uf_eleitores"]=(d.var_desc_uf_pp*d.aptos_2t/100).round(0)
d["ia_extras_lo"]=(d.aptos*d.efeito_abst_pp_lo/100).round(0); d["ia_extras_hi"]=(d.aptos*d.efeito_abst_pp_hi/100).round(0)
print("missing:",d[["abst_1t","abst_2t","var_uf_pp","precip_acum_mm"]].isna().sum().to_dict(), len(d))
print("diff pct1t repo vs tse max", (d.pct_abst_1t-d.pct_abstencao_1t).abs().max(), "precip window vs acum max",(d.precip_janela_votacao_08_17_mm-d.precip_acum_mm).abs().max())
d.to_pickle(".base_cache.pkl")
