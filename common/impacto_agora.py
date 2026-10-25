"""
"Impacto estimado agora" – efeito da chuva acumulada na janela de votação (08h–17h BRT)
sobre cada candidato, em pontos percentuais (p.p.), com faixa lo/mid/hi.

Método (nenhum coeficiente novo; tudo vem dos arquivos dos Bots 0–4):
1. Precipitação acumulada desde 08h até o instante do cálculo, por município coberto
   (15 maiores colégios com coordenadas em previsao_maiores_cidades*.csv):
   - fonte preferida: Open-Meteo /v1/forecast, hourly=precipitation, timezone America/Sao_Paulo
     (para horas já decorridas o valor é a melhor estimativa do modelo/nowcast horário, não pluviômetro).
     Convenção Open-Meteo: o valor rotulado HH:00 é o acumulado da hora anterior; portanto 08h–17h =
     rótulos 09:00..17:00. A hora em curso entra pró-rata pelos minutos já decorridos.
   - fallback: previsão do Bot 0 (CSV) – manhã (08–12h) e tarde (12–17h) pró-rata pelas horas decorridas.
2. Efeito na abstenção (p.p.) = coeficiente Bot 1 × mm acumulados. Bot 1 recomenda para simulações
   +0,7 p.p. por cm (faixa 0,4–1,0 p.p./cm) = 0,07 p.p./mm (0,04–0,10).
3. Abstenções extras = aptos × Δabst/100; divididas entre candidatos pela participação de cada um nos
   votos válidos do 1º turno no município (mesma suposição do Bot 4: efeito proporcional à base de votos).
4. Nacional: base = votos de Flávio e Lula no 1º turno em todo o país (TSE, todos os municípios + exterior).
   Δ participação de cada candidato nos votos válidos dos dois candidatos (p.p.) e efeito na margem
   (Lula − Flávio). Municípios não cobertos contribuem zero.
Antes das 08h: projeção do dia inteiro; após 17h: estimativa final do dia (congelada na janela completa).

Atualização automática (a cada 30 min): quando existe data/clima/atualizacoes/precip_horaria_latest.csv
(gravado por scripts/atualizar_clima.py), a cobertura passa dos 15 maiores colégios para todos os municípios
desse arquivo (~300 maiores colégios + lista do Bot 2), sem chamar a API a cada visita.
Ajustes por notícias (data/ajustes/ajustes_impacto_noticias.csv, status=ativo): a chuva usada no município é
max(chuva do modelo, intensidade_estimada_mm do ajuste, no mínimo o piso da classe: a=20 mm, b=5 mm).
Municípios ajustados fora da cobertura entram com os votos do 1º turno (TSE via redutos_municipios.csv).
O resultado é calculado duas vezes: só previsão e previsão + notícias (calcular_duplo).
"""
from __future__ import annotations

import json
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

from common import dados as D
from common import regras as R

DIA_ELEICAO = date(2026, 10, 25)
HORA_INI, HORA_FIM = 8, 17
# Bot 1 (data/correlacao/coeficientes_e_resultados.md §3): +0,7 pp/cm (0,4–1,0) -> pp/mm
COEF_PP_POR_MM = {"lo": 0.04, "mid": 0.07, "hi": 0.10}
COEF_FONTE = ("Bot 1 – coeficiente central para simulações: +0,7 p.p. de abstenção por cm de chuva "
              "(faixa 0,4–1,0 p.p./cm); data/correlacao/coeficientes_e_resultados.md §3")
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

FONTE_OBS = "Open-Meteo (horas já decorridas: estimativa horária do modelo/nowcast, não pluviômetro)"
FONTE_OBS_PROJ = "Open-Meteo (previsão horária atual para 08h–17h)"
FONTE_FALLBACK = ("Previsão Bot 0 (CSV, coletada ~09:01) pró-rata pelas horas decorridas "
                  "– fallback: API Open-Meteo indisponível")


