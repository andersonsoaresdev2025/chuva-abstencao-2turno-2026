"""Testes do 'Impacto estimado agora': fallback quando a API falha, API mockada e sanidade numérica."""
from datetime import datetime, timezone
from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from common import impacto_agora as IA

ROOT = Path(__file__).resolve().parent.parent
APP = str(ROOT / "dashboard" / "app.py")
UTC = timezone.utc
MOMENTOS = {
    "antes": datetime(2026, 10, 25, 10, 0, tzinfo=UTC),   # 07:00 BRT
    "durante": datetime(2026, 10, 25, 15, 30, tzinfo=UTC),  # 12:30 BRT
    "depois": datetime(2026, 10, 25, 21, 0, tzinfo=UTC),  # 18:00 BRT
}


def _falha(*a, **k):
    raise ConnectionError("API indisponível (simulado)")


def _serie_fake(lats, lons):
    # 1 mm em toda hora do dia, para todos os locais
    return [{h: 1.0 for h in range(24)} for _ in lats]


def _checa_sanidade(r):
    for k in ("flavio_pp", "lula_pp", "margem_lula_menos_flavio_pp", "votos_perdidos_flavio",
              "votos_perdidos_lula", "abstencao_nacional_pp"):
        assert r[k]["min"] <= r[k]["mid"] <= r[k]["max"], k
    for k in ("flavio_pp", "lula_pp", "margem_lula_menos_flavio_pp"):
        assert abs(r[k]["max"]) < 0.5 and abs(r[k]["min"]) < 0.5, (k, r[k])  # efeito pequeno
    assert abs(r["flavio_pp"]["mid"] + r["lula_pp"]["mid"]) < 1e-9
    assert 0 <= r["abstencao_nacional_pp"]["min"] and r["abstencao_nacional_pp"]["max"] < 1
    assert r["votos_perdidos_flavio"]["min"] >= 0 and r["votos_perdidos_lula"]["min"] >= 0
    assert 0 < r["cobertura_pct_eleitorado"] < 100
    assert r["n_municipios_cobertos"] == 15


@pytest.mark.parametrize("momento", list(MOMENTOS))
def test_fallback_quando_api_falha(momento):
    r = IA.calcular_com_api(MOMENTOS[momento], buscar=_falha)
    assert r["usou_fallback"] and "fallback" in r["fonte_precipitacao"]
    assert "ConnectionError" in r["erro_api"]
    _checa_sanidade(r)
    assert r["modo"] == {"antes": "projecao", "durante": "agora", "depois": "final"}[momento]


def test_modos_e_monotonicidade():
    a = IA.calcular(MOMENTOS["antes"])
    d = IA.calcular(MOMENTOS["durante"])
    f = IA.calcular(MOMENTOS["depois"])
    assert a["rotulo"].startswith("projeção") and f["rotulo"] == "estimativa final do dia"
    # projeção (dia inteiro) == final; durante é parcial
    assert a["abstencoes_extras"]["mid"] == pytest.approx(f["abstencoes_extras"]["mid"])
    assert d["abstencoes_extras"]["mid"] <= f["abstencoes_extras"]["mid"]
    assert d["horas_decorridas"] == pytest.approx(4.5)


def test_api_mockada_open_meteo():
    r = IA.calcular_com_api(MOMENTOS["durante"], buscar=_serie_fake)
    assert not r["usou_fallback"] and r["fonte_precipitacao"].startswith("Open-Meteo")
    assert (r["municipios"]["precip_acum_mm"] == 4.5).all()  # 4,5 h × 1 mm
    _checa_sanidade(r)
    # conferência aritmética independente da abstenção extra (mid)
    m = r["municipios"]
    esperado = (m["aptos"] * 4.5 * 0.07 / 100).sum()
    assert r["abstencoes_extras"]["mid"] == pytest.approx(esperado)


def test_convencao_open_meteo():
    serie = {h: float(h) for h in range(24)}  # rótulo HH = hora anterior
    assert IA.acumulado_open_meteo(serie, 1.0) == 9.0      # 08–09h = rótulo 09
    assert IA.acumulado_open_meteo(serie, 9.0) == sum(range(9, 18))
    assert IA.acumulado_open_meteo(serie, 0.5) == 4.5


@pytest.mark.parametrize("buscar", [_falha, _serie_fake])
def test_app_card_visao_geral(buscar, monkeypatch):
    monkeypatch.setattr(IA, "buscar_open_meteo", buscar)
    import importlib.util
    spec = importlib.util.spec_from_file_location("atualizar_impacto", ROOT / "scripts" / "atualizar_impacto.py")
    imp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(imp)
    imp.executar(MOMENTOS["durante"])  # snapshot publicado (pasta temporária)
    st.cache_data.clear()
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception, [e.value for e in at.exception]
    assert any("Impacto estimado agora" in s.value for s in at.subheader)
    labels = [m.label for m in at.metric]
    assert any(l.startswith("Flávio") for l in labels) and any(l.startswith("Lula") for l in labels)
    assert any("Cobertura" in l for l in labels)
    # manchete = snapshot publicado (mesmo arquivo do site), com horário e próxima atualização
    assert any("Snapshot de" in i.value and "próxima atualização" in i.value for i in at.info)
    # recálculo ao vivo só sob demanda, claramente rotulado
    at.button(key="recalc_vivo").click().run()
    assert not at.exception, [e.value for e in at.exception]
    vivos = [m for m in at.metric if "recálculo ao vivo" in m.label]
    assert len(vivos) == 2
    caps = " ".join(c.value for c in at.caption)
    assert "Recálculo ao vivo às" in caps and "BRT" in caps
