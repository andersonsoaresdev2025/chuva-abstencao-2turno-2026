#!/usr/bin/env python3
"""
Gera o site estático (GitHub Pages) em docs/index.html a partir dos CSVs de data/.

Uso:  python scripts/build_site.py
Reexecute após cada atualização de dados (scripts/update_and_publish.sh faz isso).
Nenhum número é inventado: tudo vem dos CSVs; só há formatação e aritmética simples
(somas e aptos × pp / 100), sempre identificada.
"""
from __future__ import annotations

import html
import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from common import dados as D  # noqa: E402
from common import impacto_agora as IA  # noqa: E402
from common import noticias as NOTI  # noqa: E402

# ---------------------------------------------------------------------------
# PREENCHER APÓS A PUBLICAÇÃO (ou exportar as variáveis de ambiente)
# ---------------------------------------------------------------------------
STREAMLIT_URL = os.environ.get("STREAMLIT_URL", "https://chuva-abstencao-2026.streamlit.app/")
REPO_URL = os.environ.get("REPO_URL", "https://github.com/andersonsoaresdev2025/chuva-abstencao-2turno-2026")

OUT = ROOT / "docs" / "index.html"
COR = {"torrencial": "#c0392b", "moderada": "#e67e22", "sem_chuva_relevante": "#27ae60"}


def esc(x) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "—"
    return html.escape(str(x))


def num(x, casas=0) -> str:
    try:
        if pd.isna(x):
            return "—"
        s = f"{float(x):,.{casas}f}"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return esc(x)


def badge(nivel) -> str:
    k = D.nivel_curto(nivel)
    letra = {"torrencial": "a", "moderada": "b", "sem_chuva_relevante": "c"}[k]
    return (f'<span class="badge" style="background:{COR[k]}" title="{esc(D.ROTULO_RISCO[k])}">'
            f'{letra}</span> {esc(nivel)}')


def link_seguro(url) -> str:
    u = "" if url is None or (isinstance(url, float) and pd.isna(url)) else str(url).strip()
    if u.startswith("http://") or u.startswith("https://"):
        return f'<a href="{html.escape(u, quote=True)}" target="_blank" rel="noopener nofollow">fonte</a>'
    return "—"


def table(df: pd.DataFrame, cols: list[tuple[str, str, callable]], caption: str = "") -> str:
    if df.empty:
        return '<p class="muted">Dados não disponíveis.</p>'
    head = "".join(f"<th>{esc(t)}</th>" for _, t, _ in cols if _ is not None or True)
    rows = []
    for _, r in df.iterrows():
        tds = []
        for c, _t, f in cols:
            v = r[c] if c in r.index else None
            tds.append(f"<td>{f(v) if f else esc(v)}</td>")
        rows.append("<tr>" + "".join(tds) + "</tr>")
    cap = f"<caption>{caption}</caption>" if caption else ""
    return f'<div class="tw"><table>{cap}<thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def faixa(r) -> str:
    return f"+{num(r['efeito_abstencao_pp_mid'], 2)} ({num(r['efeito_abstencao_pp_lo'], 1)} a {num(r['efeito_abstencao_pp_hi'], 1)})"


def ordenar_risco(df, col, extra=None, asc_extra=False):
    df = df.copy()
    df["_o"] = df[col].map(D.nivel_curto).map(D.ORDEM_RISCO)
    by, asc = ["_o"], [True]
    if extra:
        by.append(extra)
        asc.append(asc_extra)
    return df.sort_values(by, ascending=asc)


def secao_social() -> str:
    soc = D.carregar_social()
    nome_md, _ = D.ultimo_resumo_social()
    if soc.empty:
        return ('<p class="muted">Ainda não há sinais sociais publicados (pasta <code>data/social/</code> '
                'vazia ou ausente). Esta seção é preenchida automaticamente quando o monitoramento grava '
                '<code>sinais_*.csv</code>.</p>')
    top = soc.head(20)
    t = table(top, [
        ("timestamp_post", "Post", None), ("rede", "Rede", None), ("cidade", "Cidade", None), ("uf", "UF", None),
        ("tipo", "Tipo", None), ("nivel_risco_implicito", "Risco implícito", badge),
        ("confianca", "Confiança", None), ("fonte", "Fonte", None), ("tipo_fonte", "Tipo de fonte", None),
        ("resumo", "Resumo", None), ("link", "Link", link_seguro)],
        caption=f"{len(soc)} sinais no total; 20 mais recentes. Último coletado: "
                f"{esc(soc['timestamp_coleta_utc'].dropna().astype(str).max() if soc['timestamp_coleta_utc'].notna().any() else '—')}")
    extra = f'<p class="muted">Resumo mais recente: <code>data/social/{esc(nome_md)}</code></p>' if nome_md else ""
    return t + extra