def cidades_cobertas() -> pd.DataFrame:
    """Municípios com coordenadas + aptos/votos do 1º turno (impacto_municipios.csv do Bot 4)."""
    prev = D.read_csv(D.CLIMA_DIR / "previsao_maiores_cidades_com_risco.csv")
    if prev.empty:
        prev = D.read_csv(D.CLIMA_DIR / "previsao_maiores_cidades.csv")
    imp = D.read_csv(D.IMPACTO_DIR / "impacto_municipios.csv")
    if prev.empty or imp.empty:
        return pd.DataFrame()
    prev = prev.assign(_k=prev["municipio"].map(D.norm))
    imp = imp.assign(_k=imp["municipio"].map(D.norm))
    cols_imp = ["_k", "uf", "aptos", "pct_flavio_1t", "pct_lula_1t"]
    df = prev.merge(imp[cols_imp], on="_k", how="inner")
    red = D.read_csv(D.REDUTOS_DIR / "redutos_municipios.csv")
    if not red.empty:
        red = red[red["cd_ibge"].notna()].assign(_k=red["municipio"].map(D.norm))
        df = df.merge(red[["_k", "uf", "cd_ibge"]], on=["_k", "uf"], how="left")
        df["codigo_ibge"] = df.pop("cd_ibge").astype("Int64")
    return df.drop(columns="_k").reset_index(drop=True)


def cobertura_horaria() -> tuple[pd.DataFrame, list[dict], str | None]:
    """Cobertura ampliada a partir do arquivo horário da atualização automática.
    Retorna (municípios com aptos/% do 1º turno, séries {rótulo: mm}, obtido_em_utc) ou (vazio, [], None)."""
    hz = D.read_csv(D.ATUAL_CLIMA_DIR / "precip_horaria_latest.csv")
    red = D.read_csv(D.REDUTOS_DIR / "redutos_municipios.csv")
    if hz.empty or red.empty:
        return pd.DataFrame(), [], None
    red = red[red["cd_ibge"].notna()].assign(codigo_ibge=lambda x: x["cd_ibge"].astype(int))
    hz["codigo_ibge"] = hz["codigo_ibge"].astype(int)
    df = hz.drop(columns=["aptos"], errors="ignore").merge(
        red[["codigo_ibge", "aptos", "pct_flavio", "pct_lula"]].rename(
            columns={"pct_flavio": "pct_flavio_1t", "pct_lula": "pct_lula_1t"}), on="codigo_ibge", how="inner")
    hcols = [c for c in df.columns if len(c) == 3 and c.startswith("h") and c[1:].isdigit()]
    series = [{int(c[1:]): float(r[c]) for c in hcols} for _, r in df.iterrows()]
    obtido = str(df["obtido_em_utc"].dropna().astype(str).max()) if "obtido_em_utc" in df.columns else None
    cid = df[["codigo_ibge", "municipio", "uf", "lat", "lon", "aptos", "pct_flavio_1t", "pct_lula_1t"]].reset_index(drop=True)
    return cid, series, obtido


def _aplicar_ajustes(cid: pd.DataFrame, ajustes: pd.DataFrame | None) -> pd.DataFrame:
    """precip_usado_mm = max(modelo, ajuste). Ajustes fora da cobertura entram com votos TSE do 1º turno."""
    cid = cid.copy()
    cid["precip_ajuste_mm"] = float("nan")
    cid["ajuste_noticias"] = "não"
    cid["ajuste_fontes"] = ""
    cid["ajuste_confianca"] = ""
    if ajustes is not None and not ajustes.empty:
        red = D.read_csv(D.REDUTOS_DIR / "redutos_municipios.csv")
        red = red[red["cd_ibge"].notna()].assign(codigo_ibge=lambda x: x["cd_ibge"].astype(int))
        if "codigo_ibge" not in cid.columns:
            cid["codigo_ibge"] = pd.NA
        cods = set(pd.to_numeric(cid["codigo_ibge"], errors="coerce").dropna().astype(int))
        novos = []
        for _, a in ajustes.iterrows():
            c = int(a["codigo_ibge"])
            info = {"precip_ajuste_mm": float(a["mm_ajuste"]), "ajuste_noticias": "sim",
                    "ajuste_fontes": str(a.get("fontes") or ""), "ajuste_confianca": str(a.get("confianca") or "")}
            if c in cods:
                idx = cid.index[pd.to_numeric(cid["codigo_ibge"], errors="coerce") == c]
                for k, v in info.items():
                    cid.loc[idx, k] = v
            else:
                rr = red[red["codigo_ibge"] == c]
                if rr.empty:
                    continue  # fora dos dados TSE do 1º turno: não entra
                r0 = rr.iloc[0]
                novos.append({"codigo_ibge": c, "municipio": a.get("municipio") or str(r0["municipio"]).title(),
                              "uf": r0["uf"], "aptos": float(r0["aptos"]), "pct_flavio_1t": float(r0["pct_flavio"]),
                              "pct_lula_1t": float(r0["pct_lula"]), "precip_acum_mm": 0.0, **info})
        if novos:
            cid = pd.concat([cid, pd.DataFrame(novos)], ignore_index=True)
    cid["precip_usado_mm"] = cid[["precip_acum_mm", "precip_ajuste_mm"]].max(axis=1, skipna=True).round(2)
    return cid


