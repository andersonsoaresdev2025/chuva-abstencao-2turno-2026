#!/usr/bin/env python3
"""
Coletor de notícias: chuva × eleição (2º turno, 25/10/2026).

Fontes:
  1. Feeds RSS verificados em data/noticias/portais.csv (coluna rss_url);
  2. Google Notícias RSS (pt-BR) com buscas temáticas, por cidade e por portal (site:)
     para os portais sem RSS verificado.

Regras: apenas itens realmente baixados (nada é inventado); janela = publicados em
25/10/2026 (BRT) ou a partir de 24/10 18h BRT; filtro por palavras-chave de chuva
e de eleição; deduplicação por URL e similaridade de título; marcação de itens
não verificáveis ou que contradizem fontes oficiais.

Saídas em data/noticias/:
  noticias_<YYYYMMDD_HHMM>UTC.csv  (esta coleta)
  noticias_consolidado.csv         (todas as coletas, deduplicado)
  resumo_noticias.md               (resumo legível)

Uso:  python3 scripts/coletar_noticias.py  [--sem-gnews] [--max-workers 12]
Só usa a biblioteca padrão do Python.
"""
from __future__ import annotations

import argparse
import csv
import concurrent.futures as cf
import difflib
import gzip
import html
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zlib
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "noticias"
PORTAIS_CSV = OUT / "portais.csv"
RISCO_CSV = ROOT / "data" / "clima" / "previsoes_2026-10-25" / "risco_chuva_municipios.csv"

UTC = timezone.utc
BRT = timezone(timedelta(hours=-3))
DIA = datetime(2026, 10, 25, tzinfo=BRT).date()
INICIO_JANELA = datetime(2026, 10, 24, 18, 0, tzinfo=BRT)
FIM_JANELA = datetime(2026, 10, 26, 0, 0, tzinfo=BRT)
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"

COLS = ["id", "titulo", "link", "portal", "dominio", "abrangencia", "uf", "cidade", "regiao",
        "tema", "publicado_brt", "publicado_utc", "coletado_utc", "score", "sinalizacao",
        "menciona_eleicao", "origem_coleta", "resumo"]


def norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", str(t or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", t).strip()


# ---------------------------------------------------------------- palavras-chave
CHUVA = ["chuva", "chuvas", "chuvoso", "temporal", "temporais", "tempestade", "alagamento", "alagamentos",
         "alagad", "enchente", "inundac", "cheia do rio", "cheia", "granizo", "vendaval", "deslizamento",
         "defesa civil", "inmet", "alerta laranja", "alerta vermelho", "alerta amarelo", "simepar",
         "cge", "alerta rio", "queda de arvore", "arvores caidas", "falta de energia", "sem luz",
         "previsao do tempo", "frente fria", "ciclone", "mau tempo", "meteorolog"]
CHUVA_FORTE = ["temporal", "tempestade", "alagamento", "alagad", "enchente", "inundac", "granizo",
               "vendaval", "deslizamento", "defesa civil", "alerta laranja", "alerta vermelho",
               "chuva forte", "chuvas fortes", "cheia", "queda de arvore", "sem luz", "falta de energia"]
ELEICAO = ["eleic", "eleitor", "votacao", "votar", "voto", "votos", "urna", "secao eleitoral",
           "secoes eleitorais", "secoes", "local de votacao", "locais de votacao", "abstenc",
           "comparecimento", "tse", "tre-", "tre ", "segundo turno", "2o turno", "2º turno", "mesario",
           "justificativa", "justificar"]
TEMAS = [  # ordem = prioridade
    ("locais de votação", ["local de votacao", "locais de votacao", "transferid", "muda local", "mudanca de local",
                           "secao", "secoes", "remanejad", "zona eleitoral"]),
    ("abstenção", ["abstenc", "comparecimento", "justificativa", "justificar", "deixar de votar", "deixou de votar",
                   "faltar", "ausencia"]),
    ("alagamento", ["alagamento", "alagad", "enchente", "inundac", "cheia", "transbord", "deslizamento"]),
    ("mobilidade", ["transito", "transporte", "onibus", "metro", "cptm", "trem", "queda de arvore", "arvores",
                    "sem luz", "falta de energia", "energia", "interdit", "bloquead", "congestion", "mobilidade"]),
    ("alerta", ["alerta", "inmet", "defesa civil", "previsao", "aviso", "simepar", "meteorolog", "frente fria"]),
]
# Alegações que contradizem fontes oficiais (TSE/TREs) se não vierem de veículo verificado
SUSPEITO = ["eleicao adiada", "eleicao cancelada", "votacao suspensa em todo", "votacao cancelada",
            "urnas nao funcionam por causa da chuva", "metade do pais", "eleicao suspensa", "fraude"]

