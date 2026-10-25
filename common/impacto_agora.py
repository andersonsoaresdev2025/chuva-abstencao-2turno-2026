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
"""
from __future__ import annotations

import json
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

from common import dados as D

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
    return df.drop(columns="_k").reset_index(drop=True)


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
             erro_api: str | None = None) -> dict:
    """Calcula o impacto. `series` = saída de buscar_open_meteo (None -> fallback CSV)."""
    agora = agora or D.agora_utc()
    decorridas, modo = horas_decorridas(agora)
    janela = 9.0 if modo == "projecao" else decorridas
    cid = cidades_cobertas()
    nac = base_nacional()
    if cid.empty:
        raise RuntimeError("dados de municípios cobertos indisponíveis")

    usar_api = series is not None and len(series) == len(cid)
    if usar_api:
        mm = [acumulado_open_meteo(s, janela) for s in series]
        fonte = FONTE_OBS_PROJ if modo == "projecao" else FONTE_OBS
    else:
        mm = [acumulado_fallback(r, janela) for _, r in cid.iterrows()]
        fonte = FONTE_FALLBACK
    cid = cid.assign(precip_acum_mm=[round(x, 2) for x in mm])

    F0, L0 = nac["votos_flavio"], nac["votos_lula"]
    s0 = F0 / (F0 + L0)
    res = {}
    for k, c in COEF_PP_POR_MM.items():
        dabs = cid["precip_acum_mm"] * c  # p.p. de abstenção
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

    aptos_cob = float(cid["aptos"].sum())
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
        "n_municipios_cobertos": int(len(cid)),
        "aptos_cobertos": int(aptos_cob),
        "aptos_nacional": int(nac["aptos"]),
        "base_flavio_pct_2cand": s0 * 100,
        "municipios": cid[["municipio", "uf", "aptos", "pct_flavio_1t", "pct_lula_1t", "precip_acum_mm",
                           "efeito_abst_pp_lo", "efeito_abst_pp_mid", "efeito_abst_pp_hi",
                           "abst_extras_mid"]],
        "coeficiente": COEF_PP_POR_MM,
        "fontes": [COEF_FONTE, "Divisão por candidato: suposição do Bot 4 (proporcional à base de votos do 1º turno)",
                   nac["fonte"], fonte],
    }


def calcular_com_api(agora: datetime | None = None, buscar=None) -> dict:
    """Tenta Open-Meteo; em qualquer falha usa o fallback do CSV."""
    buscar = buscar or buscar_open_meteo
    cid = cidades_cobertas()
    try:
        series = buscar(cid["lat"].tolist(), cid["lon"].tolist())
        return calcular(agora, series=series)
    except Exception as e:  # noqa: BLE001
        return calcular(agora, series=None, erro_api=f"{type(e).__name__}: {e}"[:200])


METODO_TXT = (
    "Para cada um dos 15 maiores colégios com previsão horária, somamos a chuva desde 08h até agora "
    "(Open-Meteo; se a API falhar, a previsão do Bot 0 pró-rata pelas horas decorridas) e aplicamos o "
    "coeficiente do Bot 1: +0,7 p.p. de abstenção por cm de chuva (faixa 0,4–1,0). As abstenções extras "
    "(aptos × efeito) são divididas entre Flávio e Lula pela votação de cada um no município no 1º turno "
    "(mesma suposição do Bot 4), e o resultado é comparado com os votos nacionais dos dois no 1º turno. "
    "Municípios fora da cobertura contam como zero. Antes das 08h mostramos a projeção do dia; após 17h, "
    "a estimativa final."
)
DISCLAIMER = ("Estimativa baseada em modelo — **não** é contagem de votos, apuração nem pesquisa de boca de urna. "
              "Mostra apenas o efeito estimado da chuva, com grande incerteza.")
