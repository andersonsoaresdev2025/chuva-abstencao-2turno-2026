#!/usr/bin/env python3
"""
Coleta automática de sinais sociais (chuva × votação) – a cada 30 min.

- X (x.com): API v2 /tweets/search/recent SOMENTE se houver credencial em variável de ambiente
  (X_BEARER_TOKEN ou TWITTER_BEARER_TOKEN). Sem credencial: etapa pulada e registrada no log.
  (O monitoramento manual via X MCP descrito em data/social/README.md continua valendo.)
- Instagram: SEM login e SEM raspagem atrás de login. Apenas resultados públicos de buscadores web
  (DuckDuckGo HTML/Lite, Brave Search) para "site:instagram.com" + palavras-chave + cidades prioritárias.
  Linhas: rede=instagram, confianca=baixa (media se a conta for oficial conhecida).
- Grava/atualiza data/social/sinais_<YYYYMMDD>_auto.csv (schema do monitoramento + coluna `rede`)
  e data/social/log_coleta_social.csv (uma linha por consulta, inclusive quando nada é encontrado).
Nunca inventa conteúdo: só título/trecho públicos devolvidos pelo buscador, com o link original.
"""
from __future__ import annotations

import csv
import html
import os
import re
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from common import dados as D  # noqa: E402

UTC = timezone.utc
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
      "Accept-Language": "pt-BR,pt;q=0.9"}
COLS = D.SOCIAL_COLS
LOG_COLS = ["timestamp_utc", "rede", "motor", "consulta", "status", "n_resultados", "n_relevantes", "erro"]

CHUVA = ["chuva", "chove", "chovendo", "temporal", "tempestade", "alagamento", "alagad", "enchente", "inundac",
         "granizo", "queda de arvore", "sem energia", "sem luz", "deslizamento"]
ELEICAO = ["eleic", "eleitor", "votacao", "votar", "voto", "urna", "secao eleitoral", "local de votacao",
           "zona eleitoral", "segundo turno", "2o turno", "2º turno", "tse", "tre-", "tre ", "abstenc"]
OUTROS_ANOS = ["2018", "2020", "2022", "2024"]
OFICIAIS = {"defesacivilsp", "defesacivilrj", "defesacivilrs", "defesacivilpr", "defesacivilsc", "defesacivil",
            "inmet", "inmetbrasil", "tsejus", "tse_jus", "tresp", "trerj", "trepr", "trers", "tresc", "tremg",
            "cgesp", "alertario", "climatempo", "metsul", "g1", "jornalnacional", "folhadespaulo", "estadao",
            "cnnbrasil", "bandjornalismo", "agenciabrasil"}
CONSULTAS_BASE = ["chuva eleição votação", "chuva segundo turno votar", "alagamento seção eleitoral",
                  "temporal local de votação"]
CIDADES = ["São Paulo", "Rio de Janeiro", "Guarulhos", "Campinas", "Curitiba", "Campo Grande", "Osasco",
           "Santo André", "São Bernardo", "São Gonçalo", "Duque de Caxias", "Nova Iguaçu", "Porto Alegre",
           "Sorocaba", "Ribeirão Preto", "São José dos Campos", "Londrina"]


