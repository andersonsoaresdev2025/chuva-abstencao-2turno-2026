"""
Regras compartilhadas da atualização automática (papéis dos Bots 2 e 4 executados por scripts).

- Classificação a/b/c (Documento_Instrucoes_v2.2): a) torrencial/tempestade/risco de alagamento,
  b) moderada, c) sem chuva relevante. Regra numérica usada pelos scripts na janela 08h–17h:
  >= 20 mm -> a; 5–20 mm -> b; < 5 mm -> c. Aviso INMET laranja/vermelho de chuva/tempestade
  válido na janela eleva o nível em 1 (amarelo só é anotado).
- Efeitos por classe (pp de abstenção) = os mesmos valores usados pelo Bot 4 em data/impacto/.
- Camada de ajustes por notícias (data/ajustes/ajustes_impacto_noticias.csv): ajustes "ativo"
  valem como piso -> nível final = max(previsão, ajuste).
Nada aqui inventa dado: são regras determinísticas aplicadas aos dados coletados.
"""
from __future__ import annotations

import math

import pandas as pd

LIMIAR_A_MM = 20.0
LIMIAR_B_MM = 5.0

NIVEL_POR_LETRA = {"a": "torrencial", "b": "moderada", "c": "sem_chuva_relevante"}
LETRA_POR_NIVEL = {v: k for k, v in NIVEL_POR_LETRA.items()}
ORDEM = {"c": 0, "b": 1, "a": 2}
ROTULO_LETRA = {
    "a": "a) Torrencial / Tempestade / Risco de alagamento",
    "b": "b) Moderada",
    "c": "c) Sem chuva relevante",
}

# Efeitos por classe usados pelo Bot 4 (impacto_municipios.csv): (mid, lo, hi) em pp de abstenção
EFEITO_CLASSE = {"a": (2.0, 1.2, 3.0), "b": (0.85, 0.5, 1.2), "c": (0.15, 0.0, 0.4)}
FONTE_COEF = "Bot 1 regra prática (moderada +0,5 a +1,2 pp; torrencial +1,2 a +3,0 pp); valores por classe do Bot 4"

# Piso de precipitação equivalente a um ajuste por notícias sem intensidade informada
# (limite inferior da classe; conservador)
MM_PISO_AJUSTE = {"a": LIMIAR_A_MM, "b": LIMIAR_B_MM, "c": 0.0}

SEVERIDADE_ORDEM = {"": 0, "amarelo": 1, "laranja": 2, "vermelho": 3}
EVENTOS_CHUVA = ("tempestade", "chuva", "acumulado")


def letra(nivel) -> str | None:
    """Normaliza 'a', 'a) ...', 'torrencial', 'a/b' (-> a, conservador) etc. para a/b/c."""
    if nivel is None or (isinstance(nivel, float) and math.isnan(nivel)):
        return None
    s = str(nivel).strip().lower()
    if not s or s == "nan":
        return None
    if s in LETRA_POR_NIVEL:
        return LETRA_POR_NIVEL[s]
    if s[0] in ORDEM:
        return s[0]
    if "torrencial" in s or "tempest" in s:
        return "a"
    if "moder" in s:
        return "b"
    if "sem" in s:
        return "c"
    return None


def classificar_mm(mm: float) -> str:
    if mm is None or (isinstance(mm, float) and math.isnan(mm)):
        mm = 0.0
    if mm >= LIMIAR_A_MM:
        return "a"
    if mm >= LIMIAR_B_MM:
        return "b"
    return "c"


def elevar(l: str) -> str:
    return {"c": "b", "b": "a", "a": "a"}[l]


def maior(*ls) -> str | None:
    ls = [x for x in ls if x in ORDEM]
    return max(ls, key=lambda x: ORDEM[x]) if ls else None


def classificar(mm: float, severidade_alerta: str = "") -> str:
    base = classificar_mm(mm)
    if SEVERIDADE_ORDEM.get(severidade_alerta or "", 0) >= 2:
        base = elevar(base)
    return base


def efeito(l: str) -> tuple[float, float, float]:
    return EFEITO_CLASSE.get(l or "c", EFEITO_CLASSE["c"])


def vulnerabilidade(l: str) -> str:
    return {"a": "Alta", "b": "Média"}.get(l, "Baixa")