def secao_noticias(n: int = 8) -> str:
    """Top notícias (chuva × eleição) dos portais verificados; ver data/noticias/."""
    df = NOTI.carregar_noticias()
    portais = NOTI.carregar_portais()
    if df.empty:
        return ('<section id="noticias"><h2>Principais notícias: chuva × eleição</h2><p class="muted">Ainda não há '
                'notícias coletadas (<code>data/noticias/</code>).</p></section>')
    top = NOTI.principais(df, n)
    itens = []
    for _, r in top.iterrows():
        u = str(r["link"])
        href = html.escape(u, quote=True) if u.startswith(("http://", "https://")) else "#"
        local = " · ".join(x for x in [str(r["cidade"] or ""), str(r["uf"] or "")] if x)
        dia = "" if str(r["publicado_brt"]).startswith("2026-10-25") else " (24/10)"
        itens.append(f'<li><a href="{href}" target="_blank" rel="noopener nofollow">{esc(r["titulo"])}</a> '
                     f'<span class="muted">— {esc(r["portal"])} · {esc(str(r["publicado_brt"])[11:16])} BRT{dia}'
                     f'{" · " + esc(local) if local else ""} · {esc(r["tema"])}</span></li>')
    n_nac = int((portais["abrangencia"] == "nacional").sum()) if not portais.empty else 0
    n_reg = int((portais["abrangencia"] == "regional").sum()) if not portais.empty else 0
    return f"""<section id="noticias">
<h2>📰 Principais notícias: chuva × eleição</h2>
<p class="muted">Coleta: {esc(NOTI.ultima_coleta(df))} · {len(df)} notícias monitoradas · {n_nac} portais nacionais e {n_reg} locais verificados (lista em <code>data/noticias/portais.csv</code>) + Google Notícias. Lista completa e filtros no <a href="{html.escape(STREAMLIT_URL, quote=True)}">dashboard</a> (página Notícias).</p>
<ol>{''.join(itens)}</ol>
<p class="alert">{esc(NOTI.DISCLAIMER.replace('**', ''))}</p>
</section>"""


def secao_ajustes() -> str:
    aj = D.carregar_ajustes()
    if aj.empty:
        return ('<section id="ajustes"><h2>📰 Ajustes por notícias</h2><p class="muted">Nenhum <b>ajuste por notícias</b> '
                'ativo no momento (data/ajustes/ajustes_impacto_noticias.csv, revisado a cada 30 min). As estimativas usam só a '
                'previsão.</p></section>')

    def fontes(v):
        us = [u.strip() for u in str(v or "").replace(";", " ").replace(",", " ").split() if u.strip().startswith("http")]
        return " ".join(link_seguro(u) for u in us) or "—"
    t = table(aj, [("timestamp_brt", "Registrado (BRT)", None), ("municipio", "Município", None), ("uf", "UF", None),
                   ("nivel_risco_ajustado", "Nível (ajuste por notícias)", badge),
                   ("intensidade_estimada_mm", "mm estimados", None), ("evidencia", "Evidência", None),
                   ("confianca", "Confiança", None), ("fontes", "Fontes", fontes)])
    return (f'<section id="ajustes"><h2>📰 Ajustes por notícias ({len(aj)} ativos)</h2><p class="muted">Rótulo '
            '"ajuste por notícias": nível mínimo de risco por município com base em reportagens/relatos; o nível usado é o '
            'maior entre previsão e ajuste. Confira as fontes.</p>' + t + '</section>')


