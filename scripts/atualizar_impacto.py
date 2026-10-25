#!/usr/bin/env python3
"""
Atualização automática do IMPACTO NA ABSTENÇÃO (executa o papel do Bot 4) – a cada 30 min.

Entrada: data/clima/atualizacoes/risco_chuva_municipios_latest.csv (scripts/atualizar_clima.py, já com o
piso dos ajustes por notícias) – se ausente, a classificação original do Bot 2.
Método = o mesmo do Bot 4 (data/impacto/): efeito por classe (a: +2,0 pp [1,2–3,0]; b: +0,85 [0,5–1,2];
c: +0,15 [0,0–0,4]), impacto relativo = efeito_mid × % do candidato no 1º turno do município,
"mais prejudicado" = maior base local no 1º turno. Votos do 1º turno: TSE via data/redutos_1turno/.
Estados: média ponderada por aptos dos municípios cobertos + restante do eleitorado da UF com o efeito do
nível predominante da UF; UFs sem município coberto mantêm o valor do Bot 4 (sinalizado). Regiões: média
ponderada por aptos das UFs.
Saídas em data/impacto/atualizacoes/: impacto_{municipios,estados,regioes}_latest.csv (+ versões com timestamp),
impacto_agora_latest.json (só previsão vs previsão + notícias) e impacto_agora_historico.csv.
Os arquivos originais do Bot 4 NÃO são alterados.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from common import dados as D  # noqa: E402
from common import impacto_agora as IA  # noqa: E402
from common import regras as R  # noqa: E402

UTC = timezone.utc


def _efeitos(df: pd.DataFrame, col_letra: str, suf: str = "") -> pd.DataFrame:
    e = df[col_letra].map(R.efeito)
    df[f"efeito_abstencao_pp_mid{suf}"] = e.map(lambda x: x[0])
    df[f"efeito_abstencao_pp_lo{suf}"] = e.map(lambda x: x[1])
    df[f"efeito_abstencao_pp_hi{suf}"] = e.map(lambda x: x[2])
    return df


def municipios(risco: pd.DataFrame, ts: str) -> pd.DataFrame:
    red = D.read_csv(D.REDUTOS_DIR / "redutos_municipios.csv")
    red = red[red["cd_ibge"].notna()].assign(codigo_ibge=lambda x: x["cd_ibge"].astype(int))
    r = risco.copy()
    r["codigo_ibge"] = r["codigo_ibge"].astype(int)
    keep = [c for c in ["codigo_ibge", "municipio", "regiao", "nivel_risco", "nivel_risco_previsao", "precipitacao_mm_estimada",
                        "precip_observada_mm", "precip_prevista_restante_mm", "precip_manha_08_12_mm",
                        "precip_tarde_12_17_mm", "precip_dia_mm", "probabilidade", "alerta_inmet", "ajuste_noticias",
                        "ajuste_nivel", "ajuste_confianca", "ajuste_fontes", "ajuste_evidencia", "status_dado",
                        "ultima_atualizacao"] if c in r.columns]
    r = r[keep].rename(columns={"municipio": "municipio_nome", "ultima_atualizacao": "ts_clima"})
    m = r.merge(red[["codigo_ibge", "uf", "cd_tse", "municipio", "aptos", "pct_abstencao", "pct_flavio", "pct_lula",
                     "vencedor", "peso_eleitoral_pct"]], on="codigo_ibge", how="inner")
    m = m.rename(columns={"pct_abstencao": "pct_abstencao_1t", "pct_flavio": "pct_flavio_1t", "pct_lula": "pct_lula_1t",
                          "vencedor": "vencedor_1t", "precipitacao_mm_estimada": "precip_janela_votacao_08_17_mm",
                          "precip_dia_mm": "precip_sum_mm", "probabilidade": "precip_prob_max_pct"})
    m["letra"] = m["nivel_risco"].map(R.letra).fillna("c")
    m["letra_prev"] = (m["nivel_risco_previsao"].map(R.letra) if "nivel_risco_previsao" in m.columns else m["letra"]).fillna(m["letra"])
    m["classe_risco_projeto"] = m["letra"].map(R.ROTULO_LETRA)
    m["nivel_risco"] = m["letra"].map(R.NIVEL_POR_LETRA)
    m["nivel_risco_so_previsao"] = m["letra_prev"].map(R.NIVEL_POR_LETRA)
    m = _efeitos(m, "letra")
    m = _efeitos(m, "letra_prev", "_so_previsao")
    m["impacto_relativo_flavio"] = (m["efeito_abstencao_pp_mid"] * m["pct_flavio_1t"] / 100).round(3)
    m["impacto_relativo_lula"] = (m["efeito_abstencao_pp_mid"] * m["pct_lula_1t"] / 100).round(3)
    m["mais_prejudicado"] = [R.mais_prejudicado(f, l) for f, l in zip(m["pct_flavio_1t"], m["pct_lula_1t"])]
    m["vulnerabilidade"] = m["letra"].map(R.vulnerabilidade)
    m["abstencoes_extras_mid"] = (m["aptos"] * m["efeito_abstencao_pp_mid"] / 100).round(0)
    m["votos_perdidos_flavio_mid"] = (m["abstencoes_extras_mid"] * m["pct_flavio_1t"] / 100).round(0)
    m["votos_perdidos_lula_mid"] = (m["abstencoes_extras_mid"] * m["pct_lula_1t"] / 100).round(0)
    m["fonte_clima"] = "data/clima/atualizacoes/risco_chuva_municipios_latest.csv (atualizar_clima.py)"
    m["fonte_coeficiente"] = R.FONTE_COEF
    m["timestamp_atualizacao"] = ts
    manha = D.read_csv(D.IMPACTO_DIR / "impacto_municipios.csv")
    if not manha.empty:
        mm = manha[["cd_tse", "nivel_risco", "efeito_abstencao_pp_mid"]].rename(
            columns={"nivel_risco": "nivel_risco_manha_bot4", "efeito_abstencao_pp_mid": "efeito_mid_manha_bot4"})
        m = m.merge(mm, on="cd_tse", how="left")
    cols = ["uf", "cd_tse", "codigo_ibge", "municipio", "municipio_nome", "regiao", "aptos", "pct_abstencao_1t",
            "pct_flavio_1t", "pct_lula_1t", "vencedor_1t", "peso_eleitoral_pct", "precip_sum_mm",
            "precip_janela_votacao_08_17_mm", "precip_observada_mm", "precip_prevista_restante_mm",
            "precip_manha_08_12_mm", "precip_tarde_12_17_mm", "precip_prob_max_pct", "alerta_inmet",
            "classe_risco_projeto", "nivel_risco", "efeito_abstencao_pp_mid", "efeito_abstencao_pp_lo",
            "efeito_abstencao_pp_hi", "impacto_relativo_flavio", "impacto_relativo_lula", "mais_prejudicado",
            "vulnerabilidade", "abstencoes_extras_mid", "votos_perdidos_flavio_mid", "votos_perdidos_lula_mid",
            "nivel_risco_so_previsao", "efeito_abstencao_pp_mid_so_previsao", "efeito_abstencao_pp_lo_so_previsao",
            "efeito_abstencao_pp_hi_so_previsao", "ajuste_noticias", "ajuste_nivel", "ajuste_confianca",
            "ajuste_fontes", "ajuste_evidencia", "nivel_risco_manha_bot4", "efeito_mid_manha_bot4", "status_dado",
            "fonte_clima", "fonte_coeficiente", "ts_clima", "timestamp_atualizacao"]
    for c in cols:
        if c not in m.columns:
            m[c] = pd.NA
    return m[cols].sort_values(["efeito_abstencao_pp_mid", "aptos"], ascending=False).reset_index(drop=True)


def estados(mun: pd.DataFrame, ts: str) -> pd.DataFrame:
    red_uf = D.read_csv(D.REDUTOS_DIR / "redutos_estados.csv")
    bot4 = D.read_csv(D.IMPACTO_DIR / "impacto_estados.csv")
    risco_uf = D.read_csv(D.ATUAL_CLIMA_DIR / "risco_chuva_estados_latest.csv")
    pred = dict(zip(risco_uf.get("uf", []), risco_uf.get("nivel_risco_predominante", [])))
    linhas = []
    for _, b in bot4.iterrows():
        uf = b["uf"]
        sub = mun[mun["uf"] == uf]
        row = b.to_dict()
        row["efeito_mid_manha_bot4"] = b["efeito_abstencao_pp_mid"]
        row["nivel_risco_manha_bot4"] = b["nivel_risco"]
        if sub.empty:
            row["observacao"] = "Sem município coberto pela atualização: mantido o valor do Bot 4 (manhã)."
            row["n_municipios_cobertos"] = 0
            row["pct_aptos_cobertos"] = 0.0
            row["status_dado"] = "original Bot 4"
        else:
            apt_uf = float(b["aptos"])
            apt_cob = float(sub["aptos"].sum())
            resto = max(apt_uf - apt_cob, 0.0)
            lp = R.letra(pred.get(uf)) or "c"
            e_resto = R.efeito(lp)
            for i, k in enumerate(("mid", "lo", "hi")):
                v = ((sub["aptos"] * sub[f"efeito_abstencao_pp_{k}"]).sum() + resto * e_resto[i]) / apt_uf
                row[f"efeito_abstencao_pp_{k}"] = round(float(v), 2)
            row["nivel_risco"] = R.NIVEL_POR_LETRA[lp]
            row["impacto_relativo_flavio"] = round(row["efeito_abstencao_pp_mid"] * b["pct_flavio_1t"] / 100, 3)
            row["impacto_relativo_lula"] = round(row["efeito_abstencao_pp_mid"] * b["pct_lula_1t"] / 100, 3)
            row["vulnerabilidade"] = ("Alta" if row["efeito_abstencao_pp_mid"] >= 1.2 else
                                      "Média" if row["efeito_abstencao_pp_mid"] >= 0.5 else "Baixa")
            row["n_municipios_cobertos"] = int(len(sub))
            row["pct_aptos_cobertos"] = round(apt_cob / apt_uf * 100, 1)
            n_aj = int((sub["ajuste_noticias"] == "sim").sum())
            row["observacao"] = (f"{len(sub)} municípios cobertos ({row['pct_aptos_cobertos']}% dos aptos); restante da UF "
                                 f"com o efeito do nível predominante ({lp})." + (f" {n_aj} com ajuste por notícias." if n_aj else ""))
            row["status_dado"] = "atualizado"
        row["mais_prejudicado"] = R.mais_prejudicado(b["pct_flavio_1t"], b["pct_lula_1t"]).replace(" local", "")
        row["fonte_coeficiente"] = R.FONTE_COEF
        row["timestamp_atualizacao"] = ts
        linhas.append(row)
    return pd.DataFrame(linhas).sort_values("aptos", ascending=False).reset_index(drop=True)


def regioes(uf: pd.DataFrame, ts: str) -> pd.DataFrame:
    bot4 = D.read_csv(D.IMPACTO_DIR / "impacto_regioes.csv")
    linhas = []
    for _, b in bot4.iterrows():
        sub = uf[uf["regiao"] == b["regiao"]]
        row = b.to_dict()
        row["efeito_mid_manha_bot4"] = b["efeito_abstencao_pp_mid"]
        if not sub.empty:
            w = sub["aptos"].astype(float)
            for k in ("mid", "lo", "hi"):
                row[f"efeito_abstencao_pp_{k}"] = round(float((w * sub[f"efeito_abstencao_pp_{k}"]).sum() / w.sum()), 2)
            # nível com maior eleitorado na região
            por_nivel = sub.groupby("nivel_risco")["aptos"].sum()
            row["nivel_risco"] = por_nivel.idxmax()
            if "impacto_relativo_flavio" in row and "pct_flavio_1t" in row:
                row["impacto_relativo_flavio"] = round(row["efeito_abstencao_pp_mid"] * row["pct_flavio_1t"] / 100, 3)
                row["impacto_relativo_lula"] = round(row["efeito_abstencao_pp_mid"] * row["pct_lula_1t"] / 100, 3)
            if "vulnerabilidade" in row:
                row["vulnerabilidade"] = ("Alta" if row["efeito_abstencao_pp_mid"] >= 1.2 else
                                          "Média" if row["efeito_abstencao_pp_mid"] >= 0.5 else "Baixa")
        row["timestamp_atualizacao"] = ts
        linhas.append(row)
    return pd.DataFrame(linhas)


def executar(agora: datetime | None = None) -> dict:
    agora = agora or datetime.now(UTC)
    od = D.ATUAL_IMPACTO_DIR
    od.mkdir(parents=True, exist_ok=True)
    ts = agora.astimezone(D.TZ_BRT).strftime("%Y-%m-%d %H:%M BRT")
    stamp = agora.astimezone(UTC).strftime("%Y%m%d_%H%MUTC")
    risco, origem = D.latest_ou_original(D.ATUAL_CLIMA_DIR / "risco_chuva_municipios_latest.csv",
                                         D.CLIMA_DIR / "risco_chuva_municipios.csv")
    if risco.empty:
        raise RuntimeError("sem classificação de risco (nem latest nem original)")
    mun = municipios(risco, ts)
    uf = estados(mun, ts)
    reg = regioes(uf, ts)
    for nome, df in (("municipios", mun), ("estados", uf), ("regioes", reg)):
        df.to_csv(od / f"impacto_{nome}_latest.csv", index=False)
        df.to_csv(od / f"impacto_{nome}_{stamp}.csv", index=False)

    duplo = IA.calcular_duplo(agora)
    snap = {
        "gerado_em_utc": agora.isoformat(), "gerado_em_brt": ts, "origem_risco": origem,
        "n_ajustes_ativos": duplo["n_ajustes_ativos"],
        "previsao": IA.resumo_json(duplo["previsao"]),
        "previsao_mais_noticias": IA.resumo_json(duplo["previsao_mais_noticias"]),
        "metodo": IA.METODO_TXT, "disclaimer": IA.DISCLAIMER,
    }
    (od / "impacto_agora_latest.json").write_text(json.dumps(snap, ensure_ascii=False, indent=1, default=float),
                                                  encoding="utf-8")
    hist = od / "impacto_agora_historico.csv"
    linha = {"gerado_em_brt": ts, "modo": duplo["previsao"]["modo"],
             "horas_decorridas": duplo["previsao"]["horas_decorridas"],
             "n_municipios": duplo["previsao"]["n_municipios_cobertos"],
             "cobertura_pct": round(duplo["previsao"]["cobertura_pct_eleitorado"], 2),
             "n_ajustes": duplo["n_ajustes_ativos"]}
    for k, r in (("prev", duplo["previsao"]), ("prev_noticias", duplo["previsao_mais_noticias"])):
        linha[f"flavio_pp_mid_{k}"] = round(float(r["flavio_pp"]["mid"]), 5)
        linha[f"margem_pp_mid_{k}"] = round(float(r["margem_lula_menos_flavio_pp"]["mid"]), 5)
        linha[f"abst_nacional_pp_mid_{k}"] = round(float(r["abstencao_nacional_pp"]["mid"]), 4)
        linha[f"votos_perdidos_flavio_mid_{k}"] = round(float(r["votos_perdidos_flavio"]["mid"]))
        linha[f"votos_perdidos_lula_mid_{k}"] = round(float(r["votos_perdidos_lula"]["mid"]))
    pd.DataFrame([linha]).to_csv(hist, mode="a", header=not hist.exists(), index=False)
    return {"municipios": mun, "estados": uf, "regioes": reg, "agora": snap}


def main():
    r = executar()
    m, a = r["municipios"], r["agora"]
    print(f"OK impacto: {len(m)} municípios · {int((m['vulnerabilidade'] == 'Alta').sum())} Alta · "
          f"agora ({a['previsao']['rotulo']}): Flávio {a['previsao']['flavio_pp']['mid']:+.4f} pp "
          f"(+notícias {a['previsao_mais_noticias']['flavio_pp']['mid']:+.4f}); "
          f"abstenção nacional +{a['previsao']['abstencao_nacional_pp']['mid']:.3f} pp; ajustes {a['n_ajustes_ativos']}")


if __name__ == "__main__":
    main()