def mais_prejudicado(pct_flavio, pct_lula, tol_pp: float = 1.0) -> str:
    """Mesmo critério textual do Bot 4: quem tem a maior base local no 1º turno perde mais votos
    absolutos se a abstenção subir de forma uniforme (diferença < tol_pp -> equilibrado)."""
    try:
        f, l = float(pct_flavio), float(pct_lula)
    except (TypeError, ValueError):
        return "Equilibrado / incerto"
    if math.isnan(f) or math.isnan(l) or abs(f - l) < tol_pp:
        return "Equilibrado / incerto"
    return "Flávio Bolsonaro (maior base local)" if f > l else "Lula (maior base local)"


# ---------------------------------------------------------------------------
# Ajustes por notícias
# ---------------------------------------------------------------------------
AJUSTES_COLS = ["timestamp_brt", "codigo_ibge", "municipio", "uf", "nivel_risco_ajustado",
                "intensidade_estimada_mm", "evidencia", "fontes", "confianca", "status", "autor"]


def ajustes_ativos(df: pd.DataFrame) -> pd.DataFrame:
    """Último registro por codigo_ibge; mantém só os 'ativo' com nível a/b/c válido.
    Um registro 'revogado' posterior anula o ajuste anterior do mesmo município."""
    if df is None or df.empty:
        return pd.DataFrame(columns=AJUSTES_COLS + ["letra_ajuste", "mm_ajuste"])
    df = df.copy()
    for c in AJUSTES_COLS:
        if c not in df.columns:
            df[c] = pd.NA
    df["codigo_ibge"] = pd.to_numeric(df["codigo_ibge"], errors="coerce")
    df = df[df["codigo_ibge"].notna()].copy()
    df["codigo_ibge"] = df["codigo_ibge"].astype(int)
    df["_ts"] = pd.to_datetime(df["timestamp_brt"].astype(str).str.replace(" BRT", "", regex=False),
                               errors="coerce")
    df["_ord"] = range(len(df))
    df = df.sort_values(["_ts", "_ord"], na_position="first").drop_duplicates("codigo_ibge", keep="last")
    df = df[df["status"].astype(str).str.strip().str.lower() == "ativo"].copy()
    df["letra_ajuste"] = df["nivel_risco_ajustado"].map(letra)
    df = df[df["letra_ajuste"].isin(["a", "b", "c"])].copy()
    mm = pd.to_numeric(df["intensidade_estimada_mm"], errors="coerce")
    piso = df["letra_ajuste"].map(MM_PISO_AJUSTE)
    # chuva equivalente: intensidade informada, nunca abaixo do piso da classe ajustada (a = 20 mm, b = 5 mm)
    df["mm_ajuste"] = pd.concat([mm, piso.astype(float)], axis=1).max(axis=1, skipna=True).astype(float)
    return df.drop(columns=["_ts", "_ord"]).reset_index(drop=True)


UF_REGIAO = {
    "AC": "Norte", "AP": "Norte", "AM": "Norte", "PA": "Norte", "RO": "Norte", "RR": "Norte", "TO": "Norte",
    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste", "PB": "Nordeste", "PE": "Nordeste",
    "PI": "Nordeste", "RN": "Nordeste", "SE": "Nordeste",
    "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MT": "Centro-Oeste", "MS": "Centro-Oeste",
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul", "RS": "Sul", "SC": "Sul",
}
UF_NOME = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia", "CE": "Ceará",
    "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão", "MT": "Mato Grosso",
    "MS": "Mato Grosso do Sul", "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba", "PR": "Paraná",
    "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina", "SP": "São Paulo",
    "SE": "Sergipe", "TO": "Tocantins",
}
UF_COD = {12: "AC", 27: "AL", 16: "AP", 13: "AM", 29: "BA", 23: "CE", 53: "DF", 32: "ES", 52: "GO",
          21: "MA", 51: "MT", 50: "MS", 31: "MG", 15: "PA", 25: "PB", 41: "PR", 26: "PE", 22: "PI",
          33: "RJ", 24: "RN", 43: "RS", 11: "RO", 14: "RR", 42: "SC", 35: "SP", 28: "SE", 17: "TO"}
