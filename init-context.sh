#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${1:-$ROOT_DIR/context_bundle.txt}"
RUN_CODEX="${2:-}"
CODEX_BIN="codex"
if command -v codex.cmd >/dev/null 2>&1; then
  CODEX_BIN="codex.cmd"
fi

{
  echo "README.md"
  echo "----------"
  cat "$ROOT_DIR/README.md"
  echo
  for f in "$ROOT_DIR/context/"*.md; do
    [ -f "$f" ] || continue
    echo "$(basename "$f")"
    echo "----------"
    cat "$f"
    echo
  done
} > "$OUT"

echo "Contexto gerado em: $OUT"

if [[ "$RUN_CODEX" == "--codex" ]]; then
  {
    echo "Use o contexto abaixo como base para o trabalho."
    echo
    cat "$OUT"
  } | "$CODEX_BIN" exec -
fi