def secao_mudancas(rm: pd.DataFrame, ru: pd.DataFrame, ts_r: str) -> str:
    if "mudanca_vs_manha" not in rm.columns:
        return ""
    b2 = rm[rm["nivel_risco_manha_bot2"].notna()]
    mud = b2[b2["mudanca_vs_manha"] != "igual"]
    ufm = ru[ru["nivel_risco_manha_bot2"].notna() & (ru["mudanca_vs_manha"] != "igual")] if "mudanca_vs_manha" in ru.columns else ru.iloc[0:0]
    t = table(mud, [("municipio", "Município", None), ("uf", "UF", None), ("nivel_risco_manha_bot2", "Manhã (Bot 2)", badge),
                    ("precip_manha_bot2_mm", "mm manhã", lambda v: num(v, 1)), ("nivel_risco", "Agora", badge),
                    ("precipitacao_mm_estimada", "mm 08–17h agora", lambda v: num(v, 1)),
                    ("mudanca_vs_manha", "Mudança", None), ("alerta_inmet", "Alerta INMET", None),
                    ("ajuste_noticias", "Ajuste por notícias", None)]) if not mud.empty else         '<p class="muted">Nenhum dos municípios do Bot 2 mudou de nível.</p>'
    u = (" · ".join(f"{esc(r['uf'])}: {esc(r['mudanca_vs_manha'])}" for _, r in ufm.iterrows()) or "nenhum")
    return (f'<h3>🔄 O que mudou desde a manhã (Bot 2, 06:35 BRT → {esc(ts_r)})</h3>'
            f'<p class="muted">{len(mud)} de {len(b2)} municípios do Bot 2 mudaram; estados com mudança: {u}.</p>' + t)


def pp(x: float) -> str:
    casas = 4 if abs(x) < 0.01 else 2
    return f"{x:+.{casas}f}".replace("-", "−").replace(".", ",")


def secao_agora() -> str:
    """Card 'Impacto estimado agora' (só previsão vs previsão + notícias) calculado no build."""
    try:
        duplo = IA.calcular_duplo()
    except Exception as e:  # noqa: BLE001
        return (f'<section id="agora"><h2>Impacto estimado agora</h2><p class="muted">Indisponível neste build '
                f'({esc(type(e).__name__)}).</p></section>')
    r, rn, n_aj = duplo["previsao"], duplo["previsao_mais_noticias"], duplo["n_ajustes_ativos"]
    f, l, m = r["flavio_pp"], r["lula_pp"], r["margem_lula_menos_flavio_pp"]
    vf, vl, ab = r["votos_perdidos_flavio"], r["votos_perdidos_lula"], r["abstencao_nacional_pp"]

    def noti(chave, extra=""):
        if not n_aj:
            return '<br><span class="muted">Previsão + notícias: igual (nenhum ajuste ativo)</span>'
        return f'<br><span class="muted"><b>Previsão + notícias:</b> {pp(rn[chave]["mid"])} p.p.{extra}</span>'
    fb = ('<p class="alert">Open-Meteo indisponível no build: usada a previsão do Bot 0 (CSV) pró-rata.</p>'
          if r["usou_fallback"] else "")
    return f"""<section id="agora">
<h2>⏱️ Impacto estimado agora — {esc(r['rotulo'])}</h2>
<div class="kpis">
<div class="kpi"><b>{pp(f['mid'])} p.p.</b>Flávio Bolsonaro (votos válidos) · só previsão · faixa {pp(f['min'])} a {pp(f['max'])} · votos perdidos ≈ {num(round(vf['mid'], -2))} ({num(round(vf['min'], -2))}–{num(round(vf['max'], -2))}){noti('flavio_pp', ' · votos perdidos ≈ ' + num(round(rn['votos_perdidos_flavio']['mid'], -2)))}</div>
<div class="kpi"><b>{pp(l['mid'])} p.p.</b>Lula (votos válidos) · só previsão · faixa {pp(l['min'])} a {pp(l['max'])} · votos perdidos ≈ {num(round(vl['mid'], -2))} ({num(round(vl['min'], -2))}–{num(round(vl['max'], -2))}){noti('lula_pp', ' · votos perdidos ≈ ' + num(round(rn['votos_perdidos_lula']['mid'], -2)))}</div>
<div class="kpi"><b>{pp(m['mid'])} p.p.</b>Efeito na margem (Lula − Flávio) · só previsão · faixa {pp(m['min'])} a {pp(m['max'])} · abstenção nacional {pp(ab['mid'])} p.p.{noti('margem_lula_menos_flavio_pp')}</div>
<div class="kpi"><b>{num(r['cobertura_pct_eleitorado'], 1)}%</b>do eleitorado coberto ({r['n_municipios_cobertos']} maiores colégios; demais = 0){' · ' + str(n_aj) + ' ajuste(s) por notícias' if n_aj else ''}</div>
</div>
<p class="muted">🕒 Calculado em {esc(r['calculado_em_brt'])} ({esc(r['calculado_em_utc'])}) no momento da geração desta página; janela: {'dia inteiro 08h–17h (previsão)' if r['modo'] == 'projecao' else num(r['horas_decorridas'], 1) + ' h desde 08h'} · Precipitação: {esc(r['fonte_precipitacao'])}. Versão interativa no <a href="{html.escape(STREAMLIT_URL, quote=True)}">dashboard</a>.</p>
{fb}
<p class="muted"><b>Como é calculado:</b> {esc(IA.METODO_TXT)}</p>
<p class="alert">{esc(IA.DISCLAIMER.replace('**', ''))}</p>
</section>"""


