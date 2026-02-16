#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

COLLECTION="${QDRANT_COLLECTION:-transcricoes}"
TRANSCRIPTS_PATH=""
WITH_REINDEX="false"
RESTART_DOCKER="false"
ARGS_PROVIDED="false"

usage() {
  cat <<'EOF'
Uso:
  ./reset_qdrant.sh [--collection NOME] [--with-reindex --transcripts CAMINHO] [--restart-docker]

Exemplos:
  ./reset_qdrant.sh
  ./reset_qdrant.sh --collection transcricoes
  ./reset_qdrant.sh --with-reindex --transcripts "C:\Users\arthu\OneDrive\Área de Trabalho\CURSO_CVD"
  ./reset_qdrant.sh --restart-docker --with-reindex --transcripts "/mnt/c/Users/arthu/OneDrive/Área de Trabalho/CURSO_CVD"
EOF
}

while [[ $# -gt 0 ]]; do
  ARGS_PROVIDED="true"
  case "$1" in
    --collection)
      COLLECTION="${2:-}"
      shift 2
      ;;
    --with-reindex)
      WITH_REINDEX="true"
      shift
      ;;
    --transcripts)
      TRANSCRIPTS_PATH="${2:-}"
      shift 2
      ;;
    --restart-docker)
      RESTART_DOCKER="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Argumento inválido: $1"
      usage
      exit 1
      ;;
  esac
done

ask_yes_no() {
  local prompt="$1"
  local default="${2:-y}"
  local answer
  local hint="[Y/n]"
  if [[ "$default" == "n" ]]; then
    hint="[y/N]"
  fi
  read -r -p "$prompt $hint: " answer
  answer="${answer,,}"
  if [[ -z "$answer" ]]; then
    answer="$default"
  fi
  [[ "$answer" == "y" || "$answer" == "yes" ]]
}

if [[ "$ARGS_PROVIDED" != "true" ]]; then
  echo "Nenhum parâmetro informado. Modo interativo ativado."
  read -r -p "Coleção para reset [transcricoes]: " input_collection
  COLLECTION="${input_collection:-transcricoes}"

  if ask_yes_no "Reiniciar docker compose antes do reset?" "n"; then
    RESTART_DOCKER="true"
  fi

  if ask_yes_no "Executar reindex após reset?" "n"; then
    WITH_REINDEX="true"
    read -r -p "Caminho das transcrições: " TRANSCRIPTS_PATH
  fi
fi

if [[ "$WITH_REINDEX" == "true" && -z "$TRANSCRIPTS_PATH" ]]; then
  echo "Erro: use --transcripts CAMINHO junto com --with-reindex."
  exit 1
fi

find_docker_cmd() {
  if command -v docker >/dev/null 2>&1; then
    echo "docker"
    return 0
  fi
  if [[ -x "/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe" ]]; then
    echo "\"/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe\""
    return 0
  fi
  return 1
}

find_python_cmd() {
  if [[ -n "${PYTHON_CMD:-}" ]]; then
    echo "$PYTHON_CMD"
    return 0
  fi
  if command -v python3 >/dev/null 2>&1; then
    echo "python3"
    return 0
  fi
  if [[ -x "/mnt/c/Users/arthu/AppData/Local/Programs/Python/Python311/python.exe" ]]; then
    echo "\"/mnt/c/Users/arthu/AppData/Local/Programs/Python/Python311/python.exe\""
    return 0
  fi
  return 1
}

python_has_modules() {
  local py="$1"
  local modules_csv="$2"
  eval "$py -c \"import ${modules_csv}\" >/dev/null 2>&1"
}

DOCKER_CMD="$(find_docker_cmd || true)"
PY_CMD="$(find_python_cmd || true)"

if [[ -z "$PY_CMD" ]]; then
  echo "Erro: Python não encontrado."
  exit 1
fi

# Módulos mínimos para reset da coleção.
if ! python_has_modules "$PY_CMD" "qdrant_client"; then
  WIN_PY="\"/mnt/c/Users/arthu/AppData/Local/Programs/Python/Python311/python.exe\""
  if [[ "$PY_CMD" != "$WIN_PY" ]] && [[ -x /mnt/c/Users/arthu/AppData/Local/Programs/Python/Python311/python.exe ]] && python_has_modules "$WIN_PY" "qdrant_client"; then
    echo "Aviso: '$PY_CMD' sem qdrant_client. Usando Python do Windows."
    PY_CMD="$WIN_PY"
  else
    echo "Erro: Python selecionado não possui qdrant_client."
    echo "Defina PYTHON_CMD com um ambiente que tenha as dependências."
    exit 1
  fi
fi

# Módulos adicionais para reindex (scripts.reindex importa wiring/llm no carregamento).
if [[ "$WITH_REINDEX" == "true" ]] && ! python_has_modules "$PY_CMD" "qdrant_client,sentence_transformers,dotenv,langchain_openai,langchain_core"; then
  WIN_PY="\"/mnt/c/Users/arthu/AppData/Local/Programs/Python/Python311/python.exe\""
  if [[ "$PY_CMD" != "$WIN_PY" ]] && [[ -x /mnt/c/Users/arthu/AppData/Local/Programs/Python/Python311/python.exe ]] && python_has_modules "$WIN_PY" "qdrant_client,sentence_transformers,dotenv,langchain_openai,langchain_core"; then
    echo "Aviso: '$PY_CMD' sem stack completa de reindex. Usando Python do Windows."
    PY_CMD="$WIN_PY"
  else
    echo "Erro: Python selecionado não possui stack completa para reindex."
    echo "Módulos esperados: qdrant_client, sentence_transformers, dotenv, langchain_openai, langchain_core."
    exit 1
  fi
fi

if [[ "$RESTART_DOCKER" == "true" ]]; then
  if [[ -z "$DOCKER_CMD" ]]; then
    echo "Erro: docker não encontrado para --restart-docker."
    exit 1
  fi
  echo "==> Reiniciando stack do Qdrant..."
  eval "$DOCKER_CMD compose -f docker-compose.yml down"
  eval "$DOCKER_CMD compose -f docker-compose.yml up -d"
fi

echo "==> Resetando coleção '$COLLECTION'..."
RESET_COLLECTION="$COLLECTION" eval "$PY_CMD - <<'PY'
from qdrant_client import QdrantClient
import os

collection = os.environ.get('RESET_COLLECTION', 'transcricoes')
client = QdrantClient(url=os.environ.get('QDRANT_URL', 'http://localhost:6333'))
try:
    client.delete_collection(collection_name=collection)
    print(f'Coleção removida: {collection}')
except Exception as exc:
    print(f'Aviso ao remover coleção: {exc}')
print('Reset concluído.')
PY"

if [[ "$WITH_REINDEX" == "true" ]]; then
  echo "==> Reindexando transcrições em '$TRANSCRIPTS_PATH'..."
  eval "$PY_CMD -m scripts.reindex --inputs \"$TRANSCRIPTS_PATH\" --collection \"$COLLECTION\""
fi

echo "✅ Qdrant resetado com sucesso."