def base_nacional() -> dict:
    r = D.read_csv(D.REDUTOS_DIR / "redutos_municipios.csv")
    return {
        "aptos": float(r["aptos"].sum()),
        "votos_flavio": float(r["votos_flavio"].sum()),
        "votos_lula": float(r["votos_lula"].sum()),
        "fonte": "TSE 1º turno 2026 via Bot 3 (data/redutos_1turno/redutos_municipios.csv, todos os municípios + exterior)",
    }


def buscar_open_meteo(lats: list[float], lons: list[float], dia: date = DIA_ELEICAO,
                      timeout: float = 15.0) -> list[dict[str, float]]:
    """Retorna, para cada coordenada, {rótulo 'HH' (int): mm} do dia. Levanta exceção em falha."""
    q = (f"{OPEN_METEO_URL}?latitude={','.join(str(x) for x in lats)}"
         f"&longitude={','.join(str(x) for x in lons)}&hourly=precipitation"
         f"&timezone=America%2FSao_Paulo&start_date={dia.isoformat()}&end_date={dia.isoformat()}")
    with urllib.request.urlopen(q, timeout=timeout) as resp:  # noqa: S310 (URL fixa, https)
        js = json.loads(resp.read().decode())
    if isinstance(js, dict):
        js = [js]
    if len(js) != len(lats):
        raise ValueError("resposta Open-Meteo com número de locais inesperado")
    out = []
    for loc in js:
        h = loc["hourly"]
        serie = {}
        for t, v in zip(h["time"], h["precipitation"]):
            if t.startswith(dia.isoformat()) and v is not None:
                serie[int(t[11:13])] = float(v)
        if len(serie) < 18:
            raise ValueError("série horária incompleta")
        out.append(serie)
    return out


def horas_decorridas(agora: datetime) -> tuple[float, str]:
    """Horas decorridas da janela 08–17h (0..9) e o modo (projecao / agora / final)."""
    loc = agora.astimezone(D.TZ_BRT)
    if loc.date() < DIA_ELEICAO:
        return 0.0, "projecao"
    if loc.date() > DIA_ELEICAO:
        return 9.0, "final"
    h = loc.hour + loc.minute / 60 + loc.second / 3600
    if h < HORA_INI:
        return 0.0, "projecao"
    if h >= HORA_FIM:
        return 9.0, "final"
    return h - HORA_INI, "agora"


def acumulado_open_meteo(serie: dict[int, float], decorridas: float) -> float:
    """mm entre 08:00 e 08:00+decorridas, com rótulos Open-Meteo (HH = hora anterior)."""
    total = 0.0
    completas = int(decorridas)
    for i in range(completas):
        total += serie.get(HORA_INI + i + 1, 0.0)
    frac = decorridas - completas
    if frac > 0:
        total += serie.get(HORA_INI + completas + 1, 0.0) * frac
    return total


def acumulado_fallback(row: pd.Series, decorridas: float) -> float:
    manha = float(row.get("precip_manha_08_12_mm", 0) or 0)
    tarde = float(row.get("precip_tarde_12_17_mm", 0) or 0)
    if decorridas <= 4:
        return manha * decorridas / 4
    return manha + tarde * min(decorridas - 4, 5) / 5