def build() -> str:
    d = D.carregar_tudo()
    ts = D.timestamps_dados(d)
    im, iu, ir = d["impacto_mun"], d["impacto_uf"], d["impacto_reg"]
    rm, ru, rr = d["risco_mun"], d["risco_uf"], d["risco_reg"]
    red_reg, red_mun = d["redutos_reg"], d["redutos_mun"]

    # ----- KPIs (contagens/somas diretas dos CSVs)
    n_alta = int((im["vulnerabilidade"] == "Alta").sum()) if not im.empty else 0
    n_media = int((im["vulnerabilidade"] == "Média").sum()) if not im.empty else 0
    aptos_a_bot4 = int(im.loc[im["nivel_risco"].map(D.nivel_curto) == "torrencial", "aptos"].sum()) if not im.empty else 0
    n_a_bot2 = int((rm["nivel_risco"].map(D.nivel_curto) == "torrencial").sum()) if not rm.empty else 0

    # ----- Panorama nacional (somas de redutos_regioes)
    pan = ""
    if not red_reg.empty:
        vf, vl, vv = red_reg["votos_flavio"].sum(), red_reg["votos_lula"].sum(), red_reg["votos_validos"].sum()
        apt, abst = red_reg["aptos"].sum(), red_reg["abstencao"].sum()
        pan = (f"<p>1º turno (TSE, soma das regiões, sem exterior): Flávio Bolsonaro <b>{num(100*vf/vv, 2)}%</b> "
               f"× Lula <b>{num(100*vl/vv, 2)}%</b> dos votos válidos; abstenção <b>{num(100*abst/apt, 2)}%</b> "
               f"de {num(apt)} aptos.</p>")

    # ----- Impacto municipal com ordem de grandeza em votos
    imx = im.copy()
    if not imx.empty:
        imx = imx.sort_values(["efeito_abstencao_pp_mid", "aptos"], ascending=False).head(80)
        imx["faixa"] = imx.apply(faixa, axis=1)
        imx["votos"] = imx.apply(
            lambda r: f"{num(round(r['aptos']*r['efeito_abstencao_pp_lo']/100, -2))} a "
                      f"{num(round(r['aptos']*r['efeito_abstencao_pp_hi']/100, -2))}", axis=1)
    iux = iu.copy()
    if not iux.empty:
        iux = iux.sort_values(["efeito_abstencao_pp_mid", "peso_eleitoral_pct"], ascending=False)
        iux["faixa"] = iux.apply(faixa, axis=1)
    irx = ir.copy()
    if not irx.empty:
        irx["faixa"] = irx.apply(faixa, axis=1)

    top_col = red_mun.sort_values("aptos", ascending=False).head(15) if not red_mun.empty else red_mun

    social_html = secao_social()
    og = d.get("_origem", {})
    auto = og.get("risco_mun") == "atualizado"
    ts_r, ts_i = D.ts_camada(d, "risco"), D.ts_camada(d, "impacto")
    st_cl = D.status_atualizacao().get("clima", {})
    fontes_ok = ""
    if st_cl:
        om, inm = st_cl.get("open_meteo", {}), st_cl.get("inmet", {})
        fontes_ok = f"Open-Meteo: {esc(om.get('status'))} · INMET: {esc(inm.get('status'))}"
        if om.get("status") != "ok" or inm.get("status") != "ok":
            fontes_ok += " — fonte com falha: mantido o último dado válido (desatualizado)"
    mudancas_html = secao_mudancas(rm, ru, ts_r) if auto else ""
    rm_site = ordenar_risco(rm, "nivel_risco", "aptos" if "aptos" in rm.columns else "precipitacao_mm_estimada")
    n_rm = len(rm_site)
    rm_site = rm_site.head(80)
    im_site = ordenar_risco(im, "nivel_risco", "aptos").head(80)
    rot_r = "atualização automática, papel do Bot 2" if auto else "Bot 2"
    rot_i = "atualização automática, papel do Bot 4" if og.get("impacto_mun") == "atualizado" else "Bot 4"
    lim = "".join(f"<li>{esc(t)}</li>" for t in D.LIMITACOES)
    ts_html = "".join(f"<tr><td>{esc(k)}</td><td>{esc(v)}</td></tr>" for k, v in ts.items())
    gerado = D.fmt_utc_brt()

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Chuva × Abstenção Eleitoral – 2º Turno 2026</title>
<meta name="description" content="Risco de chuva no horário de votação e impacto estimado na abstenção – 2º turno 25/10/2026. Dados abertos, metodologia e limitações.">
<style>
:root{{--a:#c0392b;--b:#e67e22;--c:#27ae60;--fg:#1d2733;--mut:#5c6b7a;--bg:#f6f8fa;--card:#fff;--line:#e3e8ee}}
*{{box-sizing:border-box}}body{{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:var(--fg);background:var(--bg);line-height:1.5}}
header{{background:#12324f;color:#fff;padding:20px 16px}}header h1{{margin:0 0 4px;font-size:1.5rem}}header p{{margin:4px 0;opacity:.9}}
nav{{position:sticky;top:0;background:#fff;border-bottom:1px solid var(--line);padding:6px 12px;overflow-x:auto;white-space:nowrap;z-index:5}}
nav a{{display:inline-block;margin-right:14px;color:#12324f;text-decoration:none;font-size:.92rem;padding:4px 0}}
main{{max-width:1100px;margin:0 auto;padding:12px}}section{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:14px 0}}
h2{{font-size:1.2rem;margin:0 0 8px}}h3{{font-size:1rem;margin:14px 0 6px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px}}.kpi{{background:var(--bg);border-radius:8px;padding:10px}}.kpi b{{font-size:1.4rem;display:block}}
.tw{{overflow-x:auto;-webkit-overflow-scrolling:touch}}table{{border-collapse:collapse;width:100%;font-size:.86rem}}
th,td{{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}}th{{background:#eef2f6;position:sticky;top:0}}
caption{{caption-side:bottom;text-align:left;color:var(--mut);font-size:.8rem;padding-top:4px}}
.badge{{display:inline-block;color:#fff;border-radius:4px;padding:0 6px;font-weight:700;font-size:.8rem}}
.muted{{color:var(--mut);font-size:.88rem}}.alert{{background:#fff4e5;border-left:4px solid var(--b);padding:10px 12px;border-radius:6px}}
.cta{{display:inline-block;background:#e67e22;color:#fff;padding:8px 14px;border-radius:6px;text-decoration:none;font-weight:600;margin:6px 6px 0 0}}
footer{{text-align:center;color:var(--mut);font-size:.8rem;padding:20px}}
</style>
</head>
<body>
<header>
<h1>🌧️ Chuva × Abstenção Eleitoral</h1>
<p>Segundo turno – 25 de outubro de 2026 · Flávio Bolsonaro × Lula</p>
<p id="atualizado" style="font-size:1.25rem;background:#fff;color:#12324f;display:inline-block;padding:6px 12px;border-radius:8px;margin:8px 0"><b>🕒 Atualizado em {esc(ts_r)}</b></p>
<p><b>Dados atualizados em:</b> risco a/b/c ({rot_r}) {esc(ts_r)} · impacto ({rot_i}) {esc(ts_i)} · ajustes por notícias {esc(ts.get('Ajustes por notícias'))} · página gerada {esc(gerado)}</p>
<p>Atualização automática a cada 30 min (08h–19h BRT). {fontes_ok}</p>
<a class="cta" href="{html.escape(STREAMLIT_URL, quote=True)}" id="streamlit-link">Abrir dashboard interativo</a>
<a class="cta" style="background:#34495e" href="{html.escape(REPO_URL, quote=True)}">Código e dados (GitHub)</a>
</header>
<nav><a href="#agora">Agora</a><a href="#ajustes">Ajustes por notícias</a><a href="#mensagem">Mensagem</a><a href="#risco">Risco</a><a href="#impacto">Impacto</a><a href="#redutos">Redutos</a><a href="#noticias">Notícias</a><a href="#social">Sinais sociais</a><a href="#metodologia">Metodologia</a><a href="#limitacoes">Limitações</a><a href="#fontes">Fontes</a></nav>
<main>

{secao_agora()}

{secao_ajustes()}

{secao_noticias()}

<section id="mensagem">
<h2>Mensagem principal</h2>
<ul>
<li>O <b>Centro-Sul</b> (Região Metropolitana de São Paulo e Rio de Janeiro) concentra o risco de chuva relevante no horário de votação (08h–17h).</li>
<li>Nos locais de risco alto (a), o efeito estimado sobre a abstenção é de <b>+1,2 a +3,0 pontos percentuais</b>; na chuva moderada (b), <b>+0,5 a +1,2 pp</b> (regra prática do Bot 1).</li>
<li>O impacto diferencial entre candidatos é <b>localizado</b>; não há, nesta versão, evidência de viés climático sistemático forte em escala nacional.</li>
<li><b>Nordeste</b> e <b>Norte</b>: tempo firme previsto → baixo impacto climático esperado.</li>
</ul>
<div class="kpis">
<div class="kpi"><b>{n_a_bot2}</b>municípios em risco <span class="badge" style="background:var(--a)">a</span> ({rot_r}, {len(rm)} classificados)</div>
<div class="kpi"><b>{n_alta} / {n_media}</b>municípios com vulnerabilidade Alta / Média ({rot_i}, {len(im)} com previsão horária)</div>
<div class="kpi"><b>{num(aptos_a_bot4)}</b>eleitores aptos nos municípios "torrencial" ({rot_i}, soma)</div>
</div>
<p class="alert">Estimativas com incerteza, para acompanhamento público. <b>Não</b> é previsão eleitoral oficial. Para informações oficiais: TSE, INMET e Defesa Civil.</p>
</section>

<section id="risco">
<h2>Risco de chuva no horário de votação</h2>
<p class="muted">Classificação do projeto: <span class="badge" style="background:var(--a)">a</span> torrencial/tempestade/risco de alagamento (≥ 20–30 mm ou alertas) · <span class="badge" style="background:var(--b)">b</span> moderada (5–20/30 mm) · <span class="badge" style="background:var(--c)">c</span> sem chuva relevante (&lt; 5 mm).</p>
<p class="muted">Regra da atualização automática: chuva na janela 08–17h ≥ 20 mm → a; 5–20 mm → b; &lt; 5 mm → c; aviso INMET laranja/vermelho de chuva/tempestade eleva um nível; ajuste por notícias ativo funciona como piso.</p>
{mudancas_html}
<h3>Por município – classificação a/b/c ({rot_r})</h3>
{table(rm_site, [
    ("municipio", "Município", None), ("uf", "UF", None), ("regiao", "Região", None),
    ("nivel_risco", "Nível", badge), ("precipitacao_mm_estimada", "Precip. est. (mm)", lambda v: num(v, 1)),
    ("horario_pico", "Pico", None), ("probabilidade", "Prob. %", None), ("alerta_inmet", "Alerta INMET", None),
    ("ajuste_noticias", "Ajuste por notícias", None), ("status_dado", "Status", None)],
    caption=f"Fonte: {esc(D.FONTES['risco_auto' if auto else 'risco_bot2'])} · {esc(ts_r)} · {min(n_rm, 80)} de {n_rm} municípios (lista completa em data/clima/atualizacoes/risco_chuva_municipios_latest.csv)")}
<h3>Por município – previsão horária Open-Meteo ({rot_i})</h3>
{table(im_site, [
    ("municipio", "Município", None), ("uf", "UF", None), ("aptos", "Aptos", num),
    ("precip_sum_mm", "Precip. dia (mm)", lambda v: num(v, 1)),
    ("precip_janela_votacao_08_17_mm", "Precip. 08–17h (mm)", lambda v: num(v, 1)),
    ("precip_prob_max_pct", "Prob. máx %", None), ("nivel_risco", "Nível", badge),
    ("vulnerabilidade", "Vulnerabilidade", None)], caption=f"Fonte: {esc(D.FONTES['impacto_auto' if og.get('impacto_mun') == 'atualizado' else 'impacto_bot4'])} · {esc(ts_i)} · até 80 municípios")}
<h3>Por UF ({rot_r})</h3>
{table(ordenar_risco(ru, "nivel_risco_predominante", "precipitacao_mm_media_estimada"), [
    ("uf", "UF", None), ("estado", "Estado", None), ("regiao", "Região", None),
    ("nivel_risco_predominante", "Nível", badge), ("precipitacao_mm_media_estimada", "Precip. média (mm)", lambda v: num(v, 1)),
    ("nivel_risco_manha_bot2", "Manhã (Bot 2)", lambda v: badge(v) if isinstance(v, str) else "—"),
    ("observacoes", "Observações", None)], caption="Nível predominante = maior fatia do eleitorado coberto. UFs não listadas não têm município coberto.")}
<h3>Por grande região ({rot_r})</h3>
{table(rr, [
    ("regiao", "Região", None), ("nivel_risco_predominante", "Nível", badge),
    ("precipitacao_mm_media_estimada", "Precip. média (mm)", lambda v: num(v, 1)), ("observacoes", "Observações", None)])}
</section>

<section id="impacto">
<h2>Impacto estimado na abstenção (pp, com faixa de incerteza)</h2>
<p class="muted">Formato: <b>+mid (lo a hi)</b> pontos percentuais. "Abstenções extras" = aptos × pp / 100 (lo a hi), arredondado à centena – ordem de grandeza, não previsão.</p>
<h3>Municípios</h3>
{table(imx, [
    ("municipio", "Município", None), ("uf", "UF", None), ("aptos", "Aptos", num), ("nivel_risco", "Risco", badge),
    ("faixa", "Efeito (pp)", None), ("votos", "Abstenções extras (faixa)", None),
    ("mais_prejudicado", "Maior base local (1º turno)", None), ("vulnerabilidade", "Vulnerab.", None),
    ("ajuste_noticias", "Ajuste por notícias", None), ("efeito_mid_manha_bot4", "Efeito mid manhã (Bot 4)", lambda v: num(v, 2))],
    caption=f"Fonte: {esc(D.FONTES['impacto_auto' if og.get('impacto_mun') == 'atualizado' else 'impacto_bot4'])} · {esc(ts_i)} · até 80 municípios (lista completa em data/impacto/atualizacoes/)")}
<h3>Grandes regiões</h3>
{table(irx, [
    ("regiao", "Região", None), ("aptos", "Aptos", num), ("peso_eleitoral_pct", "Peso %", lambda v: num(v, 1)),
    ("nivel_risco", "Risco", badge), ("faixa", "Efeito (pp)", None), ("mais_prejudicado", "Maior base (1º turno)", None)])}
<h3>Unidades da Federação</h3>
{table(iux, [
    ("uf", "UF", None), ("regiao", "Região", None), ("aptos", "Aptos", num), ("nivel_risco", "Risco", badge),
    ("faixa", "Efeito (pp)", None), ("mais_prejudicado", "Maior base (1º turno)", None), ("vulnerabilidade", "Vulnerab.", None)],
    caption="ZZ = eleitores no exterior. Agregação estadual a partir de capitais/maiores centros; cobertura do interior incompleta.")}
</section>

<section id="redutos">
<h2>Redutos do 1º turno (Bot 3, TSE)</h2>
{pan}
{table(red_reg, [
    ("regiao", "Região", None), ("aptos", "Aptos", num), ("pct_abstencao", "Abstenção %", lambda v: num(v, 2)),
    ("pct_flavio", "% Flávio", lambda v: num(v, 2)), ("pct_lula", "% Lula", lambda v: num(v, 2)),
    ("diff_pp", "Dif. pp (Flávio−Lula)", lambda v: num(v, 2)), ("vencedor", "Vencedor", None),
    ("peso_eleitoral_pct", "Peso %", lambda v: num(v, 1))])}
<h3>15 maiores colégios eleitorais</h3>
{table(top_col, [
    ("municipio", "Município", None), ("uf", "UF", None), ("aptos", "Aptos", num),
    ("pct_flavio", "% Flávio", lambda v: num(v, 2)), ("pct_lula", "% Lula", lambda v: num(v, 2)),
    ("diff_pp", "Dif. pp", lambda v: num(v, 2)), ("vencedor", "Vencedor", None)])}
<p class="muted">Leitura do Bot 4: quem tem maior base local tende a perder mais votos <b>absolutos</b> se a abstenção subir de modo uniforme – isso não implica mudança de margem percentual.</p>
</section>

<section id="social">
<h2>Sinais sociais (X, Instagram + fontes locais)</h2>
<p class="alert">{esc(D.DISCLAIMER_SOCIAL).replace('**', '')}</p>
{social_html}
</section>

<section id="metodologia">
<h2>Metodologia</h2>
<ol>
<li><b>Dados eleitorais (Bot 0/Bot 3):</b> resultados oficiais do 1º turno 2026 (TSE) por município, UF e região: aptos, abstenção, votos por candidato, redutos e peso eleitoral.</li>
<li><b>Clima (Bot 0/Bot 2):</b> previsão Open-Meteo para a janela de votação 08h–17h nos maiores colégios + alertas oficiais do INMET; classificação a/b/c do projeto (alertas priorizados sobre o modelo quando divergentes).</li>
<li><b>Correlação (Bot 1):</b> literatura internacional (meta-análise de 34 estudos: ≈ +0,4 a +1,0 pp por cm de chuva) + análise cross-section do 1º turno nos 30 maiores colégios (diferença bruta ≈ +2,2 pp entre faixa moderada e sem chuva; efeito reduzido após controles regionais).</li>
<li><b>Impacto (Bot 4):</b> regra prática – moderada +0,5 a +1,2 pp; torrencial +1,2 a +3,0 pp – aplicada à classificação de cada local; impacto diferencial proporcional à base de votos do 1º turno.</li>
<li><b>Sinais sociais:</b> monitoramento do X e de portais locais, filtrado por relevância e tipo de fonte; exibido separadamente e sem alterar automaticamente as estimativas.</li>
</ol>
</section>

<section id="limitacoes">
<h2>Limitações e incerteza</h2>
<ol>{lim}</ol>
</section>

<section id="fontes">
<h2>Fontes e timestamps</h2>
<div class="tw"><table><thead><tr><th>Camada</th><th>Atualizado em (declarado no arquivo)</th></tr></thead><tbody>{ts_html}</tbody></table></div>
<ul>
<li>TSE – Tribunal Superior Eleitoral (resultados 1º turno 2026)</li>
<li>Open-Meteo (previsão e arquivo histórico ERA5) – <a href="https://open-meteo.com/">open-meteo.com</a></li>
<li>INMET – alertas meteorológicos – <a href="https://alertas2.inmet.gov.br/">alertas2.inmet.gov.br</a></li>
<li>IBGE – códigos e malhas municipais</li>
<li>Literatura: Damsbo-Svendsen &amp; Hansen (2023, Electoral Studies); Gomez, Hansford &amp; Krause (2007, J. of Politics); Horiuchi &amp; Kang (2018, APR)</li>
</ul>
<p class="muted">Código sob licença MIT; dados de análise sob CC BY 4.0; dados de origem pública mantêm os termos originais.</p>
</section>
</main>
<footer>Chuva × Abstenção Eleitoral · 2º Turno 2026 · Página gerada em {esc(gerado)} por scripts/build_site.py</footer>
</body>
</html>
"""


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    (OUT.parent / ".nojekyll").touch()
    print(f"OK: {OUT.relative_to(ROOT)} ({OUT.stat().st_size/1024:.1f} KB)")


if __name__ == "__main__":
    main()
