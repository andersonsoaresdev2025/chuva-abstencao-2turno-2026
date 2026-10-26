"""Comparação pós-eleição (data/resultado_2turno/): arquivos, site e dashboard."""
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
from streamlit.testing.v1 import AppTest

from common import dados as D
from common import resultado_2t as RES

ROOT = Path(__file__).resolve().parent.parent
APP = str(ROOT / "dashboard" / "app.py")
PAGINA = "Resultado oficial × estimativa"


def test_csv_304_linhas():
    df = RES.carregar_csv()
    assert len(df) == 304
    assert df["codigo_ibge"].is_unique
    for c in ("municipio", "uf", "aptos_2t", "variacao_descontada_media_uf_pp", "chuva_08_17h_mm_modelo",
              "efeito_estimado_pp_mid", "abstencoes_observadas_acima_media_uf_eleitores", "ajuste_noticias"):
        assert c in df.columns, c
    assert (df["ajuste_noticias"] == "sim").sum() == 9
    assert df["secoes_totalizadas_pct_2t"].min() == 100.0


def test_resumo_bate_com_csv():
    df, r = RES.carregar_csv(), RES.carregar_resumo()
    assert r["n_municipios"] == len(df) == 304
    assert r["aptos_cobertos_2t"] == int(df["aptos_2t"].sum())
    assert abs(r["soma_abst_acima_media_uf"] - df["abstencoes_observadas_acima_media_uf_eleitores"].sum()) <= 304
    assert sum(f["n"] for f in r["faixas_chuva"]) == 304
    assert len(r["ajustados"]) == 9 and len(r["capitais_destaque"]) == 6
    assert r["snapshot_estimativa"] == "2026-10-25 17:09 BRT"
    s = RES.inclinacao(r)
    assert s["lo"] > 0  # direção compatível (sem peso)
    assert RES.inclinacao(r, ponderado=True)["lo"] < 0 < RES.inclinacao(r, ponderado=True)["hi"]


def test_documentos_presentes_e_sem_travessao():
    for nome in ("CONCLUSAO.md", "README.md", "comparacao_municipios_2turno.md", "comparacao_municipios_2turno.pdf",
                 "grafico_chuva_vs_variacao.png", "grafico_estimado_vs_observado.png", "uf_variacao.csv"):
        assert (RES.DIR / nome).exists(), nome
    assert len(list((RES.DIR / "tse_2t" / "municipios").glob("*-u.json"))) == 304
    for nome in ("CONCLUSAO.md", "README.md", "comparacao_municipios_2turno.md"):
        assert "—" not in (RES.DIR / nome).read_text(encoding="utf-8"), nome
    conc = RES.carregar_conclusao()
    assert "](comparacao" not in conc and RES.BLOB in conc
    assert "sugestão para discussão" in conc


def test_estimativa_congelada():
    assert D.estimativa_congelada(datetime(2026, 10, 25, 20, 9, tzinfo=timezone.utc))
    assert not D.estimativa_congelada(datetime(2026, 10, 25, 10, 0, tzinfo=timezone.utc))
    assert not D.estimativa_congelada(None)


def test_site_pagina_e_destaque():
    import importlib.util
    spec = importlib.util.spec_from_file_location("build_site", ROOT / "scripts" / "build_site.py")
    bs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bs)
    pag = bs.build_resultado()
    assert "congelada às 17:09 BRT" in pag and 'id="estimativa-congelada"' in pag
    for k in ("comparacao_municipios_2turno.csv", "comparacao_municipios_2turno.pdf", "CONCLUSAO.md"):
        assert k in pag, k
    for sec in ("numeros", "graficos", "faixas", "capitais", "ajustes", "chuva30", "conclusao", "downloads"):
        assert f'id="{sec}"' in pag, sec
    assert "Barracão" in pag and "São Paulo" in pag and "Mogi Guaçu" in pag
    home = bs.secao_resultado_home()
    assert 'id="resultado-oficial"' in home and RES.SITE_PAGINA in home


def test_dashboard_pagina_resultado():
    st.cache_data.clear()
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception, [e.value for e in at.exception]
    assert PAGINA in at.sidebar.radio[0].options
    at.sidebar.radio[0].set_value(PAGINA).run()
    assert not at.exception, [e.value for e in at.exception]
    vals = [m.value for m in at.metric]
    assert len(vals) == 6 and "+0,34 p.p." in vals and "0,022 p.p./mm" in vals
    assert any("de 304 municípios" in c.value for c in at.caption)
    at.multiselect(key="res2t_uf").set_value(["PR"]).run()
    assert not at.exception
    assert any(c.value.startswith("22 de 304") for c in at.caption)
    at.checkbox(key="res2t_aj").check().run()
    assert any(c.value.startswith("4 de 304") for c in at.caption)
    assert any("Conclusão" in m.value for m in at.markdown)
