#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

CHANGED_FILES=""
if command -v git >/dev/null 2>&1; then
  CHANGED_FILES=$(git status --porcelain 2>/dev/null | awk "{print \$2}")
fi

WATCH_REGEX='^(src/|tests/|requeriments.txt|requirements.txt|docker-compose.yml|.*\.ya?ml$|.*\.toml$|.*\.ini$|.*\.cfg$|main.py|controller/|service/|repository/|rag_qdrant/|ui/|utils/|facade/|llm/)'
WATCHED=$(echo "$CHANGED_FILES" | awk "NF" | grep -E "$WATCH_REGEX" || true)

if [ -z "$WATCHED" ]; then
  WATCHED="nenhuma mudanca relevante detectada"
fi

export CONTEXT_UPDATE_DATE="$(date -Iseconds)"
export WATCHED_FILES="$WATCHED"

python - <<'PY'
import os, re
from pathlib import Path

path = Path("State.local.md")
text = path.read_text(encoding="utf-8") if path.exists() else "# State.local.md\n"

start = "<!-- AUTO-UPDATE-START -->"
end = "<!-- AUTO-UPDATE-END -->"

updated = os.environ.get("CONTEXT_UPDATE_DATE", "nao identificado")
watched = os.environ.get("WATCHED_FILES", "").strip().splitlines()
if not watched:
    watched = ["nao identificado"]

block = [start, f"- Atualizado em: {updated}", "- Arquivos alterados detectados:"]
for w in watched:
    block.append(f"- {w}")
block.append(end)
new_block = "\n".join(block)

if start in text and end in text:
    text = re.sub(re.escape(start) + r".*?" + re.escape(end), new_block, text, flags=re.S)
else:
    text = text + "\n\n" + new_block + "\n"

path.write_text(text, encoding="utf-8")
PY

./init-context.sh

echo "Atualizacao concluida."
