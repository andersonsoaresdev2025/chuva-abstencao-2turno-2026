import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _sem_rede(monkeypatch, tmp_path_factory):
    """Por padrão, os testes não acessam a rede (Open-Meteo simula falha -> fallback CSV) e não enxergam
    os arquivos da atualização automática nem os ajustes reais (pastas vazias temporárias), para que os
    testes antigos continuem determinísticos. Testes das atualizações usam fixtures próprias."""
    from common import dados as D
    from common import impacto_agora as IA

    def _falha(*a, **k):
        raise ConnectionError("rede desativada nos testes")
    monkeypatch.setattr(IA, "buscar_open_meteo", _falha)
    base = tmp_path_factory.mktemp("auto_vazio")
    monkeypatch.setattr(D, "ATUAL_CLIMA_DIR", base / "clima_atualizacoes")
    monkeypatch.setattr(D, "ATUAL_IMPACTO_DIR", base / "impacto_atualizacoes")
    monkeypatch.setattr(D, "AJUSTES_FILE", base / "ajustes" / "ajustes_impacto_noticias.csv")


@pytest.fixture(autouse=True)
def _sem_snapshot_remoto(monkeypatch):
    """Testes nunca leem o snapshot do GitHub (só o arquivo local)."""
    monkeypatch.setenv("CHUVA_SNAPSHOT_REMOTO", "0")
