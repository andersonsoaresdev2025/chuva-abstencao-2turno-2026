#!/usr/bin/env bash
# Reconstrói o site estático, roda testes rápidos, faz commit e push para o GitHub.
# Uso: scripts/update_and_publish.sh ["mensagem de commit"]
# Requer: gh/git autenticados (gh auth login && gh auth setup-git).
set -euo pipefail
cd "$(dirname "$0")/.."

PY="${PYTHON:-.venv/bin/python}"
[ -x "$PY" ] || PY=python3
MSG="${1:-Atualização de dados $(date -u '+%Y-%m-%d %H:%M UTC') / $(TZ=America/Sao_Paulo date '+%H:%M BRT')}"

echo "==> Reconstruindo docs/index.html"
"$PY" scripts/build_site.py

echo "==> Testes rápidos (dashboard + MCP)"
if "$PY" -c "import pytest" 2>/dev/null; then
  "$PY" -m pytest -q tests mcp/test_mcp_server.py
else
  echo "pytest não instalado; pulando testes"
fi

echo "==> Verificando arquivos > 50 MB"
BIG=$(find . -path ./.git -prune -o -path ./.venv -prune -o -type f -size +50M -print)
if [ -n "$BIG" ]; then echo "ERRO: arquivos > 50 MB:"; echo "$BIG"; exit 1; fi

echo "==> Commit"
git add -A
if git diff --cached --quiet; then
  echo "Nada para commitar."
else
  git commit -q -m "$MSG"
  echo "Commit: $(git rev-parse --short HEAD)"
fi

echo "==> Push"
if git remote get-url origin >/dev/null 2>&1; then
  git push -q origin main && echo "Push OK"
else
  echo "Remote 'origin' não configurado (crie com: gh repo create ... --source . --push)"; exit 2
fi
