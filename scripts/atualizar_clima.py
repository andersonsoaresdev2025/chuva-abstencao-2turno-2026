#!/usr/bin/env python3
"""
Atualização automática do RISCO DE CHUVA (executa o papel do Bot 2) – a cada 30 min.

1. Universo: os 29 municípios do Bot 2 + os 300 maiores colégios (data/maiores_colegios.csv, TSE->IBGE
   via data/redutos_1turno/redutos_municipios.csv) + municípios com ajuste ATIVO em
   data/ajustes/ajustes_impacto_noticias.csv (se existirem nos dados TSE do 1º turno).
2. Precipitação horária Open-Meteo (/v1/forecast, timezone America/Sao_Paulo, past_days=0):
   horas já passadas = valores do modelo para as horas decorridas; restantes = previsão.
   Janela de votação 08h–17h = rótulos horários 09..17 (o valor da hora H acumula H-1 -> H).
3. Avisos INMET: https://apiprevmet3.inmet.gov.br/avisos/ativos (JSON com geocódigos IBGE);
   fallback RSS https://apiprevmet3.inmet.gov.br/avisos/rss (só lista, sem geocódigos);
   se nada responder: últimos avisos conhecidos (cache) ou marcações "ALERTA INMET" do Bot 2,
   sempre sinalizados como desatualizados.
4. Reclassificação a/b/c (common/regras.py) + piso dos ajustes por notícias (max(previsão, ajuste)).
5. Saídas em data/clima/atualizacoes/: risco_chuva_{municipios,estados,regioes}_latest.csv e versões
   com timestamp, precip_horaria_latest.csv, inmet_avisos_latest.json, status_latest.json, resumo_latest.md.
Os arquivos originais do Bot 2 (data/clima/previsoes_2026-10-25/) NÃO são alterados.
Nunca inventa dado: se uma fonte falha, mantém o último dado válido e marca status_dado=stale.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from common import dados as D  # noqa: E402
from common import regras as R  # noqa: E402

UTC = timezone.utc
DIA = "2026-10-25"
HORAS_JANELA = list(range(9, 18))  # rótulos 09..17 = 08h–17h
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
INMET_JSON = "https://apiprevmet3.inmet.gov.br/avisos/ativos"
INMET_RSS = "https://apiprevmet3.inmet.gov.br/avisos/rss"
UA = {"User-Agent": "chuva-abstencao-2026/1.0 (+https://github.com/andersonsoaresdev2025/chuva-abstencao-2turno-2026)"}
LOTE = 50


def out_dir() -> Path:
    return D.ATUAL_CLIMA_DIR


def fmt_brt(dt: datetime) -> str:
    return dt.astimezone(D.TZ_BRT).strftime("%Y-%m-%d %H:%M BRT")


# ---------------------------------------------------------------------------
# Universo de municípios
# ---------------------------------------------------------------------------
def universo(ajustes: pd.DataFrame) -> pd.DataFrame:
    red = D.read_csv(D.REDUTOS_DIR / "redutos_municipios.csv")
    red = red[red["cd_ibge"].notna()].copy()
    red["codigo_ibge"] = red["cd_ibge"].astype(int)
    bot2 = D.read_csv(D.CLIMA_DIR / "risco_chuva_municipios.csv")
    mc = D.read_csv(D.DATA / "maiores_colegios.csv")
    geo = D.read_csv(D.GEO_FILE)

    cods: dict[int, str] = {}
    for c in bot2.get("codigo_ibge", pd.Series(dtype=int)).dropna().astype(int):
        cods.setdefault(int(c), "bot2")
    if not mc.empty:
        m = mc.merge(red[["cd_tse", "codigo_ibge"]], left_on="CD_MUNICIPIO", right_on="cd_tse", how="inner")
        for c in m["codigo_ibge"]:
            cods.setdefault(int(c), "maiores_colegios")
    for c in ajustes.get("codigo_ibge", pd.Series(dtype=int)):
        if int(c) in set(red["codigo_ibge"]):
            cods.setdefault(int(c), "ajuste_noticias")

    u = pd.DataFrame({"codigo_ibge": list(cods), "origem_lista": list(cods.values())})
    u = u.merge(red[["codigo_ibge", "cd_tse", "uf", "municipio", "aptos"]].rename(columns={"municipio": "municipio_tse"}),
                on="codigo_ibge", how="left")
    if not geo.empty:
        u = u.merge(geo[["codigo_ibge", "nome", "latitude", "longitude"]], on="codigo_ibge", how="left")
    else:
        u["nome"], u["latitude"], u["longitude"] = pd.NA, pd.NA, pd.NA
    if not bot2.empty:
        b = bot2[["codigo_ibge", "municipio", "regiao"]].rename(columns={"municipio": "nome_bot2", "regiao": "regiao_bot2"})
        u = u.merge(b, on="codigo_ibge", how="left")
    else:
        u["nome_bot2"], u["regiao_bot2"] = pd.NA, pd.NA
    u["municipio"] = u["nome_bot2"].fillna(u["nome"]).fillna(u["municipio_tse"].astype(str).str.title())
    u["regiao"] = u["uf"].map(R.UF_REGIAO).fillna(u["regiao_bot2"])
    return u.drop(columns=["nome", "nome_bot2", "regiao_bot2"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Open-Meteo
# ---------------------------------------------------------------------------
def buscar_open_meteo(lats: list[float], lons: list[float], sessao=None, tentativas: int = 3) -> list[dict]:
    """Retorna, para cada local, {'precip': {hora: mm}, 'prob': {hora: %}} do dia da eleição."""
    s = sessao or requests
    out: list[dict] = []
    for i in range(0, len(lats), LOTE):
        la, lo = lats[i:i + LOTE], lons[i:i + LOTE]
        params = {
            "latitude": ",".join(f"{x:.4f}" for x in la), "longitude": ",".join(f"{x:.4f}" for x in lo),
            "hourly": "precipitation,precipitation_probability", "timezone": "America/Sao_Paulo",
            "start_date": DIA, "end_date": DIA,
        }
        ult = None
        for t in range(tentativas):
            try:
                r = s.get(OPEN_METEO_URL, params=params, timeout=40, headers=UA)
                if r.status_code == 429:
                    raise RuntimeError("Open-Meteo 429 (limite de chamadas)")
                r.raise_for_status()
                js = r.json()
                js = js if isinstance(js, list) else [js]
                if len(js) != len(la):
                    raise ValueError(f"Open-Meteo devolveu {len(js)} locais para {len(la)} pedidos")
                for loc in js:
                    h = loc["hourly"]
                    pr, pb = {}, {}
                    for tt, p, q in zip(h["time"], h["precipitation"], h.get("precipitation_probability") or [None] * len(h["time"])):
                        if tt.startswith(DIA) and p is not None:
                            hh = int(tt[11:13])
                            pr[hh] = float(p)
                            if q is not None:
                                pb[hh] = float(q)
                    if len(pr) < 18:
                        raise ValueError("série horária incompleta")
                    out.append({"precip": pr, "prob": pb})
                ult = None
                break
            except Exception as e:  # noqa: BLE001
                ult = e
                time.sleep(2 * (t + 1))
        if ult is not None:
            raise RuntimeError(f"Open-Meteo falhou no lote {i // LOTE + 1}: {ult}") from ult
    return out


def resumir_serie(serie: dict, prob: dict, agora: datetime) -> dict:
    """Totais da janela 08–17h: observado (horas já concluídas, modelo) + previsto restante."""
    ag = agora.astimezone(D.TZ_BRT)
    hora_atual = ag.hour if ag.strftime("%Y-%m-%d") == DIA else (24 if ag.strftime("%Y-%m-%d") > DIA else -1)
    jan = {h: serie.get(h, 0.0) for h in HORAS_JANELA}
    obs = sum(v for h, v in jan.items() if h <= hora_atual)
    prev = sum(v for h, v in jan.items() if h > hora_atual)
    pico_h = max(jan, key=lambda h: jan[h])
    probs = [prob[h] for h in HORAS_JANELA if h in prob]
    return {
        "precipitacao_mm_estimada": round(obs + prev, 1),
        "precip_observada_mm": round(obs, 1),
        "precip_prevista_restante_mm": round(prev, 1),
        "precip_manha_08_12_mm": round(sum(jan[h] for h in range(9, 13)), 1),
        "precip_tarde_12_17_mm": round(sum(jan[h] for h in range(13, 18)), 1),
        "precip_dia_mm": round(sum(serie.values()), 1),
        "horario_pico": f"{pico_h - 1:02d}h-{pico_h:02d}h" if jan[pico_h] > 0 else "—",
        "pico_mm": round(jan[pico_h], 1),
        "probabilidade": int(max(probs)) if probs else pd.NA,
    }


# ---------------------------------------------------------------------------
# INMET
# ---------------------------------------------------------------------------
SEV_MAP = {"perigo potencial": "amarelo", "perigo": "laranja", "grande perigo": "vermelho"}


def _sev(txt: str) -> str:
    return SEV_MAP.get(str(txt or "").strip().lower(), "")


def _evento_chuva(txt: str) -> bool:
    t = D.norm(txt).lower()
    return any(k in t for k in R.EVENTOS_CHUVA)


def _vale_na_janela(inicio: str, fim: str) -> bool:
    try:
        ini = datetime.strptime(str(inicio)[:16], "%Y-%m-%d %H:%M")
        fi = datetime.strptime(str(fim)[:16], "%Y-%m-%d %H:%M")
    except ValueError:
        return True  # sem datas parseáveis: considera vigente (aviso ativo)
    j0, j1 = datetime(2026, 10, 25, 8), datetime(2026, 10, 25, 17)
    return ini < j1 and fi > j0


def parse_inmet_json(js) -> list[dict]:
    itens = []
    if isinstance(js, dict):
        for k in ("hoje", "futuro"):
            itens.extend(js.get(k) or [])
    elif isinstance(js, list):
        itens = js
    out = []
    for a in itens:
        geos = [int(g) for g in str(a.get("geocodes") or "").replace(";", ",").split(",") if g.strip().isdigit()]
        out.append({
            "id": a.get("id"), "evento": a.get("descricao"), "severidade": _sev(a.get("severidade")),
            "severidade_inmet": a.get("severidade"), "inicio": a.get("inicio"), "fim": a.get("fim"),
            "estados": a.get("estados"), "geocodes": geos,
            "link": f"https://alertas2.inmet.gov.br/{a.get('id')}" if a.get("id") else None,
        })
    return out


def parse_inmet_rss(xml_txt: str) -> list[dict]:
    root = ET.fromstring(xml_txt)
    out = []
    for it in root.iter("item"):
        tit = (it.findtext("title") or "").strip()
        desc = it.findtext("description") or ""
        link = (it.findtext("link") or "").strip()
        t = tit.lower()
        sev = ("vermelho" if "grande perigo" in t else "amarelo" if "potencial" in t else
               "laranja" if "perigo" in t else "")
        out.append({"id": link.rstrip("/").split("/")[-1] if link else None, "evento": tit, "severidade": sev,
                    "severidade_inmet": None, "inicio": None, "fim": None, "estados": None, "geocodes": [],
                    "link": link or None, "descricao_rss": desc[:500]})
    return out


def obter_avisos(agora: datetime, sessao=None) -> dict:
    """{'fonte','status','obtido_em_utc','avisos':[...],'erros':[...], 'tem_geocodes': bool}"""
    s = sessao or requests
    cache = out_dir() / "inmet_avisos_latest.json"
    erros = []
    try:
        r = s.get(INMET_JSON, timeout=25, headers=UA)
        r.raise_for_status()
        av = parse_inmet_json(r.json())
        res = {"fonte": INMET_JSON, "status": "ok", "obtido_em_utc": agora.isoformat(), "avisos": av,
               "tem_geocodes": True, "erros": []}
        return res
    except Exception as e:  # noqa: BLE001
        erros.append(f"JSON: {type(e).__name__}: {str(e)[:160]}")
    rss = None
    try:
        r = s.get(INMET_RSS, timeout=25, headers=UA)
        r.raise_for_status()
        rss = parse_inmet_rss(r.text)
    except Exception as e:  # noqa: BLE001
        erros.append(f"RSS: {type(e).__name__}: {str(e)[:160]}")
    # geocódigos: último cache válido do JSON
    if cache.exists():
        try:
            c = json.loads(cache.read_text(encoding="utf-8"))
            if c.get("tem_geocodes"):
                c.update({"status": "stale", "erros": erros, "rss_atual": rss,
                          "fonte": f"cache {c.get('fonte')} (obtido em {c.get('obtido_em_utc')})"})
                return c
        except Exception as e:  # noqa: BLE001
            erros.append(f"cache: {e}")
    if rss is not None:
        return {"fonte": INMET_RSS + " (sem geocódigos) + marcações ALERTA INMET do Bot 2 (06:35 BRT)",
                "status": "rss_sem_geocodigos", "obtido_em_utc": agora.isoformat(), "avisos": rss,
                "tem_geocodes": False, "erros": erros}
    return {"fonte": "marcações ALERTA INMET do Bot 2 (06:35 BRT) – INMET indisponível", "status": "stale",
            "obtido_em_utc": None, "avisos": [], "tem_geocodes": False, "erros": erros}


def alerta_por_municipio(avisos: dict, bot2: pd.DataFrame) -> dict[int, tuple[str, str]]:
    """{codigo_ibge: (severidade, descrição)} só para avisos de chuva/tempestade válidos na janela."""
    out: dict[int, tuple[str, str]] = {}
    if avisos.get("tem_geocodes"):
        for a in avisos.get("avisos", []):
            if not a.get("severidade") or not _evento_chuva(a.get("evento")):
                continue
            if not _vale_na_janela(a.get("inicio"), a.get("fim")):
                continue
            for g in a.get("geocodes", []):
                g7 = int(g)
                atual = out.get(g7, ("", ""))
                if R.SEVERIDADE_ORDEM[a["severidade"]] > R.SEVERIDADE_ORDEM.get(atual[0], 0):
                    out[g7] = (a["severidade"], f"INMET {a['severidade']} – {a.get('evento')} (aviso {a.get('id')})")
    else:
        # sem geocódigos: usa as marcações do Bot 2 da manhã (sinalizado como desatualizado)
        if not bot2.empty:
            for _, r in bot2.iterrows():
                if "ALERTA INMET" in str(r.get("observacoes", "")).upper():
                    out[int(r["codigo_ibge"])] = ("laranja", "ALERTA INMET marcado pelo Bot 2 às 06:35 BRT (desatualizado)")
    return out


# ---------------------------------------------------------------------------
# Agregação
# ---------------------------------------------------------------------------
def _predominante(g: pd.DataFrame) -> pd.Series:
    peso = g["aptos"].fillna(0).astype(float)
    tot = peso.sum() or 1.0
    pct = {l: float(peso[g["nivel_risco"] == l].sum() / tot * 100) for l in "abc"}
    pred = max("abc", key=lambda l: (pct[l], R.ORDEM[l]))
    mm = float((g["precipitacao_mm_estimada"].astype(float) * peso).sum() / tot)
    return pd.Series({"nivel_risco_predominante": pred, "precipitacao_mm_media_estimada": round(mm, 1),
                      "pct_eleitorado_nivel_a": round(pct["a"], 1), "pct_eleitorado_nivel_b": round(pct["b"], 1),
                      "pct_eleitorado_nivel_c": round(pct["c"], 1), "n_municipios": int(len(g)),
                      "aptos_cobertos": int(peso.sum()),
                      "municipios_nivel_a": ", ".join(g.loc[g["nivel_risco"] == "a"].sort_values("aptos", ascending=False)["municipio"].head(8))})


def agregar(mun: pd.DataFrame, ts: str, fonte: str):
    uf = mun.groupby("uf").apply(_predominante, include_groups=False).reset_index()
    uf["estado"] = uf["uf"].map(R.UF_NOME)
    uf["regiao"] = uf["uf"].map(R.UF_REGIAO)
    uf["observacoes"] = uf.apply(lambda r: (f"{r['n_municipios']} municípios cobertos; nível predominante pela maior "
                                            f"fatia do eleitorado coberto. Nível a: {r['municipios_nivel_a'] or '—'}"), axis=1)
    uf["ultima_atualizacao"], uf["fonte"] = ts, fonte
    reg = mun.groupby("regiao").apply(_predominante, include_groups=False).reset_index()
    reg["observacoes"] = reg.apply(lambda r: f"{r['n_municipios']} municípios cobertos; nível a: {r['municipios_nivel_a'] or '—'}", axis=1)
    reg["ultima_atualizacao"], reg["fonte"] = ts, fonte
    m_uf = D.read_csv(D.CLIMA_DIR / "risco_chuva_estados.csv")
    if not m_uf.empty:
        uf = uf.merge(m_uf[["uf", "nivel_risco_predominante"]].rename(columns={"nivel_risco_predominante": "nivel_risco_manha_bot2"}),
                      on="uf", how="left")
    m_rg = D.read_csv(D.CLIMA_DIR / "risco_chuva_regioes.csv")
    if not m_rg.empty:
        reg = reg.merge(m_rg[["regiao", "nivel_risco_predominante"]].rename(columns={"nivel_risco_predominante": "nivel_risco_manha_bot2"}),
                        on="regiao", how="left")
    for df in (uf, reg):
        if "nivel_risco_manha_bot2" not in df.columns:
            df["nivel_risco_manha_bot2"] = pd.NA
        df["mudanca_vs_manha"] = [_mudanca(m, a) for m, a in zip(df["nivel_risco_manha_bot2"], df["nivel_risco_predominante"])]
    cols_uf = ["uf", "estado", "regiao", "nivel_risco_predominante", "precipitacao_mm_media_estimada", "observacoes",
               "ultima_atualizacao", "fonte", "n_municipios", "aptos_cobertos", "pct_eleitorado_nivel_a",
               "pct_eleitorado_nivel_b", "pct_eleitorado_nivel_c", "nivel_risco_manha_bot2", "mudanca_vs_manha"]
    cols_rg = ["regiao", "nivel_risco_predominante", "precipitacao_mm_media_estimada", "observacoes", "ultima_atualizacao",
               "fonte", "n_municipios", "aptos_cobertos", "pct_eleitorado_nivel_a", "pct_eleitorado_nivel_b",
               "pct_eleitorado_nivel_c", "nivel_risco_manha_bot2", "mudanca_vs_manha"]
    return uf[cols_uf].sort_values("aptos_cobertos", ascending=False), reg[cols_rg]


def _mudanca(manha, agora_l) -> str:
    m = R.letra(manha)
    if m is None:
        return "novo (fora da lista da manhã)"
    if m == agora_l:
        return "igual"
    return f"{'subiu' if R.ORDEM[agora_l] > R.ORDEM[m] else 'desceu'} {manha}→{agora_l}"


COLS_MUN = ["codigo_ibge", "municipio", "uf", "regiao", "nivel_risco", "precipitacao_mm_estimada", "horario_pico",
            "probabilidade", "fonte_principal", "ultima_atualizacao", "observacoes", "fonte", "status_dado",
            "cd_tse", "aptos", "lat", "lon", "origem_lista", "precip_observada_mm", "precip_prevista_restante_mm",
            "precip_manha_08_12_mm", "precip_tarde_12_17_mm", "precip_dia_mm", "pico_mm", "alerta_inmet",
            "nivel_risco_previsao", "ajuste_noticias", "ajuste_nivel", "ajuste_intensidade_mm", "ajuste_confianca",
            "ajuste_fontes", "ajuste_evidencia", "ajuste_timestamp_brt", "nivel_risco_manha_bot2",
            "precip_manha_bot2_mm", "mudanca_vs_manha"]


def executar(agora: datetime | None = None, buscar=None, sessao=None) -> dict:
    agora = agora or datetime.now(UTC)
    od = out_dir()
    od.mkdir(parents=True, exist_ok=True)
    ts = fmt_brt(agora)
    stamp = agora.astimezone(UTC).strftime("%Y%m%d_%H%MUTC")
    log: list[str] = []

    ajustes = D.carregar_ajustes()
    u = universo(ajustes)
    bot2 = D.read_csv(D.CLIMA_DIR / "risco_chuva_municipios.csv")
    anterior = D.read_csv(od / "risco_chuva_municipios_latest.csv")
    log.append(f"universo: {len(u)} municípios ({u['origem_lista'].value_counts().to_dict()}); ajustes ativos: {len(ajustes)}")

    # --- Open-Meteo
    com_coord = u[u["latitude"].notna() & u["longitude"].notna()].reset_index(drop=True)
    series, erro_om = {}, None
    try:
        res = (buscar or buscar_open_meteo)(com_coord["latitude"].astype(float).tolist(),
                                            com_coord["longitude"].astype(float).tolist())
        for (_, r), s in zip(com_coord.iterrows(), res):
            series[int(r["codigo_ibge"])] = s
        log.append(f"Open-Meteo ok: {len(series)} séries")
    except Exception as e:  # noqa: BLE001
        erro_om = f"{type(e).__name__}: {e}"
        log.append(f"Open-Meteo FALHOU: {erro_om}")

    # --- INMET
    avisos = obter_avisos(agora, sessao=sessao)
    log.append(f"INMET: {avisos['status']} ({avisos['fonte']}); {len(avisos.get('avisos', []))} avisos; erros={avisos.get('erros')}")
    if avisos["status"] == "ok":
        (od / "inmet_avisos_latest.json").write_text(json.dumps(avisos, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    alertas = alerta_por_municipio(avisos, bot2)
    inmet_stale = avisos["status"] != "ok"

    aj = {int(r["codigo_ibge"]): r for _, r in ajustes.iterrows()}
    b2 = {int(r["codigo_ibge"]): r for _, r in bot2.iterrows()} if not bot2.empty else {}
    ant = {int(r["codigo_ibge"]): r for _, r in anterior.iterrows()} if not anterior.empty else {}

    linhas, horaria = [], []
    for _, m in u.iterrows():
        cod = int(m["codigo_ibge"])
        row = {"codigo_ibge": cod, "municipio": m["municipio"], "uf": m["uf"], "regiao": m["regiao"],
               "cd_tse": m["cd_tse"], "aptos": m["aptos"], "lat": m.get("latitude"), "lon": m.get("longitude"),
               "origem_lista": m["origem_lista"], "ultima_atualizacao": ts}
        sev, desc = alertas.get(cod, ("", ""))
        if cod in series:
            sm = resumir_serie(series[cod]["precip"], series[cod]["prob"], agora)
            row.update(sm)
            row["nivel_risco_previsao"] = R.classificar(sm["precipitacao_mm_estimada"], sev)
            row["fonte_principal"] = "Open-Meteo horário" + (f" + {desc}" if sev else "")
            row["status_dado"] = "ok" if not (sev and inmet_stale) else "ok (alerta INMET desatualizado)"
            row["fonte"] = f"Open-Meteo /v1/forecast ({agora.astimezone(D.TZ_BRT):%H:%M} BRT); INMET: {avisos['status']}"
            horaria.append({"codigo_ibge": cod, "municipio": m["municipio"], "uf": m["uf"], "aptos": m["aptos"],
                            "lat": m["latitude"], "lon": m["longitude"], "obtido_em_utc": agora.isoformat(),
                            **{f"h{h:02d}": series[cod]["precip"].get(h, 0.0) for h in range(24)}})
        elif cod in ant:
            p = ant[cod]
            for k in COLS_MUN:
                if k in p.index and k not in row:
                    row[k] = p[k]
            row["ultima_atualizacao"] = p.get("ultima_atualizacao")
            row["nivel_risco_previsao"] = R.letra(p.get("nivel_risco_previsao")) or R.letra(p.get("nivel_risco"))
            row["status_dado"] = f"stale (Open-Meteo falhou; último valor de {p.get('ultima_atualizacao')})"
        elif cod in b2:
            p = b2[cod]
            row.update({"precipitacao_mm_estimada": p["precipitacao_mm_estimada"], "horario_pico": p["horario_pico"],
                        "probabilidade": p["probabilidade"], "fonte_principal": p["fonte_principal"]})
            row["ultima_atualizacao"] = p["ultima_atualizacao"]
            row["nivel_risco_previsao"] = R.letra(p["nivel_risco"])
            row["status_dado"] = "stale (Open-Meteo falhou; classificação original do Bot 2)"
            row["fonte"] = "Bot 2 original (06:35 BRT)"
        else:
            row["nivel_risco_previsao"] = None
            row["status_dado"] = "sem dado de previsão"
            row["fonte"] = "—"
        row["alerta_inmet"] = desc or ""
        # --- ajuste por notícias (piso)
        nivel = row["nivel_risco_previsao"]
        if cod in aj:
            a = aj[cod]
            row.update({"ajuste_noticias": "sim", "ajuste_nivel": a["letra_ajuste"],
                        "ajuste_intensidade_mm": a["intensidade_estimada_mm"], "ajuste_confianca": a["confianca"],
                        "ajuste_fontes": a["fontes"], "ajuste_evidencia": a["evidencia"],
                        "ajuste_timestamp_brt": a["timestamp_brt"]})
            nivel = R.maior(nivel, a["letra_ajuste"])
        else:
            row["ajuste_noticias"] = "não"
        if nivel is None:
            continue
        row["nivel_risco"] = nivel
        if cod in b2:
            row["nivel_risco_manha_bot2"] = b2[cod]["nivel_risco"]
            row["precip_manha_bot2_mm"] = b2[cod]["precipitacao_mm_estimada"]
        row["mudanca_vs_manha"] = _mudanca(row.get("nivel_risco_manha_bot2"), nivel)
        obs = [f"janela 08–17h: {row.get('precip_observada_mm', '—')} mm já ocorridos (modelo) + "
               f"{row.get('precip_prevista_restante_mm', '—')} mm previstos"]
        if desc:
            obs.append(desc)
        if row["ajuste_noticias"] == "sim":
            obs.append(f"ajuste por notícias → {row['ajuste_nivel']} (confiança {row['ajuste_confianca']})")
        row["observacoes"] = "; ".join(obs)
        linhas.append(row)

    mun = pd.DataFrame(linhas)
    for c in COLS_MUN:
        if c not in mun.columns:
            mun[c] = pd.NA
    mun = mun[COLS_MUN]
    mun["_o"] = mun["nivel_risco"].map(R.ORDEM)
    mun = mun.sort_values(["_o", "aptos"], ascending=[False, False]).drop(columns="_o")

    fonte_ag = f"agregado de risco_chuva_municipios_latest.csv ({len(mun)} municípios, ponderado por aptos)"
    uf, reg = agregar(mun, ts, fonte_ag)

    ok_om = erro_om is None
    if ok_om or anterior.empty:
        mun.to_csv(od / "risco_chuva_municipios_latest.csv", index=False)
        uf.to_csv(od / "risco_chuva_estados_latest.csv", index=False)
        reg.to_csv(od / "risco_chuva_regioes_latest.csv", index=False)
        mun.to_csv(od / f"risco_chuva_municipios_{stamp}.csv", index=False)
        uf.to_csv(od / f"risco_chuva_estados_{stamp}.csv", index=False)
        reg.to_csv(od / f"risco_chuva_regioes_{stamp}.csv", index=False)
    else:
        # Open-Meteo falhou: mantém o último latest válido, só reaplica ajustes/alertas (marcado stale)
        mun.to_csv(od / "risco_chuva_municipios_latest.csv", index=False)
        uf.to_csv(od / "risco_chuva_estados_latest.csv", index=False)
        reg.to_csv(od / "risco_chuva_regioes_latest.csv", index=False)
    if horaria:
        pd.DataFrame(horaria).to_csv(od / "precip_horaria_latest.csv", index=False)

    status = {
        "executado_em_utc": agora.isoformat(), "executado_em_brt": ts,
        "open_meteo": {"status": "ok" if ok_om else "falha", "erro": erro_om, "n_series": len(series)},
        "inmet": {"status": avisos["status"], "fonte": avisos["fonte"], "obtido_em_utc": avisos.get("obtido_em_utc"),
                  "erros": avisos.get("erros"), "n_avisos": len(avisos.get("avisos", []))},
        "n_municipios": int(len(mun)), "ajustes_ativos": int(len(ajustes)),
        "arquivo_versionado": f"risco_chuva_municipios_{stamp}.csv" if (ok_om or anterior.empty) else None,
        "log": log,
    }
    (od / "status_latest.json").write_text(json.dumps(status, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    (od / "resumo_latest.md").write_text(resumo_md(mun, uf, reg, status, avisos), encoding="utf-8")
    return {"municipios": mun, "estados": uf, "regioes": reg, "status": status}


def resumo_md(mun, uf, reg, status, avisos) -> str:
    l = [f"# Risco de chuva – atualização automática ({status['executado_em_brt']})", "",
         "Gerado por `scripts/atualizar_clima.py` (executa o papel do Bot 2). Janela de votação 08h–17h BRT.", "",
         f"- Open-Meteo: **{status['open_meteo']['status']}** ({status['open_meteo']['n_series']} séries)"
         + (f" – erro: {status['open_meteo']['erro']}" if status['open_meteo']['erro'] else ""),
         f"- INMET: **{status['inmet']['status']}** – {status['inmet']['fonte']}",
         f"- Municípios classificados: {len(mun)} · ajustes por notícias ativos: {status['ajustes_ativos']}", "",
         "## Contagem por nível", ""]
    for k in "abc":
        sub = mun[mun["nivel_risco"] == k]
        apt = f"{int(sub['aptos'].fillna(0).sum()):,}".replace(",", ".")
        l.append(f"- **{R.ROTULO_LETRA[k]}**: {len(sub)} municípios, {apt} aptos")
    l += ["", "## Mudanças vs classificação da manhã (Bot 2, 06:35 BRT)", ""]
    b2 = mun[mun["nivel_risco_manha_bot2"].notna()]
    mud = b2[b2["mudanca_vs_manha"] != "igual"]
    if mud.empty:
        l.append("- Nenhuma mudança nos 29 municípios do Bot 2.")
    for _, r in mud.iterrows():
        l.append(f"- {r['municipio']}/{r['uf']}: {r['mudanca_vs_manha']} ({r['precipitacao_mm_estimada']} mm na janela"
                 f"; manhã {r['precip_manha_bot2_mm']} mm)")
    l.append(f"- Iguais: {int((b2['mudanca_vs_manha'] == 'igual').sum())} de {len(b2)}")
    mu = uf[uf["nivel_risco_manha_bot2"].notna() & (uf["mudanca_vs_manha"] != "igual")]
    if not mu.empty:
        l += ["", "### Estados com mudança", ""] + [f"- {r['uf']}: {r['mudanca_vs_manha']}" for _, r in mu.iterrows()]
    aj = mun[mun["ajuste_noticias"] == "sim"]
    l += ["", "## Ajustes por notícias aplicados", ""]
    l += ([f"- {r['municipio']}/{r['uf']}: {r['ajuste_nivel']} (confiança {r['ajuste_confianca']}) – {r['ajuste_fontes']}"
           for _, r in aj.iterrows()] or ["- Nenhum."])
    l += ["", "## Avisos INMET considerados", ""]
    for a in avisos.get("avisos", [])[:25]:
        l.append(f"- {a.get('id')}: {a.get('severidade') or '?'} – {a.get('evento')} ({a.get('inicio') or ''}–{a.get('fim') or ''})")
    if not avisos.get("avisos"):
        l.append("- Lista indisponível nesta execução (ver status).")
    l += ["", "Nenhum dado é inventado; em falha de fonte, o último dado válido é mantido e marcado como desatualizado."]
    return "\n".join(l) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.parse_args()
    r = executar()
    st = r["status"]
    print(f"OK clima: {st['n_municipios']} municípios · Open-Meteo {st['open_meteo']['status']} · INMET {st['inmet']['status']}")
    for x in st["log"]:
        print("  -", x)


if __name__ == "__main__":
    main()
