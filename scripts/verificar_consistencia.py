#!/usr/bin/env python3
"""Confere que docs/index.html mostra exatamente os números do snapshot publicado
(data/impacto/atualizacoes/impacto_agora_latest.json) – a mesma fonte lida pelo dashboard."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from common import impacto_agora as IA  # noqa: E402


def fmt(x: float) -> str:
    return f"{int(round(float(x), -2)):,}".replace(",", ".")


def valores_esperados(snap: dict) -> list[str]:
    rn = snap.get("previsao_mais_noticias") or snap["previsao"]
    return [fmt(rn["votos_perdidos_flavio"]["mid"]), fmt(rn["votos_perdidos_lula"]["mid"]),
            f"Snapshot de {snap['snapshot_hhmm_brt']} BRT"]


def verificar(html: str, snap: dict) -> list[str]:
    return [v for v in valores_esperados(snap) if v not in html]


def main() -> int:
    snap = IA.carregar_snapshot(remoto=False)
    if not snap:
        print("ERRO: snapshot ausente")
        return 1
    html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    faltam = verificar(html, snap)
    if faltam:
        print(f"ERRO: site diferente do snapshot {snap['gerado_em_brt']}: faltam {faltam}")
        return 1
    print(f"OK: site = snapshot {snap['gerado_em_brt']} · {' / '.join(valores_esperados(snap)[:2])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
