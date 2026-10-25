"""Página 'Notícias' e quadro 'Principais notícias agora': pasta ausente, vazia, fixture e dados reais."""
from pathlib import Path
import shutil

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from common import noticias as N

ROOT = Path(__file__).resolve().parent.parent
APP = str(ROOT / "dashboard" / "app.py")
FIXT = ROOT / "tests" / "fixtures" / "noticias"
REAL = ROOT / "data" / "noticias"


def _app():
    st.cache_data.clear()
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception, [e.value for e in at.exception]
    return at


def _textos(at):
    return " ".join(m.value for m in at.markdown) + " ".join(i.value for i in at.info)


@pytest.mark.parametrize("cenario", ["ausente", "vazia", "csv_vazio", "fixture"])
def test_pagina_noticias(cenario, tmp_path, monkeypatch):
    d = tmp_path / "noticias"
    if cenario == "vazia":
        d.mkdir()
    elif cenario == "csv_vazio":
        d.mkdir()
        (d / "noticias_consolidado.csv").write_text("", encoding="utf-8")
    elif cenario == "fixture":
        shutil.copytree(FIXT, d)
    monkeypatch.setattr(N, "NOTICIAS_DIR", d)
    at = _app()
    # Visão Geral: quadro de notícias presente
    assert any("Principais notícias agora" in h.value for h in at.subheader)
    at.sidebar.radio[0].set_value("Notícias").run()
    assert not at.exception, [e.value for e in at.exception]
    assert any("Não são dados oficiais" in w.value for w in at.warning)
    if cenario == "fixture":
        assert len(at.dataframe) >= 1
        assert len(at.multiselect) >= 4  # região, UF, tema, abrangência
    else:
        assert any("Ainda não há notícias" in i.value for i in at.info)


def test_principais_filtra_sinalizados_e_duplicados():
    df = N.carregar_noticias(FIXT)
    assert len(df) == 3  # link duplicado removido
    top = N.principais(df, 8)
    assert list(top["id"]) == ["t-001", "t-002"]  # item sinalizado/fora da lista excluído
    assert df.loc[df["id"] == "t-003", "alerta"].item()


def test_carregar_ausente(tmp_path):
    assert N.carregar_noticias(tmp_path / "nada").empty
    assert N.principais(N.carregar_noticias(tmp_path / "nada")).empty
    assert N.ultima_coleta(N.carregar_noticias(tmp_path / "nada")) == "—"


@pytest.mark.skipif(not (REAL / "noticias_consolidado.csv").exists(), reason="sem coleta real")
def test_dados_reais_schema_e_links():
    df = N.carregar_noticias(REAL)
    assert not df.empty
    assert set(N.COLS) <= set(df.columns)
    assert df["link"].str.startswith("http").all()
    assert df["publicado_brt"].str[:10].isin(["2026-10-24", "2026-10-25"]).all()
    portais = N.carregar_portais(REAL)
    assert len(portais) >= 20 and (portais["status_http_home"] == "200").all()
    at = _app()
    at.sidebar.radio[0].set_value("Notícias").run()
    assert not at.exception
    assert len(at.dataframe) >= 2  # tabela + portais