def norm(t: str) -> str:
    s = unicodedata.normalize("NFKD", str(t or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s)


def relevante(texto: str) -> tuple[bool, str]:
    t = norm(texto)
    if not any(k in t for k in CHUVA):
        return False, "sem termo de chuva"
    if not any(norm(k) in t for k in ELEICAO):
        return False, "sem termo eleitoral"
    if any(a in t for a in OUTROS_ANOS) and "2026" not in t:
        return False, "outro ano eleitoral"
    return True, ""


def tipo_e_nivel(texto: str) -> tuple[str, str]:
    t = norm(texto)
    if any(k in t for k in ["alagamento", "alagad", "enchente", "inundac", "deslizamento"]):
        return "alagamento", "alto"
    if any(k in t for k in ["temporal", "tempestade", "granizo", "queda de arvore"]):
        return "chuva", "alto"
    if any(k in t for k in ["sem energia", "sem luz", "fila", "transferid", "transporte"]):
        return "mobilidade", "medio"
    return "chuva", "medio"


def detectar_cidade(texto: str, risco: dict) -> tuple[str, str, str]:
    t = norm(texto)
    for c in sorted(risco, key=len, reverse=True):
        if norm(c) in t:
            uf, nv = risco[c]
            return c, uf, nv
    return "", "", "n/d"


def carregar_risco() -> dict:
    df, _ = D.latest_ou_original(D.ATUAL_CLIMA_DIR / "risco_chuva_municipios_latest.csv",
                                 D.CLIMA_DIR / "risco_chuva_municipios.csv")
    if df.empty:
        return {}
    df = df.sort_values("aptos", ascending=False) if "aptos" in df.columns else df
    return {str(r["municipio"]): (r["uf"], str(r["nivel_risco"])[0]) for _, r in df.head(80).iterrows()}


# ---------------------------------------------------------------------------
# Buscadores (resultados públicos; sem login)
# ---------------------------------------------------------------------------
class Bloqueado(Exception):
    pass


def _limpa(x: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(x or ""))).strip()


def parse_ddg_html(txt: str) -> list[dict]:
    if "anomaly" in txt.lower() and "result__a" not in txt:
        raise Bloqueado("DuckDuckGo: verificação anti-robô (anomaly)")
    out = []
    for blk in txt.split('class="result ')[1:]:
        a = re.search(r'result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', blk, re.S)
        if not a:
            continue
        href = html.unescape(a.group(1))
        if "uddg=" in href:
            href = unquote(parse_qs(urlparse("https:" + href if href.startswith("//") else href).query).get("uddg", [""])[0])
        sn = re.search(r'result__snippet[^>]*>(.*?)</(?:a|td|div)>', blk, re.S)
        out.append({"link": href, "titulo": _limpa(a.group(2)), "trecho": _limpa(sn.group(1)) if sn else ""})
    return out


def parse_ddg_lite(txt: str) -> list[dict]:
    if "anomaly" in txt.lower() and "result-link" not in txt:
        raise Bloqueado("DuckDuckGo Lite: verificação anti-robô (anomaly)")
    out = []
    links = re.findall(r"<a[^>]+href=\"([^\"]+)\"[^>]*class=['\"]result-link['\"][^>]*>(.*?)</a>", txt, re.S)
    snips = re.findall(r"class=['\"]result-snippet['\"][^>]*>(.*?)</td>", txt, re.S)
    for i, (h, t) in enumerate(links):
        h = html.unescape(h)
        if "uddg=" in h:
            h = unquote(parse_qs(urlparse("https:" + h if h.startswith("//") else h).query).get("uddg", [""])[0])
        out.append({"link": h, "titulo": _limpa(t), "trecho": _limpa(snips[i]) if i < len(snips) else ""})
    return out


def parse_brave(txt: str) -> list[dict]:
    out = []
    for m in re.finditer(r'href="(https://www\.instagram\.com/[^"]+)"[^>]*>(.*?)</a>', txt, re.S):
        out.append({"link": html.unescape(m.group(1)), "titulo": _limpa(m.group(2))[:200], "trecho": ""})
    return out


MOTORES = {
    "duckduckgo_html": ("https://html.duckduckgo.com/html/?q={q}&df=d&kl=br-pt", parse_ddg_html),
    "duckduckgo_lite": ("https://lite.duckduckgo.com/lite/?q={q}&df=d&kl=br-pt", parse_ddg_lite),
    "brave": ("https://search.brave.com/search?q={q}&tf=pd", parse_brave),
}