UF_NOME = {"sao paulo": "SP", "rio de janeiro": "RJ", "parana": "PR", "mato grosso do sul": "MS",
           "santa catarina": "SC", "rio grande do sul": "RS", "minas gerais": "MG", "espirito santo": "ES",
           "goias": "GO", "distrito federal": "DF", "bahia": "BA", "mato grosso": "MT"}
REGIAO_UF = {"SP": "Sudeste", "RJ": "Sudeste", "MG": "Sudeste", "ES": "Sudeste", "PR": "Sul", "SC": "Sul",
             "RS": "Sul", "MS": "Centro-Oeste", "MT": "Centro-Oeste", "GO": "Centro-Oeste", "DF": "Centro-Oeste",
             "BA": "Nordeste", "PE": "Nordeste", "CE": "Nordeste", "AM": "Norte", "PA": "Norte"}
CIDADES_EXTRA = {"baixada fluminense": ("Baixada Fluminense", "RJ"), "grande abc": ("Grande ABC", "SP"),
                 "abc paulista": ("Grande ABC", "SP"), "grande sp": ("Grande SP", "SP"),
                 "grande sao paulo": ("Grande SP", "SP"), "baixada santista": ("Baixada Santista", "SP"),
                 "santos": ("Santos", "SP"), "vale do paraiba": ("Vale do Paraíba", "SP"),
                 "guaratuba": ("Guaratuba", "PR"), "rio uruguai": ("Rio Uruguai (RS)", "RS"),
                 "sao caetano": ("São Caetano do Sul", "SP"), "diadema": ("Diadema", "SP"),
"niteroi": ("Niterói", "RJ"), "belford roxo": ("Belford Roxo", "RJ"),
                 "sao joao de meriti": ("São João de Meriti", "RJ"), "jundiai": ("Jundiaí", "SP"),
                 "taubate": ("Taubaté", "SP"), "regiao metropolitana de curitiba": ("RM Curitiba", "PR"),
                 "sao jose dos pinhais": ("São José dos Pinhais", "PR"), "dourados": ("Dourados", "MS"),
                 "blumenau": ("Blumenau", "SC"), "porto maua": ("Rio Uruguai (RS)", "RS"),
                 "irai": ("Rio Uruguai (RS)", "RS"), "uruguaiana": ("Rio Uruguai (RS)", "RS")}


def carregar_cidades() -> tuple[dict, set]:
    """{nome_normalizado: (Nome, UF)} e conjunto de cidades de risco alto (a)."""
    cidades, altas = dict(CIDADES_EXTRA), set()
    if RISCO_CSV.exists():
        with RISCO_CSV.open(encoding="utf-8") as f:
            for r in csv.DictReader(f):
                cidades[norm(r["municipio"])] = (r["municipio"], r["uf"])
                if str(r.get("nivel_risco", "")).strip().lower().startswith("a"):
                    altas.add(r["municipio"])
    # "rio de janeiro"/"sao paulo"/"campo grande" também são nomes de UF/bairros: tratados na detecção
    return cidades, altas


def carregar_portais() -> list[dict]:
    with PORTAIS_CSV.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- HTTP + parsing
def baixar(url: str, timeout: int = 25) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip, deflate",
                                               "Accept": "application/rss+xml, application/xml, text/xml, */*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
        enc = (r.headers.get("Content-Encoding") or "").lower()
    if enc == "gzip" or data[:2] == b"\x1f\x8b":
        data = gzip.decompress(data)
    elif enc == "deflate":
        data = zlib.decompress(data)
    return data


def limpar_html(t: str) -> str:
    t = re.sub(r"<[^>]+>", " ", html.unescape(t or ""))
    return re.sub(r"\s+", " ", t).strip()


