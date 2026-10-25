"""Leitura dos dados de notícias (data/noticias/) para dashboard, site e MCP.
Tolerante a pasta/arquivo ausente ou vazio: devolve DataFrames vazios com o schema."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
NOTICIAS_DIR = REPO_ROOT / "data" / "noticias"

COLS = ["id", "titulo", "link", "portal", "dominio", "abrangencia", "uf", "cidade", "regiao",
        "tema", "publicado_brt", "publicado_utc", "coletado_utc", "score", "sinalizacao",
        "menciona_eleicao", "origem_coleta", "resumo"]
PORTAIS_COLS = ["nome", "url", "dominio", "abrangencia", "uf", "cidades_cobertas", "tipo", "rss_url",
                "observacoes", "status_http_home", "verificado_em_utc"]

DISCLAIMER = (
    "Manchetes coletadas automaticamente de feeds RSS dos portais listados e do Google Notícias, "
    "filtradas por palavras-chave (chuva/tempo severo + eleição). **Não são dados oficiais**: "
    "a abstenção real só é conhecida na totalização do TSE. Tema, cidade e UF são classificados "
    "automaticamente e podem errar. Itens de fontes fora da lista verificada ou com alegações a "
    "checar aparecem sinalizados (⚠️). Alguns portais têm paywall. Sempre abra o link original e "
    "confira os canais oficiais (TSE, TREs, INMET, Defesa Civil)."
)


def _dir(d: Path | None) -> Path:
    return Path(d) if d is not None else NOTICIAS_DIR


def _ler(p: Path, cols: list[str]) -> pd.DataFrame:
    if not p.is_file():
        return pd.DataFrame(columns=cols)
    try:
        df = pd.read_csv(p, dtype=str, keep_default_na=False)
    except Exception:  # noqa: BLE001 (arquivo vazio/corrompido)
        return pd.DataFrame(columns=cols)
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    return df


def carregar_noticias(d: Path | None = None) -> pd.DataFrame:
    """Consolidado (ou, se não existir, o snapshot mais recente), ordenado por relevância."""
    base = _dir(d)
    df = _ler(base / "noticias_consolidado.csv", COLS)
    if df.empty and base.is_dir():
        snaps = sorted(base.glob("noticias_*UTC.csv"))
        if snaps:
            df = _ler(snaps[-1], COLS)
    if df.empty:
        return pd.DataFrame(columns=COLS + ["alerta"])
    df = df[df["titulo"].str.strip() != ""].copy()
    df["score"] = pd.to_numeric(df["score"], errors="coerce").fillna(0.0)
    df["alerta"] = df["sinalizacao"].fillna("").str.contains("verificada|checar|contradi", regex=True)
    df = df.sort_values(["score", "publicado_utc"], ascending=[False, False])
    return df.drop_duplicates("link").reset_index(drop=True)


def principais(df: pd.DataFrame, n: int = 8) -> pd.DataFrame:
    """Top n para 'Principais notícias agora': só portais da lista verificada e sem alegação a checar;
    prioriza publicados no dia da eleição."""
    if df is None or df.empty:
        return pd.DataFrame(columns=COLS + ["alerta"])
    ok = df[(df["abrangencia"].isin(["nacional", "regional"])) & (~df["alerta"])].copy()
    ok["_hoje"] = ok["publicado_brt"].astype(str).str.startswith("2026-10-25")
    ok = ok.sort_values(["_hoje", "score", "publicado_utc"], ascending=[False, False, False])
    return ok.drop(columns="_hoje").head(n).reset_index(drop=True)


def carregar_portais(d: Path | None = None) -> pd.DataFrame:
    return _ler(_dir(d) / "portais.csv", PORTAIS_COLS)


def ultima_coleta(df: pd.DataFrame) -> str:
    if df is None or df.empty or "coletado_utc" not in df.columns:
        return "—"
    ts = pd.to_datetime(df["coletado_utc"], errors="coerce", utc=True).max()
    if pd.isna(ts):
        return "—"
    return f"{ts:%Y-%m-%d %H:%M} UTC / {ts.tz_convert('America/Sao_Paulo'):%H:%M} BRT"


def resumo_md(d: Path | None = None) -> str | None:
    p = _dir(d) / "resumo_noticias.md"
    return p.read_text(encoding="utf-8") if p.is_file() else None
