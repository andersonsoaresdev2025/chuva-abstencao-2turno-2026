# MCP – Chuva × Abstenção (2º turno 2026)

Servidor MCP mínimo (SDK oficial `mcp`, API `FastMCP`, v1.x) que responde perguntas sobre **risco de chuva**
no horário de votação e **impacto estimado na abstenção**, lendo os CSVs deste repositório.
Toda resposta inclui `fonte`, `atualizado_em` (timestamps declarados nos arquivos) e `consultado_em`.

## Ferramentas
| Ferramenta | Parâmetros | O que retorna |
|---|---|---|
| `risco_chuva` | `municipio` \| `uf` \| `regiao` | Classificação a/b/c do Bot 2 (alertas INMET) e previsão horária Open-Meteo (Bot 0/4) |
| `impacto_abstencao` | `municipio` \| `uf` \| `regiao` | Efeito em pp (mid/lo/hi), candidato com maior base local, ordem de grandeza de abstenções extras |
| `ranking_risco` | `n` (padrão 10) | Municípios ordenados por nível (a>b>c) e precipitação estimada, com efeito do Bot 4 quando houver |
| `sinais_sociais_recentes` | `cidade`, `n` | Sinais de `data/social/sinais_*.csv` (se existir), com disclaimer |
| `metodologia_e_limitacoes` | — | Classificação, coeficientes, regra prática, limitações |

Sem dado para um local → a ferramenta diz isso explicitamente (não estima).

## Rodar (stdio)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r mcp/requirements.txt
python mcp/chuva_mcp_server.py          # servidor stdio
python mcp/test_mcp_server.py           # teste: sobe o servidor e chama todas as ferramentas
mcp dev mcp/chuva_mcp_server.py         # (opcional) MCP Inspector
```

## Configurar em um cliente MCP (ex.: Claude Desktop / Cursor)
```json
{
  "mcpServers": {
    "chuva-abstencao-2026": {
      "command": "/caminho/para/.venv/bin/python",
      "args": ["/caminho/para/chuva-abstencao-2turno-2026/mcp/chuva_mcp_server.py"]
    }
  }
}
```

Observação: o SDK `mcp` 2.x renomeou `FastMCP` para `MCPServer`; por isso `requirements.txt` fixa `mcp>=1.10,<2`.
