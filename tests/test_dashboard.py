"""Exercita todas as páginas do dashboard com streamlit.testing (AppTest)
em três cenários: sem pasta data/social, pasta vazia e pasta com sinais (fixture fictícia)."""
from pathlib import Path
import shutil

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from common import dados as D

ROOT = Path(__file__).resolve().parent.parent
APP = str(ROOT / "dashboard" / "app.py")
FIXT = ROOT / "tests" / "fixtures" / "social"


def _rodar_todas_paginas():
    st.cache_data.clear()
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception, [e.value for e in at.exception]
    paginas = at.sidebar.radio[0].options
    assert "Sinais Sociais" in paginas
    resultados = {}
    for p in paginas:
        at.sidebar.radio[0].set_value(p).run()
        assert not at.exception, (p, [e.value for e in at.exception])
        resultados[p] = at
        # timestamp sempre visível
        assert any("Dados atualizados em" in i.value for i in at.info), p
    return at, paginas


@pytest.mark.parametrize("cenario", ["ausente", "vazia", "com_sinais"])
def test_paginas(cenario, tmp_path, monkeypatch):
    social = tmp_path / "social"
    if cenario == "vazia":
        social.mkdir()
    elif cenario == "com_sinais":
        shutil.copytree(FIXT, social)
    monkeypatch.setattr(D, "SOCIAL_DIR", social)
    at, paginas = _rodar_todas_paginas()
    at.sidebar.radio[0].set_value("Sinais Sociais").run()
    assert not at.exception
    if cenario == "com_sinais":
        assert len(at.dataframe) >= 1
        df = D.carregar_social()
        assert len(df) == 2  # duplicado por link removido
    else:
        assert any("Ainda não há sinais sociais" in i.value for i in at.info)