def _txt(el, *tags):
    for tag in tags:
        x = el.find(tag)
        if x is not None and (x.text or "").strip():
            return x.text.strip()
        if x is not None and x.get("href"):
            return x.get("href")
    return ""


def parse_feed(data: bytes) -> list[dict]:
    data = re.sub(rb"^[\s\xef\xbb\xbf]+", b"", data)
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        # feeds sem declaração de encoding em latin-1 (ex.: UOL)
        txt = data.decode("latin-1")
        txt = re.sub(r"^<\?xml[^>]*\?>", "", txt.lstrip())
        root = ET.fromstring(txt.encode("utf-8"))
    itens = []
    atom = "{http://www.w3.org/2005/Atom}"
    for it in root.iter():
        tag = it.tag.split("}")[-1]
        if tag not in ("item", "entry"):
            continue
        titulo = _txt(it, "title", f"{atom}title")
        link = _txt(it, "link", f"{atom}link")
        pub = _txt(it, "pubDate", f"{atom}published", f"{atom}updated",
                   "{http://purl.org/dc/elements/1.1/}date")
        desc = _txt(it, "description", f"{atom}summary")
        src = it.find("source")
        itens.append({"titulo": limpar_html(titulo), "link": link.strip(), "pub": pub,
                      "desc": limpar_html(desc)[:400],
                      "fonte_nome": (src.text or "").strip() if src is not None else "",
                      "fonte_url": src.get("url", "") if src is not None else ""})
    return itens


def parse_data(s: str) -> datetime | None:
    if not s:
        return None
    try:
        dt = parsedate_to_datetime(s)
    except Exception:
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=BRT)
    return dt


# ---------------------------------------------------------------- consultas Google Notícias
def gnews_url(q: str) -> str:
    return ("https://news.google.com/rss/search?q=" + urllib.parse.quote(q + " when:2d")
            + "&hl=pt-BR&gl=BR&ceid=BR:pt-419")


CONSULTAS_TEMA = [
    "chuva eleição", "chuva votação", "temporal votação", "tempestade eleição", "alagamento seção eleitoral",
    "alagamento local de votação", "local de votação transferido chuva", "chuva abstenção",
    "chuva segundo turno", "TRE chuva local de votação", "eleitores chuva urnas", "Defesa Civil eleição chuva",
    "INMET alerta eleição", "chuva eleitores fila", "chuva comparecimento eleição",
]
CIDADES_CONSULTA = ["São Paulo", "Rio de Janeiro", "Guarulhos", "Campinas", "Curitiba", "Campo Grande",
                    "Baixada Fluminense", "Duque de Caxias", "ABC", "Santos", "São José dos Campos",
                    "Florianópolis", "Joinville", "Porto Alegre", "Belo Horizonte", "Londrina", "Sorocaba",
                    "Osasco", "Nova Iguaçu", "São Gonçalo", "Niterói", "rio Uruguai"]


def montar_consultas(portais: list[dict]) -> list[tuple[str, str]]:
    cs = [(f"gnews:{q}", gnews_url(q)) for q in CONSULTAS_TEMA]
    for c in CIDADES_CONSULTA:
        cs.append((f"gnews:{c}", gnews_url(f'(chuva OR temporal OR alagamento) (eleição OR votação) "{c}"')))
    sem_rss = [p for p in portais if not p.get("rss_url")]
    for p in sem_rss:
        dom = p["dominio"].split("/")[0]
        cs.append((f"gnews:site:{dom}", gnews_url(f"(chuva OR temporal OR alagamento OR tempestade) site:{dom}")))
    return cs


# ---------------------------------------------------------------- classificação
def tem(t: str, termos) -> list[str]:
    return [k for k in termos if k in t]


