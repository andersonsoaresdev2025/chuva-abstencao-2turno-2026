#!/usr/bin/env bash
# Orquestrador da atualização automática (a cada 30 min, via GitHub Actions ou cron local).
# Executa, em ordem, os papéis dos Bots 0–4 por scripts (os bots não são chamados):
#   1. clima    – scripts/atualizar_clima.py    (papel Bot 2/Bot 0: Open-Meteo + avisos INMET → risco a/b/c)
#   2. impacto  – scripts/atualizar_impacto.py  (papel Bot 4/Bot 1: impacto por município/UF/região + impacto agora)
#   3. social   – scripts/coletar_social.py     (X se houver credencial; Instagram via busca web pública)
#   4. noticias – scripts/coletar_noticias.py   (portais + Google News RSS)
#   5. site     – scripts/build_site.py         (docs/index.html → GitHub Pages)
#   6. testes   – pytest (rede mockada)
#   7. git      – commit → pull --rebase → push  (desative com PUBLICAR=0, p.ex. quando o workflow faz o commit)
# Uma etapa com falha NUNCA derruba a execução: é registrada no log e as próximas seguem
# (as camadas com falha mantêm o último dado válido e aparecem como desatualizadas).
# Log por execução: data/logs/atualizacao_<UTC>.log · linha de status em STATUS_PUBLICACAO.md.
set -uo pipefail
cd "$(dirname "$0")/.."

PY="${PYTHON:-.venv/bin/python}"
[ -x "$PY" ] || PY=python3
PUBLICAR="${PUBLICAR:-1}"
TS="$(date -u '+%Y%m%d_%H%MUTC')"
BRT="$(TZ=America/Sao_Paulo date '+%Y-%m-%d %H:%M BRT')"
mkdir -p data/logs
LOG="data/logs/atualizacao_${TS}.log"
RESUMO=()

etapa() {  # etapa <nome> <timeout_s> <comando...>
  local nome="$1" lim="$2"; shift 2
  local ini=$SECONDS rc
  echo "===== [$(date -u '+%H:%M:%SZ')] etapa: $nome — $*" | tee -a "$LOG"
  timeout "$lim" "$@" >>"$LOG" 2>&1
  rc=$?
  local dur=$((SECONDS - ini))
  if [ $rc -eq 0 ]; then
    RESUMO+=("$nome=ok(${dur}s)"); echo "----- $nome: OK (${dur}s)" | tee -a "$LOG"
  else
    RESUMO+=("$nome=FALHA:$rc(${dur}s)"); echo "----- $nome: FALHA rc=$rc (${dur}s) — seguindo" | tee -a "$LOG"
  fi
  return 0
}

echo "Atualização automática $TS ($BRT) — log em $LOG" | tee "$LOG"
etapa clima    240 "$PY" scripts/atualizar_clima.py
etapa impacto  180 "$PY" scripts/atualizar_impacto.py
etapa social   180 "$PY" scripts/coletar_social.py
if [ "${COLETAR_NOTICIAS:-1}" = "1" ]; then
  etapa noticias 300 "$PY" scripts/coletar_noticias.py
fi
etapa site     180 "$PY" scripts/build_site.py
if "$PY" -c "import pytest" 2>/dev/null; then
  etapa testes 600 "$PY" -m pytest -q tests mcp/test_mcp_server.py
else
  RESUMO+=("testes=pulado(sem pytest)")
fi

# Linha de status em STATUS_PUBLICACAO.md (bloco automático, mantém as 12 mais recentes)
LINHA="- ${BRT} (${TS}) · ${RESUMO[*]} · log: ${LOG}"
"$PY" - "$LINHA" <<'PYEOF' >>"$LOG" 2>&1 || echo "AVISO: não consegui atualizar STATUS_PUBLICACAO.md" | tee -a "$LOG"
import sys, pathlib
p = pathlib.Path("STATUS_PUBLICACAO.md")
ini, fim = "<!-- AUTO-STATUS:INICIO -->", "<!-- AUTO-STATUS:FIM -->"
t = p.read_text(encoding="utf-8") if p.exists() else "# Status de publicação\n"
if ini not in t:
    t = t.rstrip() + f"\n\n## Atualizações automáticas (mais recente primeiro)\n\n{ini}\n{fim}\n"
a, resto = t.split(ini, 1)
corpo, b = resto.split(fim, 1)
linhas = [l for l in corpo.strip().splitlines() if l.strip()]
linhas = [sys.argv[1]] + linhas[:11]
p.write_text(a + ini + "\n" + "\n".join(linhas) + "\n" + fim + b, encoding="utf-8")
print("STATUS_PUBLICACAO.md atualizado")
PYEOF

echo "Resumo: ${RESUMO[*]}" | tee -a "$LOG"

if [ "$PUBLICAR" = "1" ]; then
  # A saída do git vai para um arquivo ignorado pelo git (data/logs/git_ultimo.txt): escrever no log versionado
  # depois do `git add` deixaria a árvore suja e o `pull --rebase` falharia.
  GITLOG="data/logs/git_ultimo.txt"
  echo "git: commit → pull --rebase --autostash → push (saída em $GITLOG)" | tee -a "$LOG"
  {
    echo "===== git: commit → pull --rebase → push"
    BIG=$(find data docs -type f -size +50M -print)
    if [ -n "$BIG" ]; then echo "ERRO: arquivos > 50 MB, não publico: $BIG"; exit 0; fi
    git add -A data docs STATUS_PUBLICACAO.md
    if git diff --cached --quiet; then
      echo "Nada para commitar."
    else
      git commit -q -m "Atualização automática ${BRT} (${TS})" && echo "Commit: $(git rev-parse --short HEAD)"
    fi
    for i in 1 2 3; do
      # -X theirs no rebase = em conflito, prevalece o nosso commit (dado mais novo)
      git pull -q --rebase --autostash -X theirs origin main || { git rebase --abort 2>/dev/null; echo "pull --rebase falhou (tentativa $i)"; }
      if git push -q origin HEAD:main; then echo "Push OK: $(git rev-parse --short HEAD)"; break; fi
      echo "push rejeitado (tentativa $i)"; sleep $((i * 5))
    done
  } 2>&1 | tee "$GITLOG"
fi
exit 0
