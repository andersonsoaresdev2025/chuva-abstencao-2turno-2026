"""Baixa de novo os arquivos oficiais do TSE do 2º turno (eleição 6258) para data/resultado_2turno/tse_2t/.

Os arquivos já estão versionados no repositório; use este script só para conferir ou reconstruir.
- Abstenção por UF/município: https://resultados.tse.jus.br/oficial/ele2026/6258/dados/{uf}/{uf}-e006258-ab.json
  (o arquivo "br" traz as linhas por UF e o total nacional; salvo como ab_2t.json)
- Resultado municipal (Presidente, cargo 1): .../dados/{uf}/{uf}{cd_tse:05d}-c0001-e006258-u.json
A lista de municípios vem de comparacao_municipios_2turno.csv (colunas uf e codigo_tse).
"""
import csv
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "resultado_2turno"
BASE = "https://resultados.tse.jus.br/oficial/ele2026/6258/dados"
UFS = ("ac al am ap ba ce df es go ma mg ms mt pa pb pe pi pr rj rn ro rr rs sc se sp to zz").split()


def baixar(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "chuva-abstencao-2turno-2026"})
    with urllib.request.urlopen(req, timeout=60) as r:
        dest.write_bytes(r.read())
    time.sleep(0.2)


def main() -> int:
    tse = OUT / "tse_2t"
    baixar(f"{BASE}/br/br-e006258-ab.json", tse / "ab_2t.json")
    for uf in UFS:
        baixar(f"{BASE}/{uf}/{uf}-e006258-ab.json", tse / f"ab_{uf}.json")
    with open(OUT / "comparacao_municipios_2turno.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            uf, cd = row["uf"].lower(), int(row["codigo_tse"])
            nome = f"{uf}{cd:05d}-c0001-e006258-u.json"
            baixar(f"{BASE}/{uf}/{nome}", tse / "municipios" / nome)
    print("ok:", tse)
    return 0


if __name__ == "__main__":
    sys.exit(main())