def detectar_local(texto_n: str, cidades: dict, portal: dict | None) -> tuple[str, str]:
    achados = []
    for k, (nome, uf) in cidades.items():
        if re.search(r"(?<![a-z])" + re.escape(k) + r"(?![a-z])", texto_n):
            achados.append((len(k), nome, uf))
    if achados:
        achados.sort(reverse=True)
        nomes = []
        for _, nome, uf in achados:
            if nome not in [n for n, _ in nomes]:
                nomes.append((nome, uf))
        cidade = "; ".join(n for n, _ in nomes[:3])
        ufs = sorted({u for _, u in nomes[:3]})
        return cidade, "/".join(ufs)
    for nome_uf, uf in UF_NOME.items():
        if nome_uf in texto_n:
            return "", uf
    m = re.search(r"\b(sp|rj|pr|ms|sc|rs|mg)\b", texto_n)
    if m:
        return "", m.group(1).upper()
    if portal and portal.get("abrangencia") == "regional" and portal.get("uf"):
        return "", portal["uf"]
    return "", ""


def classificar_tema(t: str) -> str:
    for nome, termos in TEMAS:
        if tem(t, termos):
            return nome
    return "geral"


def achar_portal(item: dict, portais: list[dict], portal_feed: dict | None) -> dict | None:
    if portal_feed:
        return portal_feed
    cand = item.get("fonte_url") or item.get("link") or ""
    host = urllib.parse.urlparse(cand).netloc.replace("www.", "").replace("www1.", "")
    # prefere o domínio mais específico (ex.: g1.globo.com/pr/parana); por URL de fonte só há host
    melhores = [p for p in portais if p["dominio"].split("/")[0] == host or host.endswith("." + p["dominio"].split("/")[0])]
    if melhores:
        link = item.get("link", "")
        for p in sorted(melhores, key=lambda p: -len(p["dominio"])):
            if "/" not in p["dominio"] or p["dominio"] in link:
                return p
        return [p for p in melhores if "/" not in p["dominio"]][0] if any("/" not in p["dominio"] for p in melhores) else melhores[0]
    return None


def processar(item: dict, origem: str, portal_feed: dict | None, portais, cidades, altas, coletado) -> dict | None:
    titulo = item["titulo"]
    if not titulo or not item["link"]:
        return None
    dt = parse_data(item["pub"])
    if dt is None or not (INICIO_JANELA <= dt < FIM_JANELA):
        return None
    portal = achar_portal(item, portais, portal_feed)
    nome_portal = portal["nome"] if portal else (item.get("fonte_nome") or
                                                  urllib.parse.urlparse(item.get("fonte_url", "")).netloc or "?")
    # Google Notícias põe " - Fonte" no fim do título
    if item.get("fonte_nome") and titulo.endswith(" - " + item["fonte_nome"]):
        titulo = titulo[: -len(" - " + item["fonte_nome"])].strip()
    texto = norm(titulo + " " + item.get("desc", ""))
    t_tit = norm(titulo)
    k_chuva, k_forte, k_ele = tem(texto, CHUVA), tem(texto, CHUVA_FORTE), tem(texto, ELEICAO)
    cidade, uf = detectar_local(texto, cidades, portal)
    em_area_alta = any(c.strip() in altas for c in cidade.split(";")) if cidade else False
    hoje = dt.astimezone(BRT).date() == DIA
    # Relevância: chuva + eleição; ou chuva forte em área sinalizada publicada hoje (contexto do dia)
    if not k_chuva:
        return None
    if not k_ele and not (k_forte and hoje and (em_area_alta or uf in {"SP", "RJ", "PR", "MS", "SC", "RS", "MG"})):
        return None
    if not k_ele and not hoje:
        return None
    tema = classificar_tema(texto)
    score = 0.0
    score += 3 if k_ele else 0
    score += 2 if tem(t_tit, CHUVA) else 1
    score += 1.5 if tem(t_tit, ELEICAO) else 0
    score += {"locais de votação": 2.5, "abstenção": 2.5, "alagamento": 1.5, "mobilidade": 1, "alerta": 1}.get(tema, 0)
    score += 1.5 if em_area_alta else (0.5 if uf else 0)
    score += 1 if portal else 0
    horas = max(0.0, (coletado - dt.astimezone(UTC)).total_seconds() / 3600)
    score += max(0.0, 2 - horas / 6)  # recência: até +2
    flags = []
    if not portal:
        flags.append("fonte fora da lista verificada")
    if tem(texto, SUSPEITO):
        flags.append("alegação a checar com TSE/TRE (possível contradição com fontes oficiais)")
        score -= 3
    if not hoje:
        flags.append("publicado em 24/10 (véspera)")
    return {
        "titulo": titulo, "link": item["link"], "portal": nome_portal,
        "dominio": portal["dominio"] if portal else urllib.parse.urlparse(item.get("fonte_url") or item["link"]).netloc,
        "abrangencia": portal["abrangencia"] if portal else "outro",
        "uf": uf, "cidade": cidade, "regiao": "/".join(sorted({REGIAO_UF.get(u, "") for u in uf.split("/") if u})) if uf else "",
        "tema": tema,
        "publicado_brt": dt.astimezone(BRT).strftime("%Y-%m-%d %H:%M"),
        "publicado_utc": dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "coletado_utc": coletado.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "score": round(score, 2), "sinalizacao": "; ".join(flags),
        "menciona_eleicao": "sim" if k_ele else "não", "origem_coleta": origem,
        "resumo": item.get("desc", "")[:300] if norm(item.get("desc", ""))[:60] != t_tit[:60] else "",
    }


