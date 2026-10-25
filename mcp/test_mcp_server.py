"""Teste ponta a ponta: sobe o servidor MCP via stdio e chama cada ferramenta.
Uso: python mcp/test_mcp_server.py   (ou pytest mcp/test_mcp_server.py)"""
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = Path(__file__).resolve().parent / "chuva_mcp_server.py"
ESPERADAS = {"risco_chuva", "impacto_abstencao", "ranking_risco", "sinais_sociais_recentes", "metodologia_e_limitacoes", "impacto_agora"}


def _json(res):
    assert not res.isError, res.content
    return json.loads(res.content[0].text)


async def _rodar():
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)])
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            nomes = {t.name for t in (await s.list_tools()).tools}
            assert ESPERADAS <= nomes, nomes

            x = _json(await s.call_tool("risco_chuva", {"municipio": "sao paulo"}))
            assert x["bot2_classificacao"][0]["nivel_risco"] == "a"
            assert x["bot4_previsao_horaria"][0]["nivel_risco"] == "torrencial"
            assert x["fonte"] and x["atualizado_em"]
            x = _json(await s.call_tool("risco_chuva", {"uf": "RJ"}))
            assert x["bot2_classificacao_uf"]
            x = _json(await s.call_tool("risco_chuva", {"regiao": "Nordeste"}))
            assert x["bot2_classificacao_regiao"][0]["nivel_risco_predominante"] == "c"
            x = _json(await s.call_tool("risco_chuva", {"municipio": "Cidade Inexistente"}))
            assert "observacao" in x
            x = _json(await s.call_tool("risco_chuva", {}))
            assert "erro" in x

            x = _json(await s.call_tool("impacto_abstencao", {"municipio": "Rio de Janeiro"}))
            r0 = x["resultados"][0]
            assert (r0["efeito_abstencao_pp_lo"], r0["efeito_abstencao_pp_mid"], r0["efeito_abstencao_pp_hi"]) == (1.2, 2.0, 3.0)
            x = _json(await s.call_tool("impacto_abstencao", {"uf": "sp"}))
            assert x["resultados"][0]["uf"] == "SP"
            x = _json(await s.call_tool("impacto_abstencao", {"regiao": "Sudeste"}))
            assert x["resultados"][0]["regiao"] == "Sudeste"

            x = _json(await s.call_tool("ranking_risco", {"n": 5}))
            assert len(x["resultados"]) == 5 and x["resultados"][0]["nivel_risco"] == "a"

            x = _json(await s.call_tool("sinais_sociais_recentes", {"cidade": "São Paulo", "n": 3}))
            assert "disclaimer" in x and isinstance(x["resultados"], list)

            x = _json(await s.call_tool("impacto_agora", {}))
            for k in ("flavio_pp", "lula_pp", "margem_lula_menos_flavio_pp"):
                assert x[k]["min"] <= x[k]["mid"] <= x[k]["max"] and abs(x[k]["mid"]) < 0.5
            assert x["calculado_em"] and x["fonte_precipitacao"] and len(x["municipios"]) >= 15

            x = _json(await s.call_tool("metodologia_e_limitacoes", {}))
            assert len(x["limitacoes"]) >= 5
            return sorted(nomes)


def test_mcp_tools():
    asyncio.run(_rodar())


if __name__ == "__main__":
    print("Ferramentas OK:", asyncio.run(_rodar()))
