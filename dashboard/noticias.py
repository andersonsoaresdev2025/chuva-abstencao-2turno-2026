"""Componentes Streamlit do monitoramento de notícias (página 'Notícias' e
quadro 'Principais notícias agora' da Visão Geral). Isolado do resto do app."""
from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from common import noticias as N

TEMA_ICONE = {"locais de votação": "🗳️", "abstenção": "📉", "alagamento": "🌊", "mobilidade": "🚧",
              "alerta": "⚠️", "geral": "📰"}


@st.cache_data(ttl=120)
def _dados(dir_str: str):
    from pathlib import Path
    d = Path(dir_str)
    return N.carregar_noticias(d), N.carregar_portais(d)


def dados():
    return _dados(str(N.NOTICIAS_DIR))


def _local(r) -> str:
    c, u = str(r.get("cidade") or ""), str(r.get("uf") or "")
    return f"{c} ({u})" if c and u else (c or u or "—")


def _linha_md(r) -> str:
    icone = TEMA_ICONE.get(r["tema"], "📰")
    hora = str(r["publicado_brt"])[11:16] or "—"
    dia = "" if str(r["publicado_brt"]).startswith("2026-10-25") else " (24/10)"
    alerta = " ⚠️" if bool(r.get("alerta")) else ""
    titulo = str(r["titulo"]).replace("[", "(").replace("]", ")")
    return (f"{icone} **[{titulo}]({r['link']})**{alerta}  \n"
            f"<small>{html.escape(str(r['portal']))} · {hora} BRT{dia} · {html.escape(_local(r))} · "
            f"{r['tema']}</small>")


def bloco_principais(n: int = 6):
    """Quadro compacto para a Visão Geral."""
    df, _ = dados()
    st.subheader("📰 Principais notícias agora")
    if df.empty:
        st.info("Monitoramento de notícias ainda sem itens coletados (`data/noticias/`). "
                "Veja a página **Notícias** quando a primeira coleta for publicada.")
        return
    top = N.principais(df, n)
    st.caption(f"Coleta: {N.ultima_coleta(df)} · {len(df)} notícias monitoradas · "
               "portais nacionais e locais das áreas com risco de chuva · veja a página **Notícias**.")
    cols = st.columns(2)
    for i, (_, r) in enumerate(top.iterrows()):
        with cols[i % 2]:
            st.markdown(_linha_md(r), unsafe_allow_html=True)


def pagina():
    st.title("📰 Notícias: chuva × eleição")
    df, portais = dados()
    st.warning(N.DISCLAIMER)
    if df.empty:
        st.info("Ainda não há notícias coletadas. Quando `scripts/coletar_noticias.py` gravar "
                "`data/noticias/noticias_consolidado.csv`, elas aparecerão aqui automaticamente.")
    else:
        n_nac = int((df["abrangencia"] == "nacional").sum())
        n_reg = int((df["abrangencia"] == "regional").sum())
        st.caption(f"Última coleta: {N.ultima_coleta(df)} · {len(df)} notícias "
                   f"({n_nac} de portais nacionais, {n_reg} de portais locais, "
                   f"{len(df) - n_nac - n_reg} de outras fontes)")
        c1, c2, c3, c4 = st.columns(4)
        regioes = sorted({x for v in df["regiao"].astype(str) for x in v.split("/") if x})
        ufs = sorted({x for v in df["uf"].astype(str) for x in v.split("/") if x})
        with c1:
            f_reg = st.multiselect("Região", regioes)
        with c2:
            f_uf = st.multiselect("UF", ufs)
        with c3:
            f_tema = st.multiselect("Tema", sorted(df["tema"].astype(str).unique()))
        with c4:
            f_ab = st.multiselect("Abrangência", ["nacional", "regional", "outro"],
                                  help="regional = portal local; outro = fonte fora da lista verificada")
        so_verif = st.checkbox("Ocultar itens sinalizados (⚠️)", value=False)
        s = df.copy()
        if f_reg:
            s = s[s["regiao"].astype(str).apply(lambda v: any(x in v.split("/") for x in f_reg))]
        if f_uf:
            s = s[s["uf"].astype(str).apply(lambda v: any(x in v.split("/") for x in f_uf))]
        if f_tema:
            s = s[s["tema"].isin(f_tema)]
        if f_ab:
            s = s[s["abrangencia"].isin(f_ab)]
        if so_verif:
            s = s[~s["alerta"]]
        st.markdown(f"**{len(s)} notícias** (ordenadas por relevância)")
        if not s.empty:
            cont = s.groupby("tema").size().sort_values(ascending=False)
            st.caption(" · ".join(f"{TEMA_ICONE.get(k, '📰')} {k}: {v}" for k, v in cont.items()))
            t = s.assign(
                horario=s["publicado_brt"].astype(str) + " BRT",
                local=s.apply(_local, axis=1),
                aviso=s["alerta"].map({True: "⚠️", False: ""}),
            )
            st.dataframe(
                t[["aviso", "titulo", "link", "portal", "abrangencia", "horario", "local", "tema", "score",
                   "sinalizacao"]],
                width="stretch", hide_index=True,
                column_config={
                    "aviso": st.column_config.TextColumn("", width="small"),
                    "titulo": st.column_config.TextColumn("Título", width="large"),
                    "link": st.column_config.LinkColumn("Link", display_text="abrir"),
                    "portal": "Portal", "abrangencia": "Abrangência", "horario": "Publicado",
                    "local": "Cidade/UF", "tema": "Tema",
                    "score": st.column_config.NumberColumn("Relevância", format="%.1f"),
                    "sinalizacao": "Sinalização",
                })
            with st.expander("Ver como cards (top 20)"):
                for _, r in s.head(20).iterrows():
                    st.markdown(_linha_md(r), unsafe_allow_html=True)
    with st.expander(f"Portais monitorados ({len(portais)} verificados)"):
        if portais.empty:
            st.info("Lista de portais (`data/noticias/portais.csv`) não encontrada.")
        else:
            st.caption("URL verificada (HTTP 200) na data indicada. Portais sem RSS funcionando são "
                       "cobertos por buscas do Google Notícias restritas ao domínio (site:).")
            st.dataframe(
                portais[["nome", "abrangencia", "uf", "cidades_cobertas", "tipo", "url", "rss_url",
                         "observacoes", "verificado_em_utc"]],
                width="stretch", hide_index=True,
                column_config={"url": st.column_config.LinkColumn("Site"),
                               "rss_url": st.column_config.LinkColumn("RSS")})
    md = N.resumo_md()
    if md:
        with st.expander("Resumo da última coleta (resumo_noticias.md)"):
            st.markdown(md)