def chave_titulo(t: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", norm(t))


def deduplicar(itens: list[dict]) -> list[dict]:
    """Remove duplicatas por URL e por título muito parecido; mantém a versão de maior score
    e prefere link direto do portal (RSS) a link do Google Notícias."""
    def pref(x):
        return (0 if "news.google.com" in x["link"] else 1, x["score"])
    itens = sorted(itens, key=pref, reverse=True)
    vistos_url, mantidos = set(), []
    for it in itens:
        u = it["link"].split("?")[0].rstrip("/")
        if u in vistos_url:
            continue
        k = chave_titulo(it["titulo"])
        dup = False
        for m in mantidos:
            if difflib.SequenceMatcher(None, k, m["_k"]).ratio() >= 0.85:
                dup = True
                break
        if dup:
            continue
        vistos_url.add(u)
        it["_k"] = k
        mantidos.append(it)
    for m in mantidos:
        m.pop("_k", None)
    return mantidos


# ---------------------------------------------------------------- execução
def coletar(usar_gnews: bool = True, workers: int = 12) -> tuple[list[dict], list[dict], datetime]:
    coletado = datetime.now(UTC).replace(microsecond=0)
    portais = carregar_portais()
    cidades, altas = carregar_cidades()
    tarefas = [(f"rss:{p['nome']}", p["rss_url"], p) for p in portais if p.get("rss_url")]
    if usar_gnews:
        tarefas += [(o, u, None) for o, u in montar_consultas(portais)]
    log, brutos = [], []

    def job(t):
        origem, url, p = t
        try:
            itens = parse_feed(baixar(url))
            return origem, url, p, itens, ""
        except Exception as e:  # noqa: BLE001
            return origem, url, p, [], f"{type(e).__name__}: {str(e)[:120]}"

    with cf.ThreadPoolExecutor(workers) as ex:
        for origem, url, p, itens, err in ex.map(job, tarefas):
            mantidos = 0
            for it in itens:
                r = processar(it, origem, p, portais, cidades, altas, coletado)
                if r:
                    brutos.append(r)
                    mantidos += 1
            log.append({"origem": origem, "url": url, "itens_lidos": len(itens), "relevantes": mantidos,
                        "erro": err})
    return deduplicar(brutos), log, coletado


def ler_csv(p: Path) -> list[dict]:
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def gravar_csv(p: Path, linhas: list[dict]):
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows(linhas)


def ordenar(linhas):
    return sorted(linhas, key=lambda r: (-float(r["score"]), r["publicado_utc"]), reverse=False)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--sem-gnews", action="store_true", help="usar só os feeds RSS dos portais")
    ap.add_argument("--max-workers", type=int, default=12)
    a = ap.parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    novos, log, coletado = coletar(not a.sem_gnews, a.max_workers)
    stamp = coletado.strftime("%Y%m%d_%H%M")
    for i, r in enumerate(novos):
        r["id"] = f"{stamp}-{i:03d}"
    novos = ordenar(novos)
    gravar_csv(OUT / f"noticias_{stamp}UTC.csv", novos)

    # consolidado: une com coletas anteriores; o item mais recente coletado atualiza o score
    antigos = ler_csv(OUT / "noticias_consolidado.csv")
    for r in antigos:
        r["score"] = float(r.get("score") or 0)
    cons = deduplicar(novos + [r for r in antigos if r.get("link")])
    # recalcula componente de recência para todos (score salvo já tem recência do momento da coleta)
    cons = ordenar(cons)
    gravar_csv(OUT / "noticias_consolidado.csv", cons)

    with (OUT / "log_coleta.csv").open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["coletado_utc", "origem", "url", "itens_lidos", "relevantes", "erro"])
        if f.tell() == 0:
            w.writeheader()
        for l in log:
            w.writerow({"coletado_utc": coletado.strftime("%Y-%m-%dT%H:%M:%SZ"), **l})
    escrever_resumo(cons, novos, log, coletado)
    falhas = [l for l in log if l["erro"]]
    print(f"Coleta {coletado:%Y-%m-%d %H:%M} UTC: {len(log)} fontes consultadas, {len(falhas)} falhas; "
          f"{len(novos)} notícias nesta coleta; {len(cons)} no consolidado.")
    for l in falhas:
        print("  FALHA", l["origem"], l["erro"])
    return 0


