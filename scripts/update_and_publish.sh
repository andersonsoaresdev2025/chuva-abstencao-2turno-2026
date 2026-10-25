#!/usr/bin/env bash
# Mantido por compatibilidade: a publicação agora é feita pelo orquestrador
# scripts/atualizar_tudo.sh (clima → impacto → social → notícias → site → testes → commit → pull --rebase → push).
# Uso preferido: scripts/atualizar_tudo.sh   (automático: .github/workflows/atualizar.yml a cada 30 min)
set -uo pipefail
cd "$(dirname "$0")/.."
exec bash scripts/atualizar_tudo.sh "$@"
