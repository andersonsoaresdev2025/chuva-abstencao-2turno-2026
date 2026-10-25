#!/usr/bin/env python3
"""
MCP "chuva-abstencao-2026" – risco de chuva × impacto estimado na abstenção (2º turno, 25/10/2026).

Servidor MCP mínimo (SDK oficial `mcp`, FastMCP) que lê os CSVs do repositório.
Transporte: stdio.   Execução:  python mcp/chuva_mcp_server.py
Cada resposta inclui `fonte` e `atualizado_em` (timestamps declarados nos arquivos) e
`consultado_em`. Nenhum dado é gerado: apenas leitura/filtragem dos arquivos de data/.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))  # append (não insert) para não sombrear o pacote `mcp`

import pandas as pd  # noqa: E402
from mcp.server.fastmcp import FastMCP  # noqa: E402

from common import dados as D  # noqa: E402

mcp = FastMCP("chuva-abstencao-2026")

_REGIOES = {"NORTE", "NORDESTE", "CENTRO-OESTE", "SUDESTE", "SUL"}


def _limpo(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    if hasattr(v, "item"):  # numpy scalar
        v = v.item()
        if isinstance(v, float) and math.isnan(v):
            return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    return v


def _registros(df: pd.DataFrame, cols: list[str] | None = None) -> list[dict]:
    if df.empty:
        return []
    if cols:
        df = df[[c for c in cols if c in df.columns]]
    return [{k: _limpo(v) for k, v in r.items()} for r in df.to_dict(orient="records")]


def _meta(*chaves_fonte: str) -> dict:
    ts = D.timestamps_dados()
    return {
        "fonte": [D.FONTES[k] for k in chaves_fonte],
        "atualizado_em": ts,
        "consultado_em": D.fmt_utc_brt(),
        "aviso": "Estimativas com incerteza; não é previsão eleitoral oficial. Fontes oficiais: TSE, INMET, Defesa Civil.",
    }


def _filtro(df: pd.DataFrame, col: str, valor: str | None) -> pd.DataFrame:
    if df.empty or not valor or col not in df.columns:
        return df.iloc[0:0] if valor else df
    alvo = D.norm(valor)
    return df[df[col].map(D.norm) == alvo]


def _escopo(municipio: str | None, uf: str | None, regiao: str | None) -> str | None:
    if not any([municipio, uf, regiao]):
        return "Informe pelo menos um de: municipio, uf (sigla, ex. SP) ou regiao (Norte, Nordeste, Centro-Oeste, Sudeste, Sul)."
    if regiao and D.norm(regiao) not in _REGIOES:
        return f"Região inválida: {regiao}. Use Norte, Nordeste, Centro-Oeste, Sudeste ou Sul."
    return None


@mcp.tool()
def risco_chuva(municipio: str | None = None, uf: str | None = None, regiao: str | None = None) -> dict:
    """Risco de chuva (classificação a/b/c do projeto) no horário de votação 08h–17h de 25/10/2026.

    Consulte por municipio (ex. "São Paulo"), uf (sigla, ex. "RJ") ou regiao (ex. "Sul").
    Retorna as duas camadas disponíveis, cada uma com seu timestamp: Bot 2 (Open-Meteo + alertas INMET)
    e Bot 0/Bot 4 (previsão horária Open-Meteo dos maiores colégios). Elas podem divergir."""
    erro = _escopo(municipio, uf, regiao)
    if erro:
        return {"erro": erro}
    d = D.carregar_tudo()
    out: dict[str, Any] = {"consulta": {"municipio": municipio, "uf": uf, "regiao": regiao}}
    legenda = {"a": D.ROTULO_RISCO["torrencial"], "b": D.ROTULO_RISCO["moderada"], "c": D.ROTULO_RISCO["sem_chuva_relevante"]}
    if municipio:
        b2 = _filtro(d["risco_mun"], "municipio", municipio)
        if uf:
            b2 = _filtro(b2, "uf", uf)
        b4 = _filtro(d["impacto_mun"], "municipio", municipio)
        if uf:
            b4 = _filtro(b4, "uf", uf)
        out["bot2_classificacao"] = _registros(b2)
        out["bot4_previsao_horaria"] = _registros(b4, [
            "municipio", "uf", "precip_sum_mm", "precip_janela_votacao_08_17_mm", "precip_manha_08_12_mm",
            "precip_tarde_12_17_mm", "precip_prob_max_pct", "classe_risco_projeto", "nivel_risco",
            "fonte_clima", "timestamp_atualizacao"])
    elif uf:
        out["bot2_classificacao_uf"] = _registros(_filtro(d["risco_uf"], "uf", uf))
        out["bot2_municipios_da_uf"] = _registros(_filtro(d["risco_mun"], "uf", uf))
        out["bot4_agregado_uf"] = _registros(_filtro(d["impacto_uf"], "uf", uf),
                                             ["uf", "regiao", "nivel_risco", "vulnerabilidade", "observacao", "timestamp_atualizacao"])
    else:
        out["bot2_classificacao_regiao"] = _registros(_filtro(d["risco_reg"], "regiao", regiao))
        out["bot2_ufs_da_regiao"] = _registros(_filtro(d["risco_uf"], "regiao", regiao))
        out["bot4_agregado_regiao"] = _registros(_filtro(d["impacto_reg"], "regiao", regiao),
                                                 ["regiao", "nivel_risco", "vulnerabilidade", "timestamp_atualizacao"])
    encontrou = any(v for k, v in out.items() if k != "consulta")
    if not encontrou:
        out["observacao"] = ("Local não encontrado nos arquivos de risco (cobertura: 29 municípios no Bot 2, "
                             "15 no Bot 4, 15 UFs no Bot 2, 27 UFs + exterior no Bot 4). Sem dado → não estimamos.")
    out["legenda_niveis"] = legenda
    out.update(_meta("risco_bot2", "previsao_bot0", "impacto_bot4"))
    return out


@mcp.tool()
def impacto_abstencao(municipio: str | None = None, uf: str | None = None, regiao: str | None = None) -> dict:
    """Impacto estimado da chuva na abstenção (pontos percentuais: mid, lo, hi) e candidato com maior
    base local no 1º turno (mais exposto em votos absolutos). Consulte por municipio, uf ou regiao."""
    erro = _escopo(municipio, uf, regiao)
    if erro:
        return {"erro": erro}
    d = D.carregar_tudo()
    cols = ["municipio", "uf", "regiao", "aptos", "pct_abstencao_1t", "pct_flavio_1t", "pct_lula_1t", "vencedor_1t",
            "peso_eleitoral_pct", "nivel_risco", "efeito_abstencao_pp_mid", "efeito_abstencao_pp_lo",
            "efeito_abstencao_pp_hi", "impacto_relativo_flavio", "impacto_relativo_lula", "mais_prejudicado",
            "vulnerabilidade", "fonte_coeficiente", "observacao", "timestamp_atualizacao"]
    if municipio:
        df = _filtro(d["impacto_mun"], "municipio", municipio)
        if uf:
            df = _filtro(df, "uf", uf)
    elif uf:
        df = _filtro(d["impacto_uf"], "uf", uf)
    else:
        df = _filtro(d["impacto_reg"], "regiao", regiao)
    regs = _registros(df, cols)
    for r in regs:  # aritmética simples e declarada: aptos × pp / 100
        if r.get("aptos") is not None and r.get("efeito_abstencao_pp_lo") is not None:
            r["abstencoes_extras_ordem_grandeza"] = {
                k: round(r["aptos"] * r[f"efeito_abstencao_pp_{k}"] / 100)
                for k in ("lo", "mid", "hi")}
    out = {"consulta": {"municipio": municipio, "uf": uf, "regiao": regiao}, "resultados": regs,
           "regra_pratica_bot1": {"moderada_pp": [0.5, 1.2], "torrencial_pp": [1.2, 3.0], "sem_chuva_relevante_pp": [0.0, 0.4]}}
    if not regs:
        out["observacao"] = ("Sem estimativa de impacto para este local nos arquivos do Bot 4 "
                             "(municípios: 15 maiores colégios com previsão horária). Não estimamos sem dados.")
    out.update(_meta("impacto_bot4", "correlacao_bot1", "redutos_bot3"))
    return out


@mcp.tool()
def ranking_risco(n: int = 10) -> dict:
    """Ranking dos municípios com maior risco de chuva no horário de votação (nível a > b > c, depois
    precipitação estimada), da classificação do Bot 2, com o efeito estimado do Bot 4 quando disponível."""
    n = max(1, min(int(n), 100))
    d = D.carregar_tudo()
    rm = d["risco_mun"].copy()
    if rm.empty:
        return {"resultados": [], "observacao": "Arquivo de risco não disponível."} | _meta("risco_bot2")
    rm["_o"] = rm["nivel_risco"].map(D.nivel_curto).map(D.ORDEM_RISCO)
    rm = rm.sort_values(["_o", "precipitacao_mm_estimada"], ascending=[True, False]).head(n)
    im = d["impacto_mun"].copy()
    im["_k"] = im["municipio"].map(D.norm) + "|" + im["uf"].map(D.norm)
    imp = im.set_index("_k")
    res = []
    for i, r in enumerate(_registros(rm.drop(columns="_o")), 1):
        k = D.norm(r["municipio"]) + "|" + D.norm(r["uf"])
        item = {"posicao": i, **r}
        if k in imp.index:
            x = imp.loc[k]
            item["bot4"] = {c: _limpo(x[c]) for c in ["nivel_risco", "efeito_abstencao_pp_mid", "efeito_abstencao_pp_lo",
                                                      "efeito_abstencao_pp_hi", "vulnerabilidade", "aptos", "timestamp_atualizacao"]}
        res.append(item)
    return {"n": n, "resultados": res, **_meta("risco_bot2", "impacto_bot4")}


@mcp.tool()
def sinais_sociais_recentes(cidade: str | None = None, n: int = 10) -> dict:
    """Sinais recentes de redes sociais (X) e fontes locais sobre chuva/alagamento/mobilidade no dia da
    eleição, lidos de data/social/sinais_*.csv (se existir). Relatos NÃO oficiais – confira o link."""
    n = max(1, min(int(n), 200))
    soc = D.carregar_social()
    if cidade and not soc.empty:
        soc = soc[soc["cidade"].map(D.norm) == D.norm(cidade)]
    out = {"consulta": {"cidade": cidade, "n": n}, "total_encontrado": int(len(soc)),
           "resultados": _registros(soc.head(n)), "disclaimer": D.DISCLAIMER_SOCIAL.replace("**", "")}
    if soc.empty:
        out["observacao"] = ("Nenhum sinal social disponível" + (f" para {cidade}" if cidade else "") +
                             " (pasta data/social vazia, ausente ou sem registros correspondentes).")
    out.update(_meta("social"))
    return out


_CHAVES_CENARIO = ("flavio_pp", "lula_pp", "margem_lula_menos_flavio_pp", "votos_perdidos_flavio", "votos_perdidos_lula",
                   "abstencoes_extras", "abstencao_nacional_pp")


def _cenario(r: dict) -> dict:
    """Um cenário (dict de calcular_com_api ou do snapshot JSON) em formato limpo, sem a lista de municípios."""
    out = {k: _limpo(v) if not isinstance(v, dict) else {kk: _limpo(vv) for kk, vv in v.items()}
           for k, v in r.items() if k not in ("municipios", "municipios_lista", "municipios_top", "fontes", "coeficiente")}
    out["coeficiente_pp_por_mm"] = r.get("coeficiente")
    out["fonte"] = r.get("fontes")
    return out


def _impacto_ao_vivo(IA, motivo: str) -> dict:
    r = IA.calcular_com_api(ajustes=None)  # só previsão
    rn = IA.calcular_com_api(ajustes="auto")  # previsão + ajustes por notícias (igual se não houver ajuste)
    out = _cenario(r)
    out["municipios"] = _registros(r["municipios"])
    out["previsao_mais_noticias"] = _cenario(rn)
    out["previsao_mais_noticias"]["n_ajustes_noticias"] = int(rn.get("n_ajustes_noticias", 0))
    out.update({"tipo_resultado": "recalculo_ao_vivo", "observacao": motivo,
                "snapshot_brt": None, "proxima_atualizacao_brt": None})
    return out


@mcp.tool()
def impacto_agora(ao_vivo: bool = False) -> dict:
    """Impacto estimado AGORA da chuva acumulada desde 08h (BRT) sobre cada candidato, em p.p. dos votos
    válidos (Flávio+Lula), com faixa (coeficiente Bot 1 lo/mid/hi), votos perdidos, efeito na margem
    (Lula − Flávio) e cobertura do eleitorado – nos cenários "só previsão" (campos de topo) e
    "previsao_mais_noticias" (com ajustes por notícias).
    Padrão (ao_vivo=False): devolve o SNAPSHOT PUBLICADO data/impacto/atualizacoes/impacto_agora_latest.json –
    exatamente os mesmos números do site e do dashboard – com snapshot_brt e proxima_atualizacao_brt (~30 min).
    ao_vivo=True: recálculo de diagnóstico neste instante (mais horas decorridas → difere do snapshot; não é o
    número oficial). Não é contagem de votos nem boca de urna."""
    from common import impacto_agora as IA
    if ao_vivo:
        out = _impacto_ao_vivo(IA, "Recálculo ao vivo (diagnóstico): difere do snapshot publicado exibido no site e no "
                                   "dashboard; não é o número oficial.")
    else:
        snap = IA.carregar_snapshot()
        if not snap:
            out = _impacto_ao_vivo(IA, "Snapshot publicado ausente: valores recalculados agora (diagnóstico).")
        else:
            d = IA.duplo_do_snapshot(snap)
            out = _cenario(d["previsao"])
            out["municipios"] = _registros(d["previsao"]["municipios"])
            out["previsao_mais_noticias"] = _cenario(d["previsao_mais_noticias"])
            out["previsao_mais_noticias"]["municipios"] = _registros(d["previsao_mais_noticias"]["municipios"])
            out.update({
                "tipo_resultado": "snapshot_publicado",
                "snapshot_brt": f"{snap['snapshot_hhmm_brt']} BRT", "gerado_em_brt": snap.get("gerado_em_brt"),
                "gerado_em_utc": snap.get("gerado_em_utc"),
                "proxima_atualizacao_brt": f"~{snap['proxima_atualizacao_hhmm_brt']} BRT",
                "fonte_snapshot": f"data/impacto/atualizacoes/{IA.SNAPSHOT_NOME} ({snap.get('_origem_snapshot')})",
                "n_ajustes_ativos": int(snap.get("n_ajustes_ativos") or 0),
                "observacao": "Mesmos números do site e do dashboard (snapshot publicado pela atualização automática).",
            })
    out["metodo"] = IA.METODO_TXT
    out["aviso"] = IA.DISCLAIMER.replace("**", "")
    return out


@mcp.tool()
def metodologia_e_limitacoes() -> dict:
    """Metodologia do projeto (classificação de risco, coeficientes, impacto) e limitações declaradas."""
    return {
        "classificacao_risco": D.ROTULO_RISCO | {"criterios": {
            "a": ">= 20–30 mm na janela 08–17h ou alertas de tempestade/alagamento",
            "b": "5–20/30 mm", "c": "< 5 mm"}},
        "coeficientes_bot1": {
            "literatura": "+0,4 a +1,0 pp de abstenção por cm de chuva (meta-análises internacionais)",
            "primeiro_turno_2026": "diferença bruta ≈ +2,2 pp (faixa moderada vs sem chuva, 30 maiores colégios); efeito reduzido e impreciso após controles regionais",
            "regra_pratica": {"moderada": "+0,5 a +1,2 pp", "torrencial": "+1,2 a +3,0 pp"},
        },
        "impacto_diferencial_bot4": "Proporcional à base de votos do 1º turno (quem tem maior base local tende a perder mais votos absolutos).",
        "sinais_sociais": D.DISCLAIMER_SOCIAL.replace("**", ""),
        "limitacoes": D.LIMITACOES,
        **_meta("risco_bot2", "impacto_bot4", "correlacao_bot1", "redutos_bot3"),
    }


if __name__ == "__main__":
    mcp.run()  # stdio