def escrever_resumo(cons, novos, log, coletado):
    brt = coletado.astimezone(BRT)
    ok = [r for r in cons if not r.get("sinalizacao") or r["sinalizacao"].startswith("publicado em 24/10")]
    top = ok[:10]
    falhas = [l for l in log if l["erro"]]
    vazios_rss = [l for l in log if l["origem"].startswith("rss:") and not l["erro"] and l["relevantes"] == 0]
    from collections import Counter
    temas = Counter(r["tema"] for r in cons)
    ufs = Counter(u for r in cons for u in (r["uf"] or "n/d").split("/"))
    L = [f"# Monitoramento de notícias — chuva × eleição (2º turno, 25/10/2026)",
         "", f"**Coleta:** {coletado:%Y-%m-%d %H:%M} UTC ({brt:%H:%M} BRT) · **Notícias no consolidado:** {len(cons)} "
         f"(nesta coleta: {len(novos)}) · **Fontes consultadas:** {len(log)} (falhas: {len(falhas)})", "",
         "Fontes: feeds RSS verificados dos portais em `portais.csv` + Google Notícias RSS (pt-BR). "
         "Só entram itens realmente baixados, publicados em 25/10 (ou a partir de 24/10 18h BRT), "
         "que citam chuva/tempo severo **e** eleição — ou chuva forte em área sinalizada no dia da eleição.", "",
         "## Principais notícias agora", ""]
    for r in top:
        L.append(f"- **{r['titulo']}** — {r['portal']} ({r['publicado_brt'][11:]} BRT"
                 f"{', ' + r['cidade'] if r['cidade'] else ''}{'/' + r['uf'] if r['uf'] and not r['cidade'] else ''}"
                 f"; tema: {r['tema']}) — [link]({r['link']})")
    L += ["", "## Distribuição", "", "Por tema: " + ", ".join(f"{k} {v}" for k, v in temas.most_common()),
          "", "Por UF: " + ", ".join(f"{k} {v}" for k, v in ufs.most_common()), ""]
    flag = [r for r in cons if r.get("sinalizacao") and not r["sinalizacao"].startswith("publicado em 24/10")]
    if flag:
        L += ["## Itens sinalizados (não verificados ou a checar)", ""]
        for r in flag[:15]:
            L.append(f"- {r['titulo']} — {r['portal']} — _{r['sinalizacao']}_ — [link]({r['link']})")
        L.append("")
    L += ["## Limitações", "",
          "- Links do Google Notícias passam por redirecionamento (news.google.com) antes do portal original.",
          "- Vários portais têm paywall (Folha, Estadão, O Globo, Gazeta do Povo, GZH): o título é público, o texto pode não ser.",
          "- Horário = data de publicação informada pelo feed; alguns portais atualizam matérias sem mudar a data.",
          "- Classificação de tema, cidade e UF é automática por palavras-chave e pode errar.",
          "- Notícia não é dado oficial de comparecimento: o número oficial de abstenção só sai na totalização do TSE.",
          ""]
    if falhas or vazios_rss:
        L += ["### Fontes com falha nesta coleta", ""]
        for l in falhas:
            L.append(f"- {l['origem']}: {l['erro']}")
        L.append("")
    (OUT / "resumo_noticias.md").write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