def calcular(agora: datetime | None = None, series: list[dict] | None = None,
             erro_api: str | None = None, cid: pd.DataFrame | None = None,
             ajustes: pd.DataFrame | None = None, fonte: str | None = None) -> dict:
    """Calcula o impacto. `series` = saída de buscar_open_meteo (None -> fallback CSV).
    `cid` = municípios cobertos (padrão: 15 maiores colégios); `ajustes` = ajustes por notícias ativos."""
    agora = agora or D.agora_utc()
    decorridas, modo = horas_decorridas(agora)
    janela = 9.0 if modo == "projecao" else decorridas
    cid = cidades_cobertas() if cid is None else cid
    nac = base_nacional()
    if cid.empty:
        raise RuntimeError("dados de municípios cobertos indisponíveis")

    usar_api = series is not None and len(series) == len(cid)
    if usar_api:
        mm = [acumulado_open_meteo(s, janela) for s in series]
        fonte = fonte or (FONTE_OBS_PROJ if modo == "projecao" else FONTE_OBS)
    else:
        mm = [acumulado_fallback(r, janela) for _, r in cid.iterrows()]
        fonte = FONTE_FALLBACK
    cid = cid.assign(precip_acum_mm=[round(x, 2) for x in mm])
    cid = _aplicar_ajustes(cid, ajustes)
    n_aj = int((cid["ajuste_noticias"] == "sim").sum())

    F0, L0 = nac["votos_flavio"], nac["votos_lula"]
    s0 = F0 / (F0 + L0)
    res = {}
    for k, c in COEF_PP_POR_MM.items():
        dabs = cid["precip_usado_mm"] * c  # p.p. de abstenção
        extra = cid["aptos"] * dabs / 100
        perde_f = extra * cid["pct_flavio_1t"] / 100
        perde_l = extra * cid["pct_lula_1t"] / 100
        F1, L1 = F0 - perde_f.sum(), L0 - perde_l.sum()
        s1 = F1 / (F1 + L1)
        d_f = (s1 - s0) * 100
        res[k] = {
            "abstencoes_extras": float(extra.sum()),
            "votos_perdidos_flavio": float(perde_f.sum()),
            "votos_perdidos_lula": float(perde_l.sum()),
            "pp_flavio": d_f, "pp_lula": -d_f, "pp_margem_lula_menos_flavio": -2 * d_f,
            "pp_abst_nacional": float(extra.sum() / nac["aptos"] * 100),
        }
        cid[f"efeito_abst_pp_{k}"] = dabs.round(3)
        cid[f"abst_extras_{k}"] = extra.round(0)

    def faixa(chave):
        vals = sorted(res[k][chave] for k in ("lo", "mid", "hi"))
        return {"mid": res["mid"][chave], "min": vals[0], "max": vals[-1]}

    n_cob = len(mm)  # municípios com chuva do modelo (ajustes extras são anexados depois)
    aptos_cob = float(cid["aptos"].iloc[:n_cob].sum())
    rotulo = {"projecao": "projeção (votação ainda não começou)",
              "agora": "estimativa agora (chuva acumulada desde 08h)",
              "final": "estimativa final do dia"}[modo]
    return {
        "modo": modo,
        "rotulo": rotulo,
        "horas_decorridas": round(janela, 2),
        "calculado_em_utc": agora.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "calculado_em_brt": agora.astimezone(D.TZ_BRT).strftime("%H:%M BRT"),
        "calculado_em": D.fmt_utc_brt(agora),
        "fonte_precipitacao": fonte,
        "usou_fallback": not usar_api,
        "erro_api": erro_api,
        "flavio_pp": faixa("pp_flavio"),
        "lula_pp": faixa("pp_lula"),
        "margem_lula_menos_flavio_pp": faixa("pp_margem_lula_menos_flavio"),
        "votos_perdidos_flavio": faixa("votos_perdidos_flavio"),
        "votos_perdidos_lula": faixa("votos_perdidos_lula"),
        "abstencoes_extras": faixa("abstencoes_extras"),
        "abstencao_nacional_pp": faixa("pp_abst_nacional"),
        "cobertura_pct_eleitorado": aptos_cob / nac["aptos"] * 100,
        "n_municipios_cobertos": int(n_cob),
        "n_municipios_extras_ajuste": int(len(cid) - n_cob),
        "aptos_cobertos": int(aptos_cob),
        "aptos_nacional": int(nac["aptos"]),
        "base_flavio_pct_2cand": s0 * 100,
        "n_ajustes_noticias": n_aj,
        "aptos_ajustados": int(cid.loc[cid["ajuste_noticias"] == "sim", "aptos"].sum()),
        "municipios": cid[[c for c in ["codigo_ibge"] if c in cid.columns] + ["municipio", "uf", "aptos", "pct_flavio_1t", "pct_lula_1t", "precip_acum_mm",
                           "precip_ajuste_mm", "precip_usado_mm", "ajuste_noticias", "ajuste_confianca",
                           "ajuste_fontes", "efeito_abst_pp_lo", "efeito_abst_pp_mid", "efeito_abst_pp_hi",
                           "abst_extras_mid"]],
        "coeficiente": COEF_PP_POR_MM,
        "fontes": [COEF_FONTE, "Divisão por candidato: suposição do Bot 4 (proporcional à base de votos do 1º turno)",
                   nac["fonte"], fonte],
    }