def buscar_web(consulta: str, motor: str, sessao=None) -> list[dict]:
    s = sessao or requests
    url, parser = MOTORES[motor]
    r = s.get(url.format(q=quote_plus(consulta)), headers=UA, timeout=20)
    if r.status_code in (202, 403, 429):
        raise Bloqueado(f"{motor}: HTTP {r.status_code} (limite/anti-robô)")
    r.raise_for_status()
    return parser(r.text)


def conta_instagram(link: str) -> str:
    p = urlparse(link).path.strip("/").split("/")
    if not p or not p[0]:
        return ""
    return "" if p[0] in ("p", "reel", "reels", "tv", "explore", "stories") else p[0].lower()


def coletar_instagram(agora: datetime, risco: dict, sessao=None, pausa: float = 2.0, max_consultas: int = 4):
    slot = (agora.hour * 2 + agora.minute // 30)
    cidade = CIDADES[slot % len(CIDADES)]
    consultas = [CONSULTAS_BASE[slot % len(CONSULTAS_BASE)], f"chuva {cidade} votação",
                 CONSULTAS_BASE[(slot + 1) % len(CONSULTAS_BASE)], f"alagamento {cidade} eleição"][:max_consultas]
    sinais, log = [], []
    motores = list(MOTORES)
    bloqueados: set[str] = set()
    for c in consultas:
        q = f"site:instagram.com {c}"
        feito = False
        for mt in motores:
            if mt in bloqueados:
                continue
            try:
                res = buscar_web(q, mt, sessao=sessao)
            except Bloqueado as e:
                bloqueados.add(mt)
                log.append(_log(agora, "instagram", mt, q, "bloqueado", 0, 0, str(e)))
                continue
            except Exception as e:  # noqa: BLE001
                log.append(_log(agora, "instagram", mt, q, "erro", 0, 0, f"{type(e).__name__}: {str(e)[:120]}"))
                continue
            ig = [x for x in res if "instagram.com/" in x["link"]]
            rel = 0
            for x in ig:
                texto = f"{x['titulo']} {x['trecho']}"
                ok, _ = relevante(texto)
                if not ok:
                    continue
                rel += 1
                conta = conta_instagram(x["link"])
                oficial = conta in OFICIAIS
                tipo, nivel = tipo_e_nivel(texto)
                cid, uf, nv = detectar_cidade(texto, risco)
                sinais.append({
                    "timestamp_coleta_utc": agora.strftime("%Y-%m-%dT%H:%M:%SZ"), "timestamp_post": "",
                    "cidade": cid, "uf": uf, "cidade_risco_previsto": nv, "tipo": tipo,
                    "nivel_risco_implicito": nivel, "confianca": "media" if oficial else "baixa",
                    "fonte": f"Instagram @{conta}" if conta else "Instagram",
                    "tipo_fonte": "oficial" if oficial else "relato",
                    "resumo": (f"[busca web {mt}] {x['titulo']} — {x['trecho']}")[:400],
                    "link": x["link"], "rede": "instagram"})
            log.append(_log(agora, "instagram", mt, q, "ok" if rel else "ok_sem_relevantes", len(ig), rel, ""))
            feito = True
            break
        if not feito and len(bloqueados) == len(motores):
            log.append(_log(agora, "instagram", "todos", q, "pulado", 0, 0, "todos os buscadores bloquearam nesta execução"))
            break
        time.sleep(pausa)
    return sinais, log


def coletar_x(agora: datetime, risco: dict, sessao=None):
    token = os.environ.get("X_BEARER_TOKEN") or os.environ.get("TWITTER_BEARER_TOKEN")
    q = ('(chuva OR tempestade OR alagamento OR temporal OR enchente) (eleição OR urna OR votação OR '
         '"seção eleitoral" OR "segundo turno" OR votar) lang:pt -is:retweet')
    if not token:
        return [], [_log(agora, "x", "api_v2", q, "pulado", 0, 0, "sem credencial X_BEARER_TOKEN/TWITTER_BEARER_TOKEN")]
    s = sessao or requests
    try:
        r = s.get("https://api.twitter.com/2/tweets/search/recent",
                  params={"query": q, "max_results": 50, "tweet.fields": "created_at,author_id",
                          "expansions": "author_id", "user.fields": "username,verified"},
                  headers={"Authorization": f"Bearer {token}"}, timeout=25)
        r.raise_for_status()
        js = r.json()
    except Exception as e:  # noqa: BLE001
        return [], [_log(agora, "x", "api_v2", q, "erro", 0, 0, f"{type(e).__name__}: {str(e)[:120]}")]
    users = {u["id"]: u for u in (js.get("includes", {}) or {}).get("users", [])}
    sinais = []
    for t in js.get("data", []) or []:
        texto = t.get("text", "")
        ok, _ = relevante(texto)
        if not ok:
            continue
        u = users.get(t.get("author_id"), {})
        nome = u.get("username", "")
        oficial = nome.lower() in OFICIAIS
        tipo, nivel = tipo_e_nivel(texto)
        cid, uf, nv = detectar_cidade(texto, risco)
        sinais.append({
            "timestamp_coleta_utc": agora.strftime("%Y-%m-%dT%H:%M:%SZ"), "timestamp_post": t.get("created_at", ""),
            "cidade": cid, "uf": uf, "cidade_risco_previsto": nv, "tipo": tipo, "nivel_risco_implicito": nivel,
            "confianca": "media" if oficial else "baixa", "fonte": f"X @{nome}" if nome else "X",
            "tipo_fonte": "oficial" if oficial else "relato", "resumo": texto[:400],
            "link": f"https://x.com/{nome or 'i'}/status/{t['id']}", "rede": "x"})
    return sinais, [_log(agora, "x", "api_v2", q, "ok" if sinais else "ok_sem_relevantes",
                         len(js.get("data", []) or []), len(sinais), "")]


def _log(agora, rede, motor, consulta, status, n, nrel, erro) -> dict:
    return {"timestamp_utc": agora.strftime("%Y-%m-%dT%H:%M:%SZ"), "rede": rede, "motor": motor, "consulta": consulta,
            "status": status, "n_resultados": n, "n_relevantes": nrel, "erro": erro}


def _append(p: Path, linhas: list[dict], cols: list[str], chave: str | None = None):
    existentes = []
    if p.exists():
        with p.open(encoding="utf-8") as f:
            existentes = list(csv.DictReader(f))
    if chave:
        vistos = {r.get(chave) for r in existentes}
        linhas = [r for r in linhas if r.get(chave) not in vistos]
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in existentes + linhas:
            w.writerow({c: r.get(c, "") for c in cols})
    return len(linhas)


def executar(agora: datetime | None = None, sessao=None, pausa: float = 2.0) -> dict:
    agora = agora or datetime.now(UTC)
    od = D.SOCIAL_DIR
    od.mkdir(parents=True, exist_ok=True)
    risco = carregar_risco()
    sx, lx = coletar_x(agora, risco, sessao=sessao)
    si, li = coletar_instagram(agora, risco, sessao=sessao, pausa=pausa)
    sinais, log = sx + si, lx + li
    arq = od / f"sinais_{agora:%Y%m%d}_auto.csv"
    novos = _append(arq, sinais, COLS, chave="link") if sinais else 0
    if not sinais:
        log.append(_log(agora, "todas", "-", "-", "nada_encontrado", 0, 0, "nenhum sinal relevante nesta execução"))
    _append(od / "log_coleta_social.csv", log, LOG_COLS)
    return {"novos": novos, "sinais": sinais, "log": log, "arquivo": arq.name if novos or arq.exists() else None}


def main():
    r = executar()
    print(f"OK social: {len(r['sinais'])} relevantes, {r['novos']} novos → {r['arquivo']}")
    for x in r["log"]:
        print(f"  - {x['rede']}/{x['motor']}: {x['status']} ({x['n_resultados']} res., {x['n_relevantes']} relev.) {x['erro']}")


if __name__ == "__main__":
    main()
