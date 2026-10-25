import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _sem_rede(monkeypatch):
    """Por padrão, os testes não acessam a API Open-Meteo (simula falha -> fallback CSV)."""
    from common import impacto_agora as IA

    def _falha(*a, **k):
        raise ConnectionError("rede desativada nos testes")
    monkeypatch.setattr(IA, "buscar_open_meteo", _falha)