def calcular_com_api(agora: datetime | None = None, buscar=None, ajustes="auto",
                     usar_arquivo: bool = True) -> dict:
    """1) arquivo horário da atualização automática (cobertura ampliada, sem chamar a API);
    2) senão, API Open-Meteo para os 15 maiores colégios; 3) em qualquer falha, fallback do CSV do Bot 0.
    ajustes="auto" -> ajustes por notícias ativos; None -> só previsão."""
    if isinstance(ajustes, str) and ajustes == "auto":
        ajustes = D.carregar_ajustes()
    if usar_arquivo:
        cid, series, obtido = cobertura_horaria()
        if not cid.empty:
            try:
                ob = datetime.fromisoformat(obtido).astimezone(D.TZ_BRT).strftime("%H:%M BRT") if obtido else "?"
            except ValueError:
                ob = str(obtido)
            fonte = (f"Open-Meteo horário de {len(cid)} municípios (arquivo da atualização automática, obtido às {ob}; "
                     "horas decorridas = estimativa do modelo, não pluviômetro)")
            r = calcular(agora, series=series, cid=cid, ajustes=ajustes, fonte=fonte)
            r["precip_obtida_em_utc"] = obtido
            r["precip_obtida_em_brt"] = ob
            r["origem_cobertura"] = "arquivo_atualizacao"
            return r
    buscar = buscar or buscar_open_meteo
    cid = cidades_cobertas()
    try:
        series = buscar(cid["lat"].tolist(), cid["lon"].tolist())
        r = calcular(agora, series=series, ajustes=ajustes)
    except Exception as e:  # noqa: BLE001
        r = calcular(agora, series=None, erro_api=f"{type(e).__name__}: {e}"[:200], ajustes=ajustes)
    r["origem_cobertura"] = "15_maiores_colegios"
    return r


def calcular_duplo(agora: datetime | None = None, buscar=None, usar_arquivo: bool = True) -> dict:
    """Mesma conta duas vezes: só previsão vs previsão + ajustes por notícias."""
    aj = D.carregar_ajustes()
    so_prev = calcular_com_api(agora, buscar=buscar, ajustes=None, usar_arquivo=usar_arquivo)
    com_not = calcular_com_api(agora, buscar=buscar, ajustes=aj, usar_arquivo=usar_arquivo) if not aj.empty else so_prev
    return {"previsao": so_prev, "previsao_mais_noticias": com_not, "n_ajustes_ativos": int(len(aj))}


def resumo_json(r: dict) -> dict:
    """Versão serializável (sem DataFrame) de um resultado de calcular()."""
    out = {k: v for k, v in r.items() if k != "municipios"}
    mun = r["municipios"].copy()
    out["municipios_top"] = (mun.sort_values("abst_extras_mid", ascending=False).head(25)
                             .astype(object).where(mun.notna(), None).to_dict(orient="records"))
    return out


METODO_TXT = (
    "Para cada município coberto (≈300 maiores colégios do arquivo horário atualizado a cada 30 min; "
    "sem esse arquivo, os 15 maiores colégios), somamos a chuva desde 08h até agora "
    "(Open-Meteo; se a API falhar, a previsão do Bot 0 pró-rata pelas horas decorridas) e aplicamos o "
    "coeficiente do Bot 1: +0,7 p.p. de abstenção por cm de chuva (faixa 0,4–1,0). As abstenções extras "
    "(aptos × efeito) são divididas entre Flávio e Lula pela votação de cada um no município no 1º turno "
    "(mesma suposição do Bot 4), e o resultado é comparado com os votos nacionais dos dois no 1º turno. "
    "Municípios fora da cobertura contam como zero. Ajustes por notícias ativos elevam a chuva do município ao "
    "maior valor entre modelo e ajuste (versão 'previsão + notícias'). Antes das 08h mostramos a projeção do dia; "
    "após 17h, a estimativa final."
)
DISCLAIMER = ("Estimativa baseada em modelo — **não** é contagem de votos, apuração nem pesquisa de boca de urna. "
              "Mostra apenas o efeito estimado da chuva, com grande incerteza.")
