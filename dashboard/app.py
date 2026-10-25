"""
Dashboard público – Chuva × Abstenção Eleitoral
Segundo Turno 2026 | Flávio Bolsonaro × Lula
Projeto de monitoramento em tempo real

Main file para o Streamlit Community Cloud: dashboard/app.py
Os dados são lidos de ../data/ (caminhos relativos ao repositório).
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Permite importar o módulo compartilhado `common/` (raiz do repositório)
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from common import dados as D  # noqa: E402
from common import impacto_agora as IA  # noqa: E402
from dashboard import noticias as NOT  # noqa: E402  (monitoramento de notícias)

# -----------------------------------------------------------------------------
# Configuração da página
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Chuva × Abstenção | 2º Turno 2026",
    page_icon="🌧️",
    layout="wide",
    initial_sidebar_state="expanded",
)

COR = {"torrencial": "#c0392b", "moderada": "#e67e22", "sem_chuva_relevante": "#27ae60"}


def cor_risco(nivel) -> str:
    return COR.get(D.nivel_curto(nivel), "#7f8c8d")


def mapa_cores(series) -> dict:
    return {k: cor_risco(k) for k in pd.Series(series).dropna().unique()}


def tabela(df: pd.DataFrame, cols: dict, **kw):
    """Exibe apenas as colunas existentes, renomeadas (evita KeyError se o CSV mudar)."""
    presentes = [c for c in cols if c in df.columns]
    st.dataframe(df[presentes].rename(columns=cols), width="stretch", hide_index=True, **kw)


@st.cache_data(ttl=300)
def carregar():
    return D.carregar_tudo()


@st.cache_data(ttl=120)
def carregar_social():
    return D.carregar_social()


@st.cache_data(ttl=300)
def load_md(path_str: str) -> str:
    return D.read_md(Path(path_str))



# -----------------------------------------------------------------------------
# Impacto estimado AGORA (chuva acumulada desde 08h -> p.p. por candidato)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=900, show_spinner=False)
def _series_open_meteo(lats: tuple, lons: tuple):
    """Cache de ~15 min da série horária Open-Meteo. Falhas não são cacheadas (exceção propaga)."""
    return D.agora_utc().isoformat(), IA.buscar_open_meteo(list(lats), list(lons))


def _fmt_pp(x: float, sinal: bool = True) -> str:
    casas = 4 if abs(x) < 0.01 else 2
    s = f"{x:+.{casas}f}" if sinal else f"{x:.{casas}f}"
    return s.replace("-", "−").replace(".", ",")


def _fmt_int(x: float) -> str:
    return f"{int(round(x, -2)):,}".replace(",", ".")


def impacto_agora_calc():
    obtido = {}

    def buscar(lats, lons):
        ts, series = _series_open_meteo(tuple(lats), tuple(lons))
        obtido["ts"] = ts
        return series

    r = IA.calcular_com_api(buscar=buscar)
    if obtido.get("ts") and not r["usou_fallback"]:
        from datetime import datetime as _dt
        r["precip_obtida_em_brt"] = _dt.fromisoformat(obtido["ts"]).astimezone(D.TZ_BRT).strftime("%H:%M BRT")
    return r


@st.fragment(run_every="5m")
def bloco_impacto_agora():
    try:
        r = impacto_agora_calc()
    except Exception as e:  # noqa: BLE001 – o card nunca deve derrubar a página
        st.warning(f"Impacto estimado agora indisponível no momento ({type(e).__name__}).")
        return
    st.subheader(f"⏱️ Impacto estimado agora — {r['rotulo']}")
    f, l, m = r["flavio_pp"], r["lula_pp"], r["margem_lula_menos_flavio_pp"]
    vf, vl, ab = r["votos_perdidos_flavio"], r["votos_perdidos_lula"], r["abstencao_nacional_pp"]
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Flávio Bolsonaro (p.p. dos votos válidos)", _fmt_pp(f["mid"]),
                  help="Variação estimada na participação de Flávio nos votos válidos (Flávio+Lula) por causa "
                       "da chuva, ponto central (coeficiente médio do Bot 1).")
        st.caption(f"Faixa {_fmt_pp(f['min'])} a {_fmt_pp(f['max'])} p.p. · "
                   f"votos perdidos ≈ {_fmt_int(vf['mid'])} ({_fmt_int(vf['min'])}–{_fmt_int(vf['max'])})")
    with c2:
        st.metric("Lula (p.p. dos votos válidos)", _fmt_pp(l["mid"]),
                  help="Variação estimada na participação de Lula nos votos válidos (Flávio+Lula).")
        st.caption(f"Faixa {_fmt_pp(l['min'])} a {_fmt_pp(l['max'])} p.p. · "
                   f"votos perdidos ≈ {_fmt_int(vl['mid'])} ({_fmt_int(vl['min'])}–{_fmt_int(vl['max'])})")
    with c3:
        st.metric("Efeito na margem (Lula − Flávio)", f"{_fmt_pp(m['mid'])} p.p.",
                  help="Positivo = a chuva favorece Lula na margem; negativo = favorece Flávio.")
        st.caption(f"Faixa {_fmt_pp(m['min'])} a {_fmt_pp(m['max'])} p.p. · abstenção nacional "
                   f"{_fmt_pp(ab['mid'])} p.p. ({_fmt_pp(ab['min'], False)}–{_fmt_pp(ab['max'], False)})")
    with c4:
        st.metric("Cobertura do eleitorado", f"{r['cobertura_pct_eleitorado']:.1f}%".replace(".", ","),
                  help="Parcela dos eleitores aptos do país nos municípios com chuva medida; o restante conta como zero.")
        st.caption(f"{r['n_municipios_cobertos']} maiores colégios · demais municípios = 0")
    obtida = f" (dados obtidos às {r['precip_obtida_em_brt']})" if r.get("precip_obtida_em_brt") else ""
    janela = ("dia inteiro 08h–17h (previsão)" if r["modo"] == "projecao" else
              f"{r['horas_decorridas']:.1f} h desde 08h".replace(".", ","))
    st.caption(
        f"🕒 Calculado em {r['calculado_em_brt']} ({r['calculado_em_utc']}) · janela considerada: "
        f"{janela} · Precipitação: {r['fonte_precipitacao']}{obtida}."
    )
    if r["usou_fallback"]:
        st.warning("Open-Meteo indisponível agora: usando a previsão do Bot 0 (CSV) pró-rata pelas horas decorridas.")
    st.caption("⚠️ " + IA.DISCLAIMER)
    cb, ce = st.columns([1, 3])
    with cb:
        if st.button("🔄 Atualizar", help="Busca de novo a precipitação no Open-Meteo (cache de 15 min)"):
            _series_open_meteo.clear()
            st.rerun(scope="fragment")
    with ce:
        with st.expander("Como este número é calculado"):
            st.markdown(IA.METODO_TXT)
            st.markdown(
                "- Coeficiente: **0,07 p.p. de abstenção por mm** (faixa 0,04–0,10), do Bot 1.  \n"
                "- A faixa reflete só a incerteza do coeficiente; não inclui erro da precipitação nem efeitos de "
                "alagamento/transporte. O **sinal** pode mudar conforme onde chove (SP pesa a favor de Flávio na "
                "margem; RJ, Guarulhos e Campinas a favor de Lula).  \n"
                "- Base nacional: votos de Flávio e Lula no 1º turno (TSE). Valores muito pequenos são esperados: "
                "a chuva reduz votos dos dois lados quase na mesma proporção."
            )
            mun = r["municipios"].rename(columns={
                "municipio": "Município", "uf": "UF", "aptos": "Aptos", "pct_flavio_1t": "% Flávio 1ºT",
                "pct_lula_1t": "% Lula 1ºT", "precip_acum_mm": "Chuva acumulada (mm)",
                "efeito_abst_pp_lo": "Abst. lo (p.p.)", "efeito_abst_pp_mid": "Abst. mid (p.p.)",
                "efeito_abst_pp_hi": "Abst. hi (p.p.)", "abst_extras_mid": "Abstenções extras (mid)"})
            st.dataframe(mun.sort_values("Chuva acumulada (mm)", ascending=False), width="stretch",
                         hide_index=True)
            if r.get("erro_api"):
                st.caption(f"Erro da API Open-Meteo: {r['erro_api']}")


d = carregar()
impacto_mun, impacto_uf, impacto_reg = d["impacto_mun"], d["impacto_uf"], d["impacto_reg"]
risco_mun, risco_uf, risco_reg = d["risco_mun"], d["risco_uf"], d["risco_reg"]
previsao = d["previsao"]
sintese_impacto = load_md(str(D.IMPACTO_DIR / "sintese_executiva_impacto.md"))
sintese_correl = load_md(str(D.CORREL_DIR / "sintese_executiva.md"))
resumo_clima = load_md(str(D.CLIMA_DIR / "resumo_executivo.md"))
resumo_redutos = load_md(str(D.REDUTOS_DIR / "resumo_executivo_redutos.md"))

social = carregar_social()
timestamps = D.timestamps_dados(d)
ts_atualizacao = timestamps.get("Impacto (Bot 4)", "—")

PAGINAS = [
    "Visão Geral",
    "Risco de Chuva",
    "Impacto na Abstenção",
    "Redutos e Diferencial",
    "Sinais Sociais",
    "Notícias",
    "Metodologia e Limitações",
]

# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🌧️ Chuva × Abstenção")
    st.markdown("**2º Turno 2026**")
    st.caption("Flávio Bolsonaro × Lula")
    st.markdown("---")
    pagina = st.radio("Navegação", PAGINAS, index=0)
    st.markdown("---")
    st.markdown("**Dados atualizados em:**")
    for k, v in timestamps.items():
        st.caption(f"{k}: {v}")
    st.caption(f"Página gerada: {D.fmt_utc_brt()}")
    st.markdown("---")
    st.caption(
        "Projeto aberto · Dados do TSE, Open-Meteo, INMET e análises dos Bots 0–4.  \n"
        "Transparência máxima: efeitos são estimativas com incerteza."
    )

st.markdown(
    """
    <style>
    h1, h2, h3 { font-weight: 600; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Faixa de timestamp sempre visível no topo
st.info(
    f"🕒 **Dados atualizados em:** impacto (Bot 4) {ts_atualizacao} · "
    f"risco a/b/c (Bot 2) {timestamps.get('Risco de chuva a/b/c (Bot 2)', '—')} · "
    f"agora {D.fmt_utc_brt()}. Estimativas com incerteza — não é previsão eleitoral oficial."
)

# -----------------------------------------------------------------------------
# PÁGINA: VISÃO GERAL
# -----------------------------------------------------------------------------
if pagina == "Visão Geral":
    st.title("🌧️ Chuva × Abstenção Eleitoral")
    st.markdown("### Monitoramento do 2º Turno — 25 de outubro de 2026")
    st.markdown(
        "Acompanhe o risco de chuva durante o horário de votação "
        "(08h–17h) e a estimativa de impacto sobre a abstenção e sobre cada candidato."
    )

    bloco_impacto_agora()
    st.markdown("---")

    NOT.bloco_principais()  # quadro de notícias (abaixo dos cards de impacto)
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    n_alta = n_media = 0
    if not impacto_mun.empty and "vulnerabilidade" in impacto_mun.columns:
        n_alta = int((impacto_mun["vulnerabilidade"] == "Alta").sum())
        n_media = int((impacto_mun["vulnerabilidade"] == "Média").sum())
    with col1:
        st.metric("Municípios com vulnerabilidade Alta", n_alta,
                  help="Entre os municípios com previsão detalhada (Bot 4)")
    with col2:
        st.metric("Municípios com vulnerabilidade Média", n_media)
    with col3:
        sudeste = impacto_reg[impacto_reg["regiao"] == "Sudeste"] if not impacto_reg.empty else pd.DataFrame()
        if not sudeste.empty:
            r = sudeste.iloc[0]
            st.metric("Efeito mid Sudeste (pp)", f"+{r['efeito_abstencao_pp_mid']:.1f}",
                      help=f"Faixa {r['efeito_abstencao_pp_lo']:.1f}–{r['efeito_abstencao_pp_hi']:.1f} pp")
        else:
            st.metric("Efeito mid Sudeste (pp)", "—")
    with col4:
        n_prev = len(impacto_mun) if not impacto_mun.empty else 0
        st.metric("Municípios com previsão horária", n_prev,
                  help="Maiores colégios com previsão Open-Meteo (Bot 0/Bot 4)")

    st.markdown("---")
    st.subheader("Onde a chuva deve importar mais hoje")
    if not impacto_mun.empty:
        criticos = impacto_mun[impacto_mun["vulnerabilidade"].isin(["Alta", "Média"])].sort_values(
            "aptos", ascending=False).copy()
        if not criticos.empty:
            criticos["aptos_fmt"] = criticos["aptos"].apply(lambda x: f"{int(x):,}".replace(",", "."))
            criticos["efeito"] = criticos.apply(
                lambda r: f"+{r['efeito_abstencao_pp_mid']:.2f} ({r['efeito_abstencao_pp_lo']:.1f}–{r['efeito_abstencao_pp_hi']:.1f})",
                axis=1)
            tabela(criticos, {
                "municipio": "Município", "uf": "UF", "aptos_fmt": "Eleitores aptos",
                "nivel_risco": "Risco de chuva", "efeito": "Efeito na abstenção (pp)",
                "mais_prejudicado": "Maior base local (1º turno)", "vulnerabilidade": "Vulnerabilidade"})
        else:
            st.info("Nenhum município prioritário classificado com vulnerabilidade Alta ou Média.")
    else:
        st.warning("Dados de impacto ainda não carregados.")

    st.markdown("---")
    st.subheader("Mensagem principal")
    st.markdown(
        """
        - O **Centro-Sul** (especialmente a Região Metropolitana de São Paulo e o Rio de Janeiro) concentra o risco de chuva relevante no horário de votação.
        - O efeito estimado sobre a abstenção nos locais de risco alto fica na faixa de **+1,2 a +3,0 pontos percentuais**.
        - O impacto diferencial entre candidatos é **localizado** e depende da base de votos do 1º turno. Não há, nesta versão, evidência de viés climático sistemático forte em escala nacional.
        - **Nordeste** (principal reduto de Lula) tem previsão de tempo bom → baixo impacto climático esperado.
        """
    )
    if not social.empty:
        st.markdown("---")
        st.subheader("📣 Últimos sinais sociais")
        st.caption(D.DISCLAIMER_SOCIAL)
        st.dataframe(
            social.head(5)[["timestamp_post", "cidade", "uf", "nivel_risco_implicito", "fonte", "resumo", "link"]],
            width="stretch", hide_index=True,
            column_config={"link": st.column_config.LinkColumn("Link")})

# -----------------------------------------------------------------------------
# PÁGINA: RISCO DE CHUVA
# -----------------------------------------------------------------------------
elif pagina == "Risco de Chuva":
    st.title("📡 Risco de Chuva no Horário de Votação")
    st.markdown("Classificação oficial do projeto para a janela **08h–17h** (horário de Brasília).")
    st.markdown(
        """
        | Nível | Critério | Cor |
        |-------|----------|-----|
        | **a) Torrencial / Tempestade / Risco de alagamento** | ≥ 20–30 mm ou alertas | 🔴 |
        | **b) Moderada** | 5–20/30 mm | 🟠 |
        | **c) Sem chuva relevante** | < 5 mm | 🟢 |
        """
    )

    st.subheader("Previsão horária – maiores colégios (Bot 0 / Bot 4)")
    st.caption(f"Fonte: {D.FONTES['impacto_bot4']} · atualizado {ts_atualizacao}")
    if not impacto_mun.empty:
        df = impacto_mun.copy()
        df["_ordem"] = df["nivel_risco"].map(D.nivel_curto).map(D.ORDEM_RISCO)
        df = df.sort_values(["_ordem", "aptos"], ascending=[True, False])
        col_precip = ("precip_janela_votacao_08_17_mm" if "precip_janela_votacao_08_17_mm" in df.columns
                      else "precip_sum_mm")
        if col_precip in df.columns:
            fig = px.bar(
                df, x="municipio", y=col_precip, color="nivel_risco",
                color_discrete_map=mapa_cores(df["nivel_risco"]),
                labels={col_precip: "Precipitação estimada (mm)", "municipio": "Município", "nivel_risco": "Risco"},
                title="Precipitação prevista na janela de votação 08–17h (Open-Meteo)",
            )
            fig.update_layout(xaxis_tickangle=-40, height=420, margin=dict(t=40, b=80))
            st.plotly_chart(fig, width="stretch")
        tabela(df, {
            "municipio": "Município", "uf": "UF", "precip_sum_mm": "Precip. dia (mm)",
            "precip_janela_votacao_08_17_mm": "Precip. 08–17h (mm)",
            "precip_prob_max_pct": "Prob. máx. (%)", "nivel_risco": "Nível de risco",
            "vulnerabilidade": "Vulnerabilidade"})
    else:
        st.warning("Dados de municípios não disponíveis.")

    st.markdown("---")
    st.subheader("Classificação a/b/c com alertas INMET (Bot 2)")
    st.caption(f"Fonte: {D.FONTES['risco_bot2']} · atualizado "
               f"{timestamps.get('Risco de chuva a/b/c (Bot 2)', '—')}")
    if not risco_mun.empty:
        rm = risco_mun.copy()
        rm["_ordem"] = rm["nivel_risco"].map(D.nivel_curto).map(D.ORDEM_RISCO)
        rm = rm.sort_values(["_ordem", "precipitacao_mm_estimada"], ascending=[True, False])
        filtro_uf = st.multiselect("Filtrar UF", sorted(rm["uf"].dropna().unique()))
        if filtro_uf:
            rm = rm[rm["uf"].isin(filtro_uf)]
        tabela(rm, {
            "municipio": "Município", "uf": "UF", "regiao": "Região", "nivel_risco": "Nível",
            "precipitacao_mm_estimada": "Precip. estimada (mm)", "horario_pico": "Pico",
            "probabilidade": "Prob. (%)", "fonte_principal": "Fonte", "observacoes": "Observações",
            "ultima_atualizacao": "Atualizado"})
    else:
        st.info("Classificação do Bot 2 não disponível.")

    st.warning(
        "⚠️ As duas camadas acima foram geradas em horários diferentes (Bot 2 ~06:35 BRT com alertas INMET; "
        "Bot 4 ~09:24 BRT com nova rodada Open-Meteo) e **divergem para alguns locais** "
        "(ex.: Curitiba 'a' no Bot 2 vs 'moderada' no Bot 4; MS 'a' vs 'sem chuva relevante'). "
        "Ambas são mostradas sem ajuste para máxima transparência."
    )

    st.markdown("---")
    st.subheader("Por estado e região")
    c1, c2 = st.columns(2)
    with c1:
        if not risco_uf.empty:
            st.markdown("**Estados – classificação Bot 2**")
            tabela(risco_uf, {
                "uf": "UF", "regiao": "Região", "nivel_risco_predominante": "Nível",
                "precipitacao_mm_media_estimada": "Precip. média (mm)", "observacoes": "Observações"},
                height=400)
        if not impacto_uf.empty:
            st.markdown("**Estados – agregado Bot 4 (impacto)**")
            tabela(impacto_uf, {
                "uf": "UF", "regiao": "Região", "nivel_risco": "Risco",
                "efeito_abstencao_pp_mid": "Efeito mid (pp)", "vulnerabilidade": "Vulnerabilidade",
                "peso_eleitoral_pct": "Peso %"}, height=400)
    with c2:
        if not risco_reg.empty:
            st.markdown("**Grandes Regiões – classificação Bot 2**")
            tabela(risco_reg, {
                "regiao": "Região", "nivel_risco_predominante": "Nível",
                "precipitacao_mm_media_estimada": "Precip. média (mm)", "observacoes": "Observações"})
        if not impacto_reg.empty:
            st.markdown("**Grandes Regiões – efeito estimado (Bot 4)**")
            fig_reg = px.bar(
                impacto_reg, x="regiao", y="efeito_abstencao_pp_mid", color="nivel_risco",
                color_discrete_map=mapa_cores(impacto_reg["nivel_risco"]),
                labels={"efeito_abstencao_pp_mid": "Efeito mid na abstenção (pp)", "regiao": "Região"},
                title="Efeito estimado por região",
            )
            fig_reg.update_layout(height=360)
            st.plotly_chart(fig_reg, width="stretch")

# -----------------------------------------------------------------------------
# PÁGINA: IMPACTO NA ABSTENÇÃO
# -----------------------------------------------------------------------------
elif pagina == "Impacto na Abstenção":
    st.title("📊 Impacto Estimado na Abstenção")
    st.markdown(
        "Efeito esperado da chuva sobre a taxa de abstenção, em **pontos percentuais**, "
        "com base nos coeficientes do Bot 1 (literatura + 1º turno 2026)."
    )
    st.info(
        "**Regra prática do Bot 1:**  \n"
        "• Moderada → +0,5 a +1,2 pp  \n"
        "• Torrencial / tempestade / alagamento → +1,2 a +3,0 pp  \n"
        "Valores “mid” são o ponto central da faixa usada nas tabelas."
    )
    st.caption(f"Fonte: {D.FONTES['impacto_bot4']} · atualizado {ts_atualizacao}")

    if not impacto_mun.empty:
        st.subheader("Municípios prioritários")
        df = impacto_mun.sort_values("efeito_abstencao_pp_mid", ascending=False).copy()
        df["faixa"] = df.apply(
            lambda r: f"{r['efeito_abstencao_pp_lo']:.1f} – {r['efeito_abstencao_pp_hi']:.1f}", axis=1)
        # Ordem de grandeza em votos (Bot 1: +1 pp ≈ 1% dos aptos) – apenas aritmética sobre os CSVs
        df["abst_extra_mid"] = (df["aptos"] * df["efeito_abstencao_pp_mid"] / 100).round(-2).astype(int)
        df["abst_extra_faixa"] = df.apply(
            lambda r: f"{int(round(r['aptos'] * r['efeito_abstencao_pp_lo'] / 100, -2)):,} – "
                      f"{int(round(r['aptos'] * r['efeito_abstencao_pp_hi'] / 100, -2)):,}".replace(",", "."),
            axis=1)

        fig = go.Figure()
        for _, row in df.iterrows():
            fig.add_trace(go.Bar(
                name=row["municipio"], x=[row["municipio"]], y=[row["efeito_abstencao_pp_mid"]],
                error_y=dict(type="data", symmetric=False,
                             array=[row["efeito_abstencao_pp_hi"] - row["efeito_abstencao_pp_mid"]],
                             arrayminus=[row["efeito_abstencao_pp_mid"] - row["efeito_abstencao_pp_lo"]]),
                marker_color=cor_risco(row["nivel_risco"]), showlegend=False))
        fig.update_layout(title="Efeito estimado na abstenção (ponto central + faixa de incerteza)",
                          yaxis_title="Pontos percentuais", xaxis_tickangle=-40, height=450,
                          margin=dict(b=100))
        st.plotly_chart(fig, width="stretch")

        tabela(df, {
            "municipio": "Município", "uf": "UF", "nivel_risco": "Risco",
            "efeito_abstencao_pp_mid": "Efeito mid (pp)", "faixa": "Faixa (pp)",
            "abst_extra_mid": "Abstenções extras (mid, ordem de grandeza)",
            "abst_extra_faixa": "Abstenções extras (faixa)", "vulnerabilidade": "Vulnerabilidade"})
        st.caption("Abstenções extras = aptos × efeito (pp) / 100, arredondado à centena. Ordem de grandeza, "
                   "não previsão.")
    else:
        st.warning("Dados de impacto municipal não disponíveis.")

    st.markdown("---")
    st.subheader("Visão por região")
    if not impacto_reg.empty:
        tabela(impacto_reg, {
            "regiao": "Região", "aptos": "Aptos", "peso_eleitoral_pct": "Peso %", "nivel_risco": "Risco",
            "efeito_abstencao_pp_mid": "Efeito mid", "efeito_abstencao_pp_lo": "Lo",
            "efeito_abstencao_pp_hi": "Hi", "mais_prejudicado": "Maior base (1º turno)"})
    st.subheader("Visão por estado")
    if not impacto_uf.empty:
        tabela(impacto_uf.sort_values("efeito_abstencao_pp_mid", ascending=False), {
            "uf": "UF", "regiao": "Região", "aptos": "Aptos", "nivel_risco": "Risco",
            "efeito_abstencao_pp_mid": "Efeito mid", "efeito_abstencao_pp_lo": "Lo",
            "efeito_abstencao_pp_hi": "Hi", "mais_prejudicado": "Maior base (1º turno)",
            "observacao": "Observação"}, height=420)

# -----------------------------------------------------------------------------
# PÁGINA: REDUTOS E DIFERENCIAL
# -----------------------------------------------------------------------------
elif pagina == "Redutos e Diferencial":
    st.title("🗳️ Redutos do 1º Turno e Impacto Diferencial")
    st.markdown(
        "Quem tinha maior base de votos em cada localidade no 1º turno tende a perder "
        "mais votos **absolutos** se a abstenção subir de forma uniforme. "
        "Isso não implica necessariamente mudança de margem percentual."
    )
    st.caption(f"Fonte: {D.FONTES['redutos_bot3']} e {D.FONTES['impacto_bot4']}")

    rr = d["redutos_reg"]
    if not rr.empty:
        st.subheader("Resultado do 1º turno por região (TSE)")
        tabela(rr, {
            "regiao": "Região", "aptos": "Aptos", "pct_abstencao": "Abstenção %",
            "pct_flavio": "% Flávio", "pct_lula": "% Lula", "diff_pp": "Dif. (pp, Flávio−Lula)",
            "vencedor": "Vencedor", "peso_eleitoral_pct": "Peso %"})

    if not impacto_mun.empty:
        st.subheader("Municípios prioritários")
        tabela(impacto_mun, {
            "municipio": "Município", "uf": "UF", "pct_flavio_1t": "% Flávio (1ºT)",
            "pct_lula_1t": "% Lula (1ºT)", "vencedor_1t": "Vencedor 1ºT", "nivel_risco": "Risco chuva",
            "efeito_abstencao_pp_mid": "Efeito mid (pp)", "mais_prejudicado": "Maior base local",
            "vulnerabilidade": "Vulnerabilidade"})
        st.markdown("---")
        st.subheader("Leitura política (provisória, Bot 4)")
        st.markdown(
            """
            - **São Paulo capital** e **São Bernardo do Campo**: Lula à frente no 1º turno + risco torrencial → maior exposição relativa de Lula em votos absolutos.
            - **Rio de Janeiro capital**, **Guarulhos** e **Campinas**: Flávio à frente + risco alto → maior exposição relativa de Flávio.
            - Agregado de **SP, PR e RS**: Flávio tem vantagem estrutural; a chuva nessas áreas pode reduzir um pouco sua margem em votos absolutos.
            - **Nordeste**: tempo bom previsto → pouco efeito climático esperado sobre o reduto de Lula.
            - **Conclusão cautelosa:** não há evidência forte de viés climático nacional sistemático favorecendo um dos candidatos. O efeito mais relevante é o aumento localizado da abstenção em grandes municípios competitivos do Centro-Sul.
            """
        )
    else:
        st.warning("Dados não disponíveis.")

    st.markdown("---")
    st.subheader("Por estado (resumo)")
    if not impacto_uf.empty:
        tabela(impacto_uf.sort_values("peso_eleitoral_pct", ascending=False), {
            "uf": "UF", "regiao": "Região", "pct_flavio_1t": "% Flávio", "pct_lula_1t": "% Lula",
            "vencedor_1t": "Vencedor 1ºT", "nivel_risco": "Risco", "efeito_abstencao_pp_mid": "Efeito mid",
            "mais_prejudicado": "Maior base", "peso_eleitoral_pct": "Peso %"}, height=420)

    with st.expander("Ver resumo executivo completo do Bot 3 (redutos)"):
        st.markdown(resumo_redutos)

# -----------------------------------------------------------------------------
# PÁGINA: SINAIS SOCIAIS
# -----------------------------------------------------------------------------
elif pagina == "Sinais Sociais":
    st.title("📣 Sinais Sociais (X + fontes locais)")
    st.warning(D.DISCLAIMER_SOCIAL)
    if social.empty:
        st.info(
            "Ainda não há sinais sociais publicados. Quando o monitoramento gravar arquivos "
            "`data/social/sinais_*.csv` (e opcionalmente `resumo_*.md`), eles aparecerão aqui automaticamente."
        )
    else:
        st.caption(f"Fonte: {D.FONTES['social']} · último coletado "
                   f"{timestamps.get('Sinais sociais (último coletado)', '—')} · {len(social)} sinais")
        c1, c2, c3 = st.columns(3)
        with c1:
            cidades = st.multiselect("Cidade", sorted(social["cidade"].dropna().astype(str).unique()))
        with c2:
            niveis = st.multiselect("Nível de risco implícito",
                                    sorted(social["nivel_risco_implicito"].dropna().astype(str).unique()))
        with c3:
            tipos_fonte = st.multiselect("Tipo de fonte",
                                         sorted(social["tipo_fonte"].dropna().astype(str).unique()))
        s = social.copy()
        if cidades:
            s = s[s["cidade"].astype(str).isin(cidades)]
        if niveis:
            s = s[s["nivel_risco_implicito"].astype(str).isin(niveis)]
        if tipos_fonte:
            s = s[s["tipo_fonte"].astype(str).isin(tipos_fonte)]

        cont = s.groupby(["cidade", "nivel_risco_implicito"], dropna=False).size().reset_index(name="n")
        if not cont.empty:
            fig = px.bar(cont, x="cidade", y="n", color="nivel_risco_implicito",
                         color_discrete_map=mapa_cores(cont["nivel_risco_implicito"]),
                         labels={"n": "Nº de sinais", "cidade": "Cidade",
                                 "nivel_risco_implicito": "Risco implícito"},
                         title="Sinais por cidade e nível de risco implícito")
            fig.update_layout(height=340, xaxis_tickangle=-30)
            st.plotly_chart(fig, width="stretch")

        st.dataframe(
            s[["timestamp_post", "timestamp_coleta_utc", "cidade", "uf", "tipo", "nivel_risco_implicito",
               "confianca", "fonte", "tipo_fonte", "resumo", "link", "cidade_risco_previsto"]],
            width="stretch", hide_index=True,
            column_config={"link": st.column_config.LinkColumn("Link (fonte original)")})

    nome_md, txt_md = D.ultimo_resumo_social()
    if txt_md:
        with st.expander(f"Resumo mais recente do monitoramento ({nome_md})", expanded=social.empty is False):
            st.markdown(txt_md)

# -----------------------------------------------------------------------------
# PÁGINA: NOTÍCIAS (módulo dashboard/noticias.py)
# -----------------------------------------------------------------------------
elif pagina == "Notícias":
    NOT.pagina()

# -----------------------------------------------------------------------------
# PÁGINA: METODOLOGIA E LIMITAÇÕES
# -----------------------------------------------------------------------------
elif pagina == "Metodologia e Limitações":
    st.title("📐 Metodologia, Fontes e Limitações")
    st.markdown("Transparência é regra do projeto. Leia com atenção.")

    st.subheader("Fontes dos dados")
    st.markdown(
        """
        | Camada | Origem | Conteúdo principal |
        |--------|--------|--------------------|
        | Bot 0 | TSE + Open-Meteo + IBGE | Resultados 1º turno, aptos, abstenção, previsão meteorológica |
        | Bot 1 | Literatura + análise empírica 1º turno | Coeficientes de efeito chuva → abstenção |
        | Bot 2 | Open-Meteo + alertas INMET + classificação do projeto | Risco de chuva por município/estado/região na janela 08h–17h |
        | Bot 3 | TSE 1º turno | Redutos eleitorais, margens, peso eleitoral |
        | Bot 4 | Cruzamento dos anteriores | Impacto diferencial e síntese |
        | Social | X + portais locais públicos | Relatos de chuva/alagamento/mobilidade (não oficiais) |
        """
    )

    st.subheader("Timestamps declarados nos arquivos")
    st.table(pd.DataFrame({"Camada": list(timestamps), "Atualizado em": list(timestamps.values())}))

    st.subheader("Coeficientes de efeito (Bot 1)")
    st.markdown(
        """
        - Literatura internacional (meta-análises): cerca de **+0,4 a +1,0 pp por centímetro** de chuva.
        - Observado no 1º turno 2026 (30 maiores colégios): diferença bruta de ≈ **+2,2 pp** entre faixa sem chuva relevante e faixa moderada.
        - **Regra prática adotada para o dia:**
          - Moderada → **+0,5 a +1,2 pp**
          - Torrencial / tempestade / alagamento → **+1,2 a +3,0 pp**
        """
    )
    if not d["faixas_chuva"].empty:
        st.caption("Abstenção no 1º turno por faixa de chuva (30 maiores colégios, Bot 1)")
        tabela(d["faixas_chuva"], {
            "faixa_chuva": "Faixa de chuva", "n_municipios": "N", "media_precip_mm": "Precip. média (mm)",
            "pct_abst_ponderada": "Abstenção ponderada (%)", "mediana_pct_abst": "Mediana (%)"})

    st.subheader("Impacto estimado agora (cards da Visão Geral)")
    st.markdown(IA.METODO_TXT)
    st.caption(" · ".join(IA.COEF_FONTE.split("; ")))

    st.subheader("Principais limitações (declaradas)")
    st.markdown("\n".join(f"{i}. {t}" for i, t in enumerate(D.LIMITACOES, 1)))

    st.subheader("Política para sinais de redes sociais")
    st.markdown(D.DISCLAIMER_SOCIAL)

    st.subheader("Como interpretar os números")
    st.markdown(
        """
        - Todos os efeitos são **estimativas** com faixa de incerteza, não previsões determinísticas.
        - O objetivo do dashboard é informar o acompanhamento público com a melhor síntese possível a partir dos dados disponíveis até o momento.
        - Atualizações podem ocorrer ao longo do dia conforme novas observações meteorológicas e refinamentos dos bots.
        """
    )
    with st.expander("Ver síntese executiva completa do Bot 4"):
        st.markdown(sintese_impacto)
    with st.expander("Ver síntese do Bot 1 (correlação)"):
        st.markdown(sintese_correl)
    with st.expander("Ver resumo executivo do Bot 2 (clima)"):
        st.markdown(resumo_clima)

# -----------------------------------------------------------------------------
# Rodapé
# -----------------------------------------------------------------------------
st.markdown("---")
st.caption(
    f"Dashboard Chuva × Abstenção · 2º Turno 2026 · Dados atualizados em: {ts_atualizacao} (impacto) · "
    "Código MIT · Dados de análise CC BY 4.0 · Uso informativo — não constitui previsão eleitoral oficial."
)
