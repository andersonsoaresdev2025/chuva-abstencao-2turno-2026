"""
Carregamento dos dados do projeto Chuva × Abstenção Eleitoral – 2º Turno 2026.

Todos os caminhos são relativos à raiz do repositório (pasta que contém `data/`),
para funcionar localmente, no Streamlit Community Cloud, no build do site e no MCP.
Nenhum dado é inventado aqui: apenas leitura e normalização leve dos CSVs.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

VERSAO_CODIGO = "2026-10-25-resultado2t"  # conferido pelo dashboard para recarregar módulos após deploy

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA = REPO_ROOT / "data"

# Encerramento das atualizações do dia da eleição. A última execução publicou o snapshot de 17:09 BRT;
# as atualizações automáticas foram encerradas às 17:10 BRT de 25/10/2026 (workflow desativado).
# Snapshots gerados a partir das 17:00 BRT do dia 25 são tratados como a estimativa final, congelada.
ENCERRAMENTO_TXT = "atualizações encerradas às 17:10 BRT de 25/10/2026"
ENCERRAMENTO_TXT_INICIAL = "Atualizações encerradas às 17:10 BRT de 25/10/2026"
INICIO_ESTIMATIVA_FINAL_UTC = datetime(2026, 10, 25, 20, 0, tzinfo=timezone.utc)  # 17:00 BRT
RESULTADO_2T_DIR = DATA / "resultado_2turno"
REPO_BLOB = "https://github.com/andersonsoaresdev2025/chuva-abstencao-2turno-2026/blob/main/data/resultado_2turno"
REPO_TREE = "https://github.com/andersonsoaresdev2025/chuva-abstencao-2turno-2026/tree/main/data/resultado_2turno"


def estimativa_congelada(gerado_utc) -> bool:
    """True se o snapshot é a estimativa final do dia da eleição (mantida sem alteração como registro histórico)."""
    try:
        return gerado_utc is not None and gerado_utc >= INICIO_ESTIMATIVA_FINAL_UTC
    except TypeError:
        return False
IMPACTO_DIR = DATA / "impacto"
CLIMA_DIR = DATA / "clima" / "previsoes_2026-10-25"
CORREL_DIR = DATA / "correlacao"
REDUTOS_DIR = DATA / "redutos_1turno"
SOCIAL_DIR = DATA / "social"
# Atualização automática (scripts/atualizar_*.py executam os papéis dos Bots 2 e 4 a cada 30 min)
ATUAL_CLIMA_DIR = DATA / "clima" / "atualizacoes"
ATUAL_IMPACTO_DIR = DATA / "impacto" / "atualizacoes"
AJUSTES_FILE = DATA / "ajustes" / "ajustes_impacto_noticias.csv"
GEO_FILE = DATA / "geo" / "municipios_coordenadas.csv"
LOGS_DIR = DATA / "logs"

TZ_BRT = ZoneInfo("America/Sao_Paulo")

SOCIAL_COLS = [
    "timestamp_coleta_utc", "timestamp_post", "cidade", "uf", "tipo",
    "nivel_risco_implicito", "confianca", "fonte", "tipo_fonte", "resumo",
    "link", "cidade_risco_previsto", "rede",
]

# Fontes declaradas por arquivo (texto exibido junto de cada resposta/tabela)
FONTES = {
    "risco_bot2": "Bot 2 – Open-Meteo + alertas INMET (classificação a/b/c do projeto); "
                  "arquivo data/clima/previsoes_2026-10-25/risco_chuva_*.csv",
    "impacto_bot4": "Bot 4 – cruzamento Open-Meteo (Bot 0) + coeficientes Bot 1 + redutos Bot 3; "
                    "arquivo data/impacto/impacto_*.csv",
    "previsao_bot0": "Bot 0 – Open-Meteo (previsão horária, maiores cidades); "
                     "arquivo data/clima/previsoes_2026-10-25/previsao_maiores_cidades_com_risco.csv",
    "redutos_bot3": "Bot 3 – TSE 1º turno 2026 (processado pelo Bot 0); arquivo data/redutos_1turno/",
    "correlacao_bot1": "Bot 1 – literatura internacional + análise 1º turno 2026 (Open-Meteo Archive/ERA5 + TSE); "
                       "arquivo data/correlacao/",
    "social": "Monitoramento de redes sociais (X, Instagram via busca web pública, fontes locais); "
              "arquivo data/social/sinais_*.csv",
    "risco_auto": "scripts/atualizar_clima.py (papel do Bot 2, a cada 30 min) – Open-Meteo horário + avisos INMET "
                  "+ ajustes por notícias; arquivo data/clima/atualizacoes/risco_chuva_*_latest.csv",
    "impacto_auto": "scripts/atualizar_impacto.py (papel do Bot 4, a cada 30 min) – mesma regra por classe do Bot 4; "
                    "arquivo data/impacto/atualizacoes/impacto_*_latest.csv",
    "ajustes": "Ajustes por notícias (Grok Bot, revisão a cada 30 min); arquivo data/ajustes/ajustes_impacto_noticias.csv",
}

ORDEM_RISCO = {"torrencial": 0, "moderada": 1, "sem_chuva_relevante": 2}
ROTULO_RISCO = {
    "torrencial": "a) Torrencial / Tempestade / Risco de alagamento",
    "moderada": "b) Moderada",
    "sem_chuva_relevante": "c) Sem chuva relevante",
}


def agora_utc() -> datetime:
    return datetime.now(timezone.utc)


def fmt_utc_brt(dt: datetime | None = None) -> str:
    dt = dt or agora_utc()
    return (f"{dt.astimezone(timezone.utc):%Y-%m-%d %H:%M} UTC / "
            f"{dt.astimezone(TZ_BRT):%Y-%m-%d %H:%M} BRT")


def norm(txt) -> str:
    """Normaliza nomes para comparação (sem acento, maiúsculo, sem espaços extras)."""
    if txt is None or (isinstance(txt, float) and pd.isna(txt)):
        return ""
    s = unicodedata.normalize("NFKD", str(txt)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().upper()


def nivel_curto(val) -> str:
    """Converte qualquer rótulo de risco (a/b/c, 'a/b', 'torrencial', 'b) Moderada'...) em chave curta."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "sem_chuva_relevante"
    v = norm(val).lower()
    if v.startswith("baix") or v.startswith("sem") or v.startswith("c"):
        return "sem_chuva_relevante"
    # aceita também a escala alto/médio/baixo usada pelo monitoramento social
    if v.startswith("medi") or v.startswith("moderad") or v.startswith("b"):
        return "moderada"
    if "torrencial" in v or v.startswith("alt") or v.startswith("a"):
        return "torrencial"
    return "sem_chuva_relevante"


