"""Leitura da comparação pós-eleição (resultado oficial do 2º turno x estimativa de 17:09 BRT).

Fonte única para o site e o dashboard: data/resultado_2turno/ (gerado por scripts/pos_eleicao/).
Este módulo só lê e formata; não recalcula estatísticas.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DIR = REPO_ROOT / "data" / "resultado_2turno"
CSV = "comparacao_municipios_2turno.csv"
REPO = "https://github.com/andersonsoaresdev2025/chuva-abstencao-2turno-2026"
BLOB = f"{REPO}/blob/main/data/resultado_2turno"
TREE = f"{REPO}/tree/main/data/resultado_2turno"
RAW = "https://raw.githubusercontent.com/andersonsoaresdev2025/chuva-abstencao-2turno-2026/main/data/resultado_2turno"
SITE_PAGINA = "resultado_2turno.html"

LINKS = {
    "Conclusão (CONCLUSAO.md)": f"{BLOB}/CONCLUSAO.md",
    "Relatório completo (Markdown)": f"{BLOB}/comparacao_municipios_2turno.md",
    "Relatório completo (PDF)": f"{RAW}/comparacao_municipios_2turno.pdf",
    "Dados por município (CSV, 304 linhas)": f"{RAW}/comparacao_municipios_2turno.csv",
    "Números-chave (resumo.json)": f"{BLOB}/resumo.json",
    "Pasta com todos os arquivos e dados brutos do TSE": TREE,
}

FAIXAS = [(0, 1, "0 a 1 mm"), (1, 5, "1 a 5 mm"), (5, 15, "5 a 15 mm"), (15, 30, "15 a 30 mm"), (30, float("inf"), "30 mm ou mais")]


def carregar_csv(base: Path | None = None) -> pd.DataFrame:
    return pd.read_csv((base or DIR) / CSV, encoding="utf-8")


def carregar_resumo(base: Path | None = None) -> dict:
    return json.loads(((base or DIR) / "resumo.json").read_text(encoding="utf-8"))


def carregar_conclusao(base: Path | None = None, links_absolutos: bool = True) -> str:
    """CONCLUSAO.md; links relativos viram links do GitHub (para uso fora do repositório)."""
    txt = ((base or DIR) / "CONCLUSAO.md").read_text(encoding="utf-8")
    if links_absolutos:
        txt = re.sub(r"\]\((?!https?://)([^)]+)\)", lambda m: f"]({BLOB}/{m.group(1)})", txt)
    return txt


def faixa_chuva(mm: float) -> str:
    for lo, hi, rot in FAIXAS:
        if lo <= mm < hi:
            return rot
    return FAIXAS[-1][2]


def br(x, nd: int = 2, sinal: bool = False) -> str:
    """Número no formato pt-BR (vírgula decimal, ponto de milhar, sinal de menos tipográfico)."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "n/d"
    s = f"{abs(x):,.{nd}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if x < 0 and s.strip("0,.") != "":
        return "−" + s
    return ("+" + s) if sinal and x > 0 else s


def inclinacao(resumo: dict, amostra: str = "todos", modelo: str = "simples", ponderado: bool = False) -> dict:
    for i in resumo["inclinacoes_pp_por_10mm"]:
        if i["amostra"] == amostra and i["modelo"] == modelo and i["ponderado"] == ponderado:
            return i
    raise KeyError((amostra, modelo, ponderado))


def numeros_chave(resumo: dict) -> list[tuple[str, str, str]]:
    """(rótulo, valor, detalhe) para os cartões do site e do dashboard."""
    r = resumo
    s, w = inclinacao(r), inclinacao(r, ponderado=True)
    ci = r["coef_implicito_simples"]
    ab, ex = r["estimativa_abst_nacional_pp"], r["estimativa_abst_extras"]
    return [
        ("Abstenção nacional (TSE)", f"{br(r['abst_nacional_pct_1t'])}% → {br(r['abst_nacional_pct_2t'])}%",
         f"1º → 2º turno ({br(r['abst_nacional_pct_2t'] - r['abst_nacional_pct_1t'], 2, True)} p.p.)"),
        ("Estimativa final (17:09 BRT)", f"{br(ab['mid'], 2, True)} p.p.",
         f"{br(ex['mid'], 0)} abstenções extras (faixa {br(ex['min'], 0)} a {br(ex['max'], 0)})"),
        ("Observado acima da média da UF", f"{br(r['soma_abst_acima_media_uf'], 0)}",
         f"eleitores, soma dos {r['n_municipios']} municípios cobertos"),
        ("Inclinação sem peso", f"{br(s['b'], 2, True)} p.p. / 10 mm",
         f"IC 95% {br(s['lo'], 2, True)} a {br(s['hi'], 2, True)}: direção compatível com o modelo"),
        ("Coeficiente implícito", f"{br(ci['b'], 3)} p.p./mm",
         f"contra {br(r['coef_bot1_pp_por_mm'], 2)} usado ({br(100 * ci['b'] / r['coef_bot1_pp_por_mm'], 0)}%): cerca de um terço"),
        ("Inclinação com peso (eleitorado)", f"{br(w['b'], 2, True)} p.p. / 10 mm",
         f"IC 95% {br(w['lo'], 2, True)} a {br(w['hi'], 2, True)}: não se distingue de zero"),
    ]


def _inline_html(t: str) -> str:
    import html as _h
    t = _h.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![*\w])\*([^*]+)\*(?![*\w])", r"<i>\1</i>", t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", lambda m: f'<a href="{_h.escape(m.group(2), quote=True)}">{m.group(1)}</a>', t)
    return t


def md_para_html(md: str, nivel_base: int = 2) -> str:
    """Conversor mínimo de Markdown (títulos, parágrafos, listas, citações, negrito, itálico, código, links)
    usado para publicar CONCLUSAO.md no site sem dependências extras."""
    out, lista, par = [], None, []

    def fecha_par():
        if par:
            out.append("<p>" + _inline_html(" ".join(par)) + "</p>")
            par.clear()

    def fecha_lista():
        nonlocal lista
        if lista:
            out.append(f"</{lista}>")
            lista = None

    for linha in md.splitlines():
        s = linha.strip()
        if not s:
            fecha_par()
            fecha_lista()
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            fecha_par()
            fecha_lista()
            n = min(6, len(m.group(1)) - 1 + nivel_base)
            out.append(f"<h{n}>{_inline_html(m.group(2))}</h{n}>")
            continue
        if s.startswith(">"):
            fecha_par()
            fecha_lista()
            out.append('<p class="alert">' + _inline_html(s.lstrip("> ").strip()) + "</p>")
            continue
        mo, mu = re.match(r"^\d+\.\s+(.*)$", s), re.match(r"^[-*]\s+(.*)$", s)
        if mo or mu:
            fecha_par()
            tipo = "ol" if mo else "ul"
            if lista != tipo:
                fecha_lista()
                out.append(f"<{tipo}>")
                lista = tipo
            out.append("<li>" + _inline_html((mo or mu).group(1)) + "</li>")
            continue
        if lista:
            out[-1] = out[-1][:-5] + " " + _inline_html(s) + "</li>"
            continue
        par.append(s)
    fecha_par()
    fecha_lista()
    return "\n".join(out)
