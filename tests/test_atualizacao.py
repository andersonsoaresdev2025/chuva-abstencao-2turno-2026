"""Atualização automática (papéis dos Bots 0–4 executados por scripts), com a rede 100% mockada:
regras a/b/c, ajustes por notícias, atualizar_clima (Open-Meteo/INMET e fallbacks), atualizar_impacto,
impacto agora (só previsão × previsão + notícias), coleta social (X/Instagram) e dashboard/site."""
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from common import dados as D
from common import impacto_agora as IA
from common import regras as R

ROOT = Path(__file__).resolve().parent.parent
APP = str(ROOT / "dashboard" / "app.py")
AGORA = datetime(2026, 10, 25, 10, 0, tzinfo=timezone.utc)  # 07:00 BRT (antes da votação)
SP, CAMPINAS, RIO, PARATY, CURITIBA = 3550308, 3509502, 3304557, 3303807, 4106902


def _mod(nome):
    spec = importlib.util.spec_from_file_location(nome, ROOT / "scripts" / f"{nome}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


CL, IMP, SOC = _mod("atualizar_clima"), _mod("atualizar_impacto"), _mod("coletar_social")


# ---------------------------------------------------------------- mocks de rede
class Resp:
    def __init__(self, status=200, js=None, text=""):
        self.status_code, self._js, self.text = status, js, text

    def json(self):
        return self._js

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class Sessao:
    """Roteia por prefixo de URL; registra as chamadas."""
    def __init__(self, rotas):
        self.rotas, self.chamadas = rotas, []

    def get(self, url, **k):
        self.chamadas.append(url)
        for pref, r in self.rotas.items():
            if url.startswith(pref):
                if isinstance(r, Exception):
                    raise r
                return r
        raise ConnectionError(f"sem rota mock: {url}")


AVISOS_JSON = {"hoje": [
    {"id": 999, "descricao": "Tempestade", "severidade": "Perigo", "inicio": "2026-10-25 00:00:00.0",
     "fim": "2026-10-25 23:59:00.0", "estados": "SP", "geocodes": f"{CAMPINAS},3500105"},
    {"id": 998, "descricao": "Baixa Umidade", "severidade": "Grande Perigo", "inicio": "2026-10-25 00:00:00.0",
     "fim": "2026-10-25 23:59:00.0", "estados": "MT", "geocodes": str(SP)},
], "futuro": []}
RSS = """<rss><channel><item><title>Aviso de Tempestade. Severidade Grau: Perigo</title>
<link>https://alertas2.inmet.gov.br/999</link><description>x</description></item></channel></rss>"""


def _buscar_fake(lats, lons):
    geo = D.read_csv(D.GEO_FILE).set_index("codigo_ibge")
    sp = (geo.loc[SP, "latitude"], geo.loc[SP, "longitude"])
    out = []
    for la, lo in zip(lats, lons):
        chuva = abs(la - sp[0]) < 1e-3 and abs(lo - sp[1]) < 1e-3
        out.append({"precip": {h: (4.0 if chuva and 9 <= h <= 17 else 0.0) for h in range(24)},
                    "prob": {h: 80.0 if chuva else 5.0 for h in range(24)}})
    return out


def _falha(*a, **k):
    raise ConnectionError("rede mockada: falha")


@pytest.fixture
def ambiente(tmp_path, monkeypatch):
    """Pastas temporárias de saída + ajustes por notícias de teste."""
    monkeypatch.setattr(D, "ATUAL_CLIMA_DIR", tmp_path / "clima")
    monkeypatch.setattr(D, "ATUAL_IMPACTO_DIR", tmp_path / "impacto")
    monkeypatch.setenv("CHUVA_SNAPSHOT_REMOTO", "0")  # testes nunca leem o snapshot do GitHub
    aj = tmp_path / "ajustes.csv"
    pd.DataFrame([
        # município fora das listas (existe no TSE 1º turno) → entra no cálculo
        {"timestamp_brt": "2026-10-25 11:00 BRT", "codigo_ibge": PARATY, "municipio": "Paraty", "uf": "RJ",
         "nivel_risco_ajustado": "a", "intensidade_estimada_mm": 25, "evidencia": "alagamento perto de seções",
         "fontes": "https://exemplo.org/a", "confianca": "media", "status": "ativo", "autor": "teste"},
        {"timestamp_brt": "2026-10-25 11:00 BRT", "codigo_ibge": RIO, "municipio": "Rio de Janeiro", "uf": "RJ",
         "nivel_risco_ajustado": "b", "intensidade_estimada_mm": "", "evidencia": "chuva moderada relatada",
         "fontes": "https://exemplo.org/b", "confianca": "baixa", "status": "ativo", "autor": "teste"},
        # ajuste revogado depois → não vale
        {"timestamp_brt": "2026-10-25 10:00 BRT", "codigo_ibge": CURITIBA, "municipio": "Curitiba", "uf": "PR",
         "nivel_risco_ajustado": "a", "intensidade_estimada_mm": 40, "evidencia": "x", "fontes": "https://e/c",
         "confianca": "alta", "status": "ativo", "autor": "teste"},
        {"timestamp_brt": "2026-10-25 10:30 BRT", "codigo_ibge": CURITIBA, "municipio": "Curitiba", "uf": "PR",
         "nivel_risco_ajustado": "a", "intensidade_estimada_mm": 40, "evidencia": "x", "fontes": "https://e/c",
         "confianca": "alta", "status": "revogado", "autor": "teste"},
    ], columns=R.AJUSTES_COLS).to_csv(aj, index=False)
    monkeypatch.setattr(D, "AJUSTES_FILE", aj)
    return tmp_path


def _rodar_clima(buscar=_buscar_fake, sessao=None, agora=AGORA):
    sessao = sessao or Sessao({CL.INMET_JSON: Resp(js=AVISOS_JSON)})
    return CL.executar(agora, buscar=buscar, sessao=sessao)


# ---------------------------------------------------------------- regras
def test_regras_classificacao():
    assert R.classificar(25) == "a" and R.classificar(20) == "a"
    assert R.classificar(5) == "b" and R.classificar(19.9) == "b"
    assert R.classificar(4.9) == "c"
    assert R.classificar(1, "laranja") == "b" and R.classificar(6, "vermelho") == "a"
    assert R.classificar(1, "amarelo") == "c"          # amarelo não eleva
    assert R.maior("c", "a", None) == "a" and R.letra("a (torrencial)") == "a"
    assert R.efeito("a") == (2.0, 1.2, 3.0)
    assert R.mais_prejudicado(50.5, 50.0) == "Equilibrado / incerto"


def test_ajustes_ativos(ambiente):
    aj = D.carregar_ajustes()
    assert set(aj["codigo_ibge"]) == {PARATY, RIO}      # Curitiba revogado
    rio = aj.set_index("codigo_ibge").loc[RIO]
    assert rio["mm_ajuste"] == R.MM_PISO_AJUSTE["b"]   # sem intensidade → piso da classe
    assert aj.set_index("codigo_ibge").loc[PARATY, "mm_ajuste"] == 25
    assert R.ajustes_ativos(pd.DataFrame()).empty


# ---------------------------------------------------------------- clima (papel Bot 2)
def test_atualizar_clima_ok(ambiente):
    r = _rodar_clima()
    mun = r["municipios"].set_index("codigo_ibge")
    assert r["status"]["open_meteo"]["status"] == "ok" and r["status"]["inmet"]["status"] == "ok"
    assert mun.loc[SP, "nivel_risco"] == "a" and mun.loc[SP, "precipitacao_mm_estimada"] == pytest.approx(36, abs=.1)
    assert mun.loc[CAMPINAS, "nivel_risco"] == "b"                    # 0 mm + aviso laranja de tempestade
    assert "INMET laranja" in mun.loc[CAMPINAS, "alerta_inmet"]
    assert mun.loc[RIO, "nivel_risco"] == "b" and mun.loc[RIO, "ajuste_noticias"] == "sim"   # piso por notícias
    assert mun.loc[RIO, "nivel_risco_previsao"] == "c"
    assert PARATY in mun.index and mun.loc[PARATY, "nivel_risco"] == "a"   # fora das listas, via ajuste
    assert mun.loc[CURITIBA, "ajuste_noticias"] == "não"
    assert mun.loc[SP, "mudanca_vs_manha"] in ("igual", "subiu", "desceu") or "→" in str(mun.loc[SP, "mudanca_vs_manha"])
    od = D.ATUAL_CLIMA_DIR
    for f in ("risco_chuva_municipios_latest.csv", "risco_chuva_estados_latest.csv", "risco_chuva_regioes_latest.csv",
              "precip_horaria_latest.csv", "status_latest.json", "resumo_latest.md", "inmet_avisos_latest.json",
              "risco_chuva_municipios_20261025_1000UTC.csv"):
        assert (od / f).exists(), f
    assert "Mudanças" in (od / "resumo_latest.md").read_text(encoding="utf-8") or \
        "manhã" in (od / "resumo_latest.md").read_text(encoding="utf-8")
    # original do Bot 2 intocado
    assert len(D.read_csv(D.CLIMA_DIR / "risco_chuva_municipios.csv")) == 29


def test_inmet_fallbacks(ambiente):
    od = D.ATUAL_CLIMA_DIR
    od.mkdir(parents=True)
    # JSON falha, RSS ok, sem cache → RSS sem geocódigos + marcações do Bot 2
    s = Sessao({CL.INMET_JSON: Resp(503), CL.INMET_RSS: Resp(text=RSS)})
    a = CL.obter_avisos(AGORA, s)
    assert a["status"] == "rss_sem_geocodigos" and a["avisos"][0]["severidade"] == "laranja"
    # com cache válido do JSON → usa o cache, marcado stale
    _rodar_clima()
    a = CL.obter_avisos(AGORA, Sessao({}))
    assert a["status"] == "stale" and a["tem_geocodes"] and "cache" in a["fonte"]
    # tudo fora e sem cache → stale, nenhum aviso inventado
    (od / "inmet_avisos_latest.json").unlink()
    a = CL.obter_avisos(AGORA, Sessao({}))
    assert a["status"] == "stale" and a["avisos"] == []


def test_open_meteo_falha_mantem_ultimo_valido(ambiente):
    _rodar_clima()
    antes = D.read_csv(D.ATUAL_CLIMA_DIR / "risco_chuva_municipios_latest.csv").set_index("codigo_ibge")
    depois_t = datetime(2026, 10, 25, 10, 30, tzinfo=timezone.utc)
    r = _rodar_clima(buscar=_falha, agora=depois_t)
    m = r["municipios"].set_index("codigo_ibge")
    assert r["status"]["open_meteo"]["status"] == "falha" and r["status"]["arquivo_versionado"] is None
    assert m.loc[SP, "nivel_risco"] == antes.loc[SP, "nivel_risco"] == "a"
    assert m.loc[SP, "precipitacao_mm_estimada"] == antes.loc[SP, "precipitacao_mm_estimada"]
    assert str(m.loc[SP, "status_dado"]).startswith("stale")
    assert not (D.ATUAL_CLIMA_DIR / "risco_chuva_municipios_20261025_1030UTC.csv").exists()


def test_open_meteo_mock_http_lotes():
    """buscar_open_meteo com sessão mockada: lotes, convenção horária e erro 429."""
    def js(n):
        t = [f"2026-10-25T{h:02d}:00" for h in range(24)]
        return [{"hourly": {"time": t, "precipitation": [1.0] * 24, "precipitation_probability": [50] * 24}}] * n

    class S:
        def __init__(self):
            self.n = 0

        def get(self, url, params=None, **k):
            self.n += 1
            return Resp(js=js(len(params["latitude"].split(","))))
    s = S()
    res = CL.buscar_open_meteo([-23.0] * 120, [-46.0] * 120, sessao=s)
    assert len(res) == 120 and s.n == 3 and res[0]["precip"][9] == 1.0
    with pytest.raises(RuntimeError):
        CL.buscar_open_meteo([-23.0], [-46.0], sessao=Sessao({CL.OPEN_METEO_URL: Resp(429)}), tentativas=1)


# ---------------------------------------------------------------- impacto (papel Bot 4) + impacto agora
def test_atualizar_impacto_e_agora_duplo(ambiente):
    _rodar_clima()
    r = IMP.executar(AGORA)
    mun = r["municipios"].set_index("codigo_ibge")
    assert mun.loc[SP, "efeito_abstencao_pp_mid"] == 2.0
    assert mun.loc[PARATY, "ajuste_noticias"] == "sim" and mun.loc[PARATY, "efeito_abstencao_pp_mid"] == 2.0
    # Paraty: Flávio teve a maior fatia no 1º turno → mais prejudicado
    assert "Flávio" in mun.loc[PARATY, "mais_prejudicado"]
    od = D.ATUAL_IMPACTO_DIR
    snap = json.loads((od / "impacto_agora_latest.json").read_text(encoding="utf-8"))
    assert snap["n_ajustes_ativos"] == 2
    p, pn = snap["previsao"], snap["previsao_mais_noticias"]
    assert pn["abstencao_nacional_pp"]["mid"] > p["abstencao_nacional_pp"]["mid"]   # notícias somam chuva
    assert (od / "impacto_agora_historico.csv").exists()
    for f in ("impacto_municipios_latest.csv", "impacto_estados_latest.csv", "impacto_regioes_latest.csv"):
        assert (od / f).exists()


def test_impacto_agora_ajuste_fora_da_cobertura(ambiente):
    _rodar_clima()
    d = IA.calcular_duplo(AGORA)
    so, com = d["previsao"], d["previsao_mais_noticias"]
    assert d["n_ajustes_ativos"] == 2 and com["n_ajustes_noticias"] == 2
    par = com["municipios"][com["municipios"]["codigo_ibge"] == PARATY]
    assert len(par) == 1 and par.iloc[0]["precip_usado_mm"] == 25 and par.iloc[0]["precip_acum_mm"] == 0
    assert com["votos_perdidos_flavio"]["mid"] > so["votos_perdidos_flavio"]["mid"]
    # cobertura padrão (15 maiores colégios, sem Paraty): o ajuste anexa o município com os votos do 1º turno
    r = IA.calcular(AGORA, cid=IA.cidades_cobertas(), ajustes=D.carregar_ajustes())
    assert r["n_municipios_cobertos"] == 15 and r["n_municipios_extras_ajuste"] == 1
    par = r["municipios"][r["municipios"]["codigo_ibge"] == PARATY].iloc[0]
    red = D.read_csv(D.REDUTOS_DIR / "redutos_municipios.csv").set_index("cd_ibge").loc[PARATY]
    assert par["pct_flavio_1t"] == red["pct_flavio"] and par["aptos"] == red["aptos"]
    assert r["votos_perdidos_flavio"]["mid"] > IA.calcular(AGORA, cid=IA.cidades_cobertas())["votos_perdidos_flavio"]["mid"]


def test_ajuste_municipio_inexistente_no_tse_e_ignorado(ambiente, monkeypatch):
    aj = pd.DataFrame([{"timestamp_brt": "2026-10-25 11:00 BRT", "codigo_ibge": 9999999, "municipio": "Inventada",
                        "uf": "XX", "nivel_risco_ajustado": "a", "intensidade_estimada_mm": 50, "evidencia": "-",
                        "fontes": "-", "confianca": "baixa", "status": "ativo", "autor": "t"}])
    cid = IA._aplicar_ajustes(IA.cidades_cobertas().assign(precip_acum_mm=0.0), R.ajustes_ativos(aj))
    assert 9999999 not in set(pd.to_numeric(cid["codigo_ibge"], errors="coerce").dropna().astype(int))


# ---------------------------------------------------------------- social (X / Instagram)
DDG_HTML = """<div class="result results_links"><a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.instagram.com%2Fp%2Fabc%2F">
Chuva forte alaga local de votação em Guarulhos</a><a class="result__snippet">Eleitores enfrentam alagamento para votar no segundo turno</a></div>
<div class="result results_links"><a class="result__a" href="https://www.instagram.com/defesacivilsp/">Defesa Civil SP</a>
<a class="result__snippet">Temporal: atenção eleitores, votação segue</a></div>
<div class="result results_links"><a class="result__a" href="https://www.instagram.com/p/old/">Chuva eleição 2022</a>
<a class="result__snippet">chuva no dia da votação de 2022</a></div>"""


def test_parse_e_relevancia():
    res = SOC.parse_ddg_html(DDG_HTML)
    assert res[0]["link"] == "https://www.instagram.com/p/abc/"
    assert SOC.relevante(res[0]["titulo"] + " " + res[0]["trecho"])[0]
    assert not SOC.relevante(res[2]["titulo"] + " " + res[2]["trecho"])[0]   # outro ano
    assert SOC.conta_instagram("https://www.instagram.com/defesacivilsp/") == "defesacivilsp"
    with pytest.raises(SOC.Bloqueado):
        SOC.parse_ddg_html("<html>anomaly detected</html>")


@pytest.fixture
def social_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(D, "SOCIAL_DIR", tmp_path / "social")
    monkeypatch.delenv("X_BEARER_TOKEN", raising=False)
    monkeypatch.delenv("TWITTER_BEARER_TOKEN", raising=False)
    return tmp_path / "social"


def test_coleta_social_instagram_sem_x(social_tmp):
    s = Sessao({"https://html.duckduckgo.com": Resp(text=DDG_HTML)})
    r = SOC.executar(AGORA, sessao=s, pausa=0)
    assert not any("twitter.com" in u for u in s.chamadas)            # sem credencial → X pulado
    log = pd.read_csv(social_tmp / "log_coleta_social.csv")
    assert ((log["rede"] == "x") & (log["status"] == "pulado")).any()
    ig = [x for x in r["sinais"] if x["rede"] == "instagram"]
    assert ig and all(x["confianca"] in ("baixa", "media") for x in ig)
    of = [x for x in ig if "defesacivilsp" in x["link"]]
    assert of and of[0]["confianca"] == "media" and of[0]["tipo_fonte"] == "oficial"
    assert [x for x in ig if "/p/abc/" in x["link"]][0]["confianca"] == "baixa"
    df = D.carregar_social()
    assert set(df["rede"]) == {"instagram"} and df["link"].is_unique
    SOC.executar(AGORA, sessao=s, pausa=0)                              # deduplica por link
    assert len(D.carregar_social()) == len(df)


def test_coleta_social_bloqueada_registra(social_tmp):
    s = Sessao({"https://html.duckduckgo.com": Resp(202, text="anomaly"), "https://lite.duckduckgo.com": Resp(202),
                "https://search.brave.com": Resp(429)})
    r = SOC.executar(AGORA, sessao=s, pausa=0)
    assert r["sinais"] == [] and r["novos"] == 0
    log = pd.read_csv(social_tmp / "log_coleta_social.csv")
    assert (log["status"] == "bloqueado").any() and (log["status"] == "nada_encontrado").any()


def test_coleta_x_com_token_mockado(social_tmp, monkeypatch):
    monkeypatch.setenv("X_BEARER_TOKEN", "fake-token-de-teste")
    js = {"data": [{"id": "1", "text": "Alagamento na porta da seção eleitoral em Osasco, difícil votar",
                    "author_id": "u1", "created_at": "2026-10-25T11:00:00Z"}],
          "includes": {"users": [{"id": "u1", "username": "fulano"}]}}
    s = Sessao({"https://api.twitter.com": Resp(js=js), "https://html.duckduckgo.com": Resp(202, text="anomaly"),
                "https://lite.duckduckgo.com": Resp(202), "https://search.brave.com": Resp(429)})
    r = SOC.executar(AGORA, sessao=s, pausa=0)
    x = [i for i in r["sinais"] if i["rede"] == "x"]
    assert x and x[0]["link"] == "https://x.com/fulano/status/1" and x[0]["confianca"] == "baixa"


def test_rede_inferida_em_arquivo_antigo(social_tmp):
    social_tmp.mkdir(parents=True)
    cols = [c for c in D.SOCIAL_COLS if c != "rede"]
    pd.DataFrame([{**{c: "" for c in cols}, "link": "https://x.com/a/status/1", "cidade": "A"},
                  {**{c: "" for c in cols}, "link": "https://www.instagram.com/p/z/", "cidade": "B"},
                  {**{c: "" for c in cols}, "link": "https://g1.globo.com/x", "cidade": "C"}]).to_csv(
        social_tmp / "sinais_20261025_0900UTC.csv", index=False)
    df = D.carregar_social().set_index("cidade")
    assert df.loc["A", "rede"] == "x" and df.loc["B", "rede"] == "instagram" and df.loc["C", "rede"] == "web"


# ---------------------------------------------------------------- dashboard e site com *_latest + ajustes
def test_dashboard_com_latest_e_ajustes(ambiente, social_tmp):
    _rodar_clima()
    IMP.executar(AGORA)
    SOC.executar(AGORA, sessao=Sessao({"https://html.duckduckgo.com": Resp(text=DDG_HTML)}), pausa=0)
    d = D.carregar_tudo()
    assert d["_origem"]["risco_mun"] == "atualizado" and d["_origem"]["impacto_mun"] == "atualizado"
    assert D.ts_camada(d, "risco").startswith("2026-10-25 07:00")
    st.cache_data.clear()
    at = AppTest.from_file(APP, default_timeout=90).run()
    assert not at.exception, [e.value for e in at.exception]
    for p in at.sidebar.radio[0].options:
        at.sidebar.radio[0].set_value(p).run()
        assert not at.exception, (p, [e.value for e in at.exception])
        txt = " ".join(str(getattr(e, "value", "")) for e in list(at.markdown) + list(at.caption) + list(at.info))
        if p == "Risco de Chuva":
            assert "O que mudou desde a manhã" in " ".join(s.value for s in at.subheader)
        if p in ("Visão Geral", "Risco de Chuva", "Impacto na Abstenção"):
            assert "ajuste por notícias" in txt.lower(), p
    at.sidebar.radio[0].set_value("Sinais Sociais").run()
    ms = [m for m in at.multiselect if m.label == "Rede"][0]
    ms.set_value(["X"]).run()
    assert not at.exception
    ms = [m for m in at.multiselect if m.label == "Rede"][0]
    ms.set_value(["Instagram"]).run()
    assert not at.exception and len(at.dataframe) >= 1


def test_site_mostra_timestamp_e_ajustes(ambiente, social_tmp):
    _rodar_clima()
    IMP.executar(AGORA)
    bs = _mod("build_site")
    html = bs.build()
    assert 'id="atualizado"' in html and "2026-10-25 07:00 BRT" in html
    assert "Ajustes por notícias (2 ativos)" in html and "https://exemplo.org/a" in html
    assert "O que mudou desde a manhã" in html and "Previsão + notícias" in html


def test_destaque_votos_perdidos_previsao_mais_noticias(ambiente, social_tmp):
    _rodar_clima()
    d = IMP.executar(AGORA)["agora"]  # o dashboard mostra o snapshot publicado
    st.cache_data.clear()
    at = AppTest.from_file(APP, default_timeout=90).run()
    assert not at.exception, [e.value for e in at.exception]
    labels = {m.label: m for m in at.metric}
    mf = labels["Flávio Bolsonaro — votos perdidos (previsão + notícias)"]
    ml = labels["Lula — votos perdidos (previsão + notícias)"]
    fmt = lambda x: f"{int(round(x, -2)):,}".replace(",", ".")  # noqa: E731
    assert mf.value == fmt(d["previsao_mais_noticias"]["votos_perdidos_flavio"]["mid"])
    assert ml.value == fmt(d["previsao_mais_noticias"]["votos_perdidos_lula"]["mid"])
    assert "vs só previsão" in mf.delta
    assert {"Flávio (p.p.)", "Lula (p.p.)", "Margem Lula − Flávio"} <= set(labels)
    html = _mod("build_site").build()
    assert 'id="votos-perdidos"' in html and "Flávio Bolsonaro — votos perdidos (previsão + notícias)" in html


def test_site_e_dashboard_iguais_ao_snapshot(ambiente, social_tmp, monkeypatch):
    """Fonte única: manchete do site e do dashboard = impacto_agora_latest.json (sem recálculo próprio)."""
    import json
    _rodar_clima()
    IMP.executar(AGORA)
    snap = json.loads((D.ATUAL_IMPACTO_DIR / "impacto_agora_latest.json").read_text(encoding="utf-8"))
    rn = snap["previsao_mais_noticias"]
    fmt = lambda x: f"{int(round(x, -2)):,}".replace(",", ".")  # noqa: E731
    vf, vl = fmt(rn["votos_perdidos_flavio"]["mid"]), fmt(rn["votos_perdidos_lula"]["mid"])
    # se alguém recalculasse "agora", o resultado seria outro: força isso a falhar
    monkeypatch.setattr(IA, "calcular_duplo", lambda *a, **k: (_ for _ in ()).throw(AssertionError("recalculou")))
    html = _mod("build_site").build()
    assert vf in html and vl in html and "Snapshot de 07:00 BRT" in html and "próxima atualização ~07:30 BRT" in html
    vc = _mod("verificar_consistencia")
    assert vc.verificar(html, IA.carregar_snapshot(remoto=False)) == []
    st.cache_data.clear()
    at = AppTest.from_file(APP, default_timeout=90).run()
    assert not at.exception, [e.value for e in at.exception]
    labels = {m.label: m for m in at.metric}
    assert labels["Flávio Bolsonaro — votos perdidos (previsão + notícias)"].value == vf
    assert labels["Lula — votos perdidos (previsão + notícias)"].value == vl
    assert any("Snapshot de 07:00 BRT" in i.value and "~07:30 BRT" in i.value for i in at.info)


def test_snapshot_remoto_mais_novo_vence(ambiente):
    _rodar_clima()
    IMP.executar(AGORA)
    loc = IA.carregar_snapshot(remoto=False)

    class S:
        def get(self, url, timeout=None):
            d = dict(loc)
            d["gerado_em_utc"] = "2026-10-25T12:44:00+00:00"
            return Resp(js=d)
    r = IA.carregar_snapshot(remoto=True, sessao=S())
    assert r["_origem_snapshot"].startswith("GitHub") and r["snapshot_hhmm_brt"] == "09:44"
    assert r["proxima_atualizacao_hhmm_brt"] == "10:14"

    class Falha:
        def get(self, *a, **k):
            raise ConnectionError("x")
    assert IA.carregar_snapshot(remoto=True, sessao=Falha())["_origem_snapshot"].startswith("arquivo")