def read_csv(path: Path) -> pd.DataFrame:
    if path.exists() and path.stat().st_size > 0:
        try:
            return pd.read_csv(path)
        except Exception:  # arquivo corrompido/vazio não deve derrubar o app
            return pd.DataFrame()
    return pd.DataFrame()


def read_md(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "_Arquivo não encontrado._"


def latest_ou_original(latest: Path, original: Path) -> tuple[pd.DataFrame, str]:
    """Lê o *_latest.csv da atualização automática; se ausente/vazio, cai no arquivo original."""
    df = read_csv(latest)
    if not df.empty:
        return df, "atualizado"
    return read_csv(original), "original"


def carregar_ajustes(somente_ativos: bool = True) -> pd.DataFrame:
    from common import regras as R
    df = read_csv(AJUSTES_FILE)
    if df.empty:
        return pd.DataFrame(columns=R.AJUSTES_COLS + ["letra_ajuste", "mm_ajuste"])
    return R.ajustes_ativos(df) if somente_ativos else df


def carregar_tudo() -> dict:
    origem = {}
    d = {}
    pares = {
        "impacto_mun": ("impacto_municipios_latest.csv", "impacto_municipios.csv", ATUAL_IMPACTO_DIR, IMPACTO_DIR),
        "impacto_uf": ("impacto_estados_latest.csv", "impacto_estados.csv", ATUAL_IMPACTO_DIR, IMPACTO_DIR),
        "impacto_reg": ("impacto_regioes_latest.csv", "impacto_regioes.csv", ATUAL_IMPACTO_DIR, IMPACTO_DIR),
        "risco_mun": ("risco_chuva_municipios_latest.csv", "risco_chuva_municipios.csv", ATUAL_CLIMA_DIR, CLIMA_DIR),
        "risco_uf": ("risco_chuva_estados_latest.csv", "risco_chuva_estados.csv", ATUAL_CLIMA_DIR, CLIMA_DIR),
        "risco_reg": ("risco_chuva_regioes_latest.csv", "risco_chuva_regioes.csv", ATUAL_CLIMA_DIR, CLIMA_DIR),
    }
    for k, (lat, orig, dl, do) in pares.items():
        d[k], origem[k] = latest_ou_original(dl / lat, do / orig)
    d.update({
        "previsao": read_csv(CLIMA_DIR / "previsao_maiores_cidades_com_risco.csv"),
        "redutos_mun": read_csv(REDUTOS_DIR / "redutos_municipios.csv"),
        "redutos_uf": read_csv(REDUTOS_DIR / "redutos_estados.csv"),
        "redutos_reg": read_csv(REDUTOS_DIR / "redutos_regioes.csv"),
        "faixas_chuva": read_csv(CORREL_DIR / "resumo_por_faixa_chuva.csv"),
        # camadas da manhã (originais dos Bots 2 e 4), para comparação
        "risco_mun_manha": read_csv(CLIMA_DIR / "risco_chuva_municipios.csv"),
        "impacto_mun_manha": read_csv(IMPACTO_DIR / "impacto_municipios.csv"),
        "ajustes": carregar_ajustes(),
    })
    d["_origem"] = origem
    # UF "ZZ" = eleitores no exterior (sem região)
    if not d["impacto_uf"].empty and "regiao" in d["impacto_uf"].columns:
        d["impacto_uf"]["regiao"] = d["impacto_uf"]["regiao"].fillna("Exterior (ZZ)")
    return d


def status_atualizacao() -> dict:
    """Status gravado pelos scripts de atualização (fontes ok/falha, horários). {} se não houver."""
    import json
    out = {}
    for nome, p in (("clima", ATUAL_CLIMA_DIR / "status_latest.json"),
                    ("impacto", ATUAL_IMPACTO_DIR / "impacto_agora_latest.json")):
        try:
            out[nome] = json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            out[nome] = {}
    return out


def _primeiro(df: pd.DataFrame, col: str) -> str | None:
    if df.empty or col not in df.columns:
        return None
    vals = df[col].dropna().astype(str)
    return vals.max() if not vals.empty else None


def timestamps_dados(d: dict | None = None) -> dict[str, str]:
    """Timestamps declarados DENTRO dos arquivos (não mtime), por camada."""
    d = d or carregar_tudo()
    og = d.get("_origem", {})
    rot_imp = "Impacto (auto, papel Bot 4)" if og.get("impacto_mun") == "atualizado" else "Impacto (Bot 4)"
    rot_ris = ("Risco de chuva a/b/c (auto, papel Bot 2)" if og.get("risco_mun") == "atualizado"
               else "Risco de chuva a/b/c (Bot 2)")
    out = {
        rot_imp: _primeiro(d["impacto_mun"], "timestamp_atualizacao"),
        rot_ris: _primeiro(d["risco_mun"], "ultima_atualizacao"),
        "Previsão Open-Meteo maiores cidades (Bot 0)": _primeiro(d["previsao"], "timestamp_coleta"),
    }
    if og.get("risco_mun") == "atualizado":
        out["Classificação da manhã (Bot 2 original)"] = _primeiro(d.get("risco_mun_manha", pd.DataFrame()),
                                                                    "ultima_atualizacao")
    corr = read_csv(CORREL_DIR / "analise_1turno_2026.csv")
    out["Correlação 1º turno (Bot 1)"] = _primeiro(corr, "timestamp")
    out["Redutos 1º turno (Bot 3)"] = "2026-10-25 ~06:30 BRT (resumo_executivo_redutos.md)"
    aj = read_csv(AJUSTES_FILE)
    out["Ajustes por notícias"] = (_primeiro(aj, "timestamp_brt") if not aj.empty else "nenhum ajuste registrado")
    soc = carregar_social()
    if not soc.empty:
        out["Sinais sociais (último coletado)"] = _primeiro(soc, "timestamp_coleta_utc")
    return {k: (v if v else "—") for k, v in out.items()}


def ts_camada(d: dict, chave: str) -> str:
    """Timestamp BRT declarado da camada 'impacto' ou 'risco'."""
    col = {"impacto": ("impacto_mun", "timestamp_atualizacao"), "risco": ("risco_mun", "ultima_atualizacao")}[chave]
    return _primeiro(d[col[0]], col[1]) or "—"


def ultimo_timestamp_principal(d: dict | None = None) -> str:
    d = d or carregar_tudo()
    return ts_camada(d, "impacto")


# -----------------------------------------------------------------------------
# Sinais sociais (pasta opcional data/social/)
# -----------------------------------------------------------------------------
def arquivos_social() -> tuple[list[Path], list[Path]]:
    if not SOCIAL_DIR.is_dir():
        return [], []
    csvs = sorted(SOCIAL_DIR.glob("sinais_*.csv"), key=lambda p: (p.stat().st_mtime, p.name))
    mds = sorted(SOCIAL_DIR.glob("resumo_*.md"), key=lambda p: (p.stat().st_mtime, p.name))
    return csvs, mds


def rede_do_link(link) -> str:
    """Infere a rede para arquivos antigos sem a coluna `rede`: x, instagram ou web."""
    u = "" if link is None or (isinstance(link, float) and pd.isna(link)) else str(link).lower()
    if "x.com/" in u or "twitter.com/" in u:
        return "x"
    if "instagram.com/" in u:
        return "instagram"
    return "web"


def carregar_social() -> pd.DataFrame:
    """Concatena todos os sinais_*.csv (deduplicados por link+cidade), mais recentes primeiro.
    Retorna DataFrame vazio (com colunas do schema) se a pasta não existir ou estiver vazia."""
    csvs, _ = arquivos_social()
    frames = []
    for p in csvs:
        df = read_csv(p)
        if df.empty:
            continue
        for c in SOCIAL_COLS:
            if c not in df.columns:
                df[c] = pd.NA
        df = df[SOCIAL_COLS].copy()
        df["rede"] = df["rede"].where(df["rede"].notna() & (df["rede"].astype(str).str.strip() != ""),
                                      df["link"].map(rede_do_link))
        df["arquivo_origem"] = p.name
        frames.append(df)
    if not frames:
        return pd.DataFrame(columns=SOCIAL_COLS + ["arquivo_origem"])
    soc = pd.concat(frames, ignore_index=True)
    soc["_ts"] = pd.to_datetime(soc["timestamp_coleta_utc"], errors="coerce", utc=True)
    soc["_tp"] = pd.to_datetime(soc["timestamp_post"], errors="coerce", utc=True, format="ISO8601")
    soc = soc.sort_values(["_ts", "_tp"], ascending=False, na_position="last")
    has_link = soc["link"].notna() & (soc["link"].astype(str).str.strip() != "")
    soc = pd.concat([soc[has_link].drop_duplicates(["link", "cidade"], keep="first"), soc[~has_link]])
    soc = soc.sort_values(["_ts", "_tp"], ascending=False, na_position="last").drop(columns=["_ts", "_tp"])
    return soc.reset_index(drop=True)


def ultimo_resumo_social() -> tuple[str | None, str | None]:
    _, mds = arquivos_social()
    if not mds:
        return None, None
    p = mds[-1]
    return p.name, p.read_text(encoding="utf-8")


DISCLAIMER_SOCIAL = (
    "Sinais de redes sociais e portais locais são **relatos não oficiais**, coletados "
    "automaticamente e filtrados por relevância e tipo de fonte (preferência para INMET, "
    "Defesa Civil, meteorologistas, veículos de imprensa e relatos locais consistentes). "
    "Eles **não alteram automaticamente** as estimativas de impacto (só entram por meio da camada revisada "
    "'ajuste por notícias', com fontes e confiança declaradas) e podem conter erros, "
    "atrasos ou desinformação. Sempre confira o link original e os canais oficiais "
    "(TSE, INMET, Defesa Civil)."
)

LIMITACOES = [
    "Atualização automática (a cada 30 min) executa por script os papéis dos Bots 2 e 4 com regras fixas; "
    "a classificação a/b/c usa a chuva da janela 08–17h (o Bot 4 da manhã usou o total do dia), então parte das "
    "mudanças vs manhã decorre também do critério. Agregados estaduais extrapolam o nível predominante dos "
    "municípios cobertos para o restante do eleitorado da UF.",
    "Ajustes por notícias são julgamentos baseados em reportagens/relatos (confiança alta/média/baixa declarada); "
    "podem superestimar o efeito (notícia de alagamento pontual) e só elevam o nível (nunca reduzem a previsão). "
    "A intensidade usada é no mínimo o piso da classe (a = 20 mm, b = 5 mm).",
    "Instagram: apenas resultados públicos de buscadores (sem login); a cobertura é pequena, os buscadores podem "
    "bloquear consultas automáticas e os itens têm confiança baixa. X: coleta automática só com credencial de API.",
    "Cobertura climática incompleta: previsão horária detalhada (Open-Meteo) só para os 15 maiores "
    "colégios; a classificação a/b/c do Bot 2 cobre 29 municípios; interior e municípios menores "
    "têm classificação agregada ou extrapolada.",
    "Coeficientes com incerteza: a análise do 1º turno é cross-sectional (30 maiores colégios); parte "
    "da associação chuva × abstenção é explicada por diferenças regionais estruturais. O efeito "
    "após controles é positivo, porém impreciso.",
    "Impacto diferencial simplificado: proporcional à base de votos do 1º turno; não modela renda, "
    "transporte público, idade ou motivação partidária.",
    "O comportamento no 2º turno pode diferir do 1º (mobilização, polarização, transferência de votos).",
    "Chuva ≠ alagamento: eventos extremos podem ter efeitos discretos (seções fechadas, transporte "
    "interrompido) não capturados por uma relação linear média.",
    "No Brasil o voto é obrigatório; a literatura internacional (voto facultativo) pode superestimar o efeito.",
    "As camadas foram geradas em horários diferentes (Bot 2 às 06:35 BRT; Bot 4 às 09:24 BRT com "
    "previsão Open-Meteo coletada às ~09:01). Há divergências de classificação entre elas para alguns "
    "locais (ex.: Curitiba, MS, MG, região Sudeste). Ambas são exibidas com seus timestamps.",
    "Impacto estimado agora: com a atualização automática cobre ~300 maiores colégios (~54% do eleitorado; "
    "sem o arquivo horário, só os 15 maiores, ~20%); o resto do país conta como zero. A chuva das horas decorridas vem do modelo horário Open-Meteo (não de pluviômetros) "
    "e a faixa lo–hi reflete só a incerteza do coeficiente do Bot 1.",
    "Correlação não é causalidade. Todos os efeitos são estimativas com faixa de incerteza, "
    "não previsões eleitorais.",
]
