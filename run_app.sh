#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Load .env to centralize sensitive configuration.
if [[ -f "$ROOT_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env"
  set +a
fi

LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$LOG_DIR"

TRANSCRIPTS_PATH=""
COLLECTION="${QDRANT_COLLECTION:-transcricoes}"
SKIP_INGEST="false"
SKIP_DB_INIT="false"
ARGS_PROVIDED="false"
UI_PAGE="chat"
STREAMLIT_PORT="${STREAMLIT_PORT:-8501}"
WITH_POSTGRES_CONTAINER="true"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-chat_history}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
POSTGRES_DSN="${POSTGRES_DSN:-postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}}"

usage() {
  cat <<'EOF'
Uso:
  ./run_app.sh [--transcripts "CAMINHO"] [--collection NOME] [--skip-ingest] [--skip-db-init] [--ui-page chat|dashboard|product-mining] [--streamlit-port PORT] [--without-postgres-container]

Exemplos:
  ./run_app.sh --transcripts "/mnt/c/Users/arthu/OneDrive/Área de Trabalho/CURSO_CVD"
  ./run_app.sh --transcripts "C:\Users\arthu\OneDrive\Área de Trabalho\CURSO_CVD"
  ./run_app.sh --skip-ingest
  ./run_app.sh --skip-db-init
  ./run_app.sh --ui-page dashboard
  ./run_app.sh --ui-page product-mining
  ./run_app.sh --streamlit-port 8502
  ./run_app.sh --without-postgres-container
EOF
}

while [[ $# -gt 0 ]]; do
  ARGS_PROVIDED="true"
  case "$1" in
    --transcripts)
      TRANSCRIPTS_PATH="${2:-}"
      shift 2
      ;;
    --collection)
      COLLECTION="${2:-transcricoes}"
      shift 2
      ;;
    --skip-ingest)
      SKIP_INGEST="true"
      shift
      ;;
    --skip-db-init)
      SKIP_DB_INIT="true"
      shift
      ;;
    --ui-page)
      UI_PAGE="${2:-chat}"
      shift 2
      ;;
    --streamlit-port)
      STREAMLIT_PORT="${2:-8501}"
      shift 2
      ;;
    --without-postgres-container)
      WITH_POSTGRES_CONTAINER="false"
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

  if ask_yes_no "Deseja rodar ingestão/reindex agora?" "n"; then
    SKIP_INGEST="false"
    read -r -p "Caminho das transcrições: " TRANSCRIPTS_PATH
    read -r -p "Coleção Qdrant [transcricoes]: " input_collection
    COLLECTION="${input_collection:-transcricoes}"
  else
    SKIP_INGEST="true"
  fi

  if ask_yes_no "Deseja pular init do Postgres?" "n"; then
    SKIP_DB_INIT="true"
  else
    SKIP_DB_INIT="false"
  fi

  read -r -p "Qual tela Streamlit deseja abrir? [chat/dashboard/product-mining]: " input_ui
  UI_PAGE="${input_ui:-chat}"

  if ask_yes_no "Deseja subir container Postgres local?" "y"; then
    WITH_POSTGRES_CONTAINER="true"
  else
    WITH_POSTGRES_CONTAINER="false"
  fi
fi

if [[ "$UI_PAGE" != "chat" && "$UI_PAGE" != "dashboard" && "$UI_PAGE" != "product-mining" ]]; then
  echo "Erro: --ui-page deve ser 'chat', 'dashboard' ou 'product-mining'."
  exit 1
fi

if ! [[ "$STREAMLIT_PORT" =~ ^[0-9]+$ ]]; then
  echo "Erro: --streamlit-port deve ser numérico."
  exit 1
fi

port_is_busy() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    lsof -iTCP:"$port" -sTCP:LISTEN -nP >/dev/null 2>&1
    return $?
  fi
  if command -v ss >/dev/null 2>&1; then
    ss -ltn "sport = :$port" 2>/dev/null | tail -n +2 | grep -q .
    return $?
  fi
  return 1
}

pick_free_port() {
  local base="$1"
  local max_tries=20
  local i=0
  local candidate="$base"
  while (( i < max_tries )); do
    if ! port_is_busy "$candidate"; then
      echo "$candidate"
      return 0
    fi
    candidate=$((candidate + 1))
    i=$((i + 1))
  done
  echo "$base"
  return 0
}

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

python_has_required_modules() {
  local py="$1"
  if eval "$py -c \"import uvicorn, streamlit, psycopg2\" >/dev/null 2>&1"; then
    return 0
  fi
  return 1
}

DOCKER_CMD="$(find_docker_cmd || true)"
PY_CMD="$(find_python_cmd || true)"

if [[ -z "$DOCKER_CMD" ]]; then
  echo "Erro: docker não encontrado (nem docker.exe)."
  exit 1
fi

if [[ -z "$PY_CMD" ]]; then
  echo "Erro: Python não encontrado."
  exit 1
fi

# Se python3 do WSL não tiver dependências, tenta fallback para Python do Windows.
if ! python_has_required_modules "$PY_CMD"; then
  WIN_PY="\"/mnt/c/Users/arthu/AppData/Local/Programs/Python/Python311/python.exe\""
  if [[ "$PY_CMD" != "$WIN_PY" ]] && [[ -x /mnt/c/Users/arthu/AppData/Local/Programs/Python/Python311/python.exe ]] && python_has_required_modules "$WIN_PY"; then
    echo "Aviso: '$PY_CMD' sem módulos necessários. Usando Python do Windows."
    PY_CMD="$WIN_PY"
  else
    echo "Erro: Python encontrado, mas faltam módulos obrigatórios ('uvicorn', 'streamlit' e/ou 'psycopg2')."
    echo "Instale dependências ou defina PYTHON_CMD com um ambiente pronto."
    exit 1
  fi
fi

echo "==> Subindo Qdrant..."
eval "$DOCKER_CMD compose -f docker-compose.yml up -d qdrant"

if [[ "$WITH_POSTGRES_CONTAINER" == "true" ]]; then
  echo "==> Subindo Postgres..."
  eval "$DOCKER_CMD compose -f docker-compose.yml up -d postgres"
fi

echo "==> Encerrando Streamlit anterior (se existir)..."
pkill -f "Python311/python.exe.*streamlit" || true
pkill -f "python3.*streamlit" || true
echo "==> Encerrando API anterior (se existir)..."
pkill -f "Python311/python.exe.*uvicorn main:app" || true
pkill -f "python3.*uvicorn main:app" || true

if [[ "$SKIP_DB_INIT" != "true" ]]; then
  echo "==> Inicializando Postgres (schema)..."
  DB_INIT_PY="$PY_CMD"
  if command -v python3 >/dev/null 2>&1; then
    DB_INIT_PY="python3"
  fi

  if command -v timeout >/dev/null 2>&1; then
    if ! eval "env POSTGRES_DSN=\"$POSTGRES_DSN\" timeout 90s $DB_INIT_PY -m scripts.init_db --db-dsn \"$POSTGRES_DSN\""; then
      echo "Aviso: init_db falhou ou expirou timeout. Continuando subida da aplicação."
      echo "Dica: rode manualmente depois com '--skip-db-init' no run_app."
    fi
  else
    if ! eval "env POSTGRES_DSN=\"$POSTGRES_DSN\" $DB_INIT_PY -m scripts.init_db --db-dsn \"$POSTGRES_DSN\""; then
      echo "Aviso: init_db falhou. Continuando subida da aplicação."
    fi
  fi
fi

if [[ "$SKIP_INGEST" != "true" && -n "$TRANSCRIPTS_PATH" ]]; then
  echo "==> Indexando transcrições em '$TRANSCRIPTS_PATH' (coleção: $COLLECTION)..."
  eval "$PY_CMD -m scripts.reindex --inputs \"$TRANSCRIPTS_PATH\" --collection \"$COLLECTION\""
fi

echo "==> Iniciando API (FastAPI) em background..."
nohup bash -lc "cd \"$ROOT_DIR\" && POSTGRES_DSN=\"$POSTGRES_DSN\" $PY_CMD -m uvicorn main:app --host 0.0.0.0 --port 8000" \
  > "$LOG_DIR/api.log" 2>&1 &
API_PID=$!

STREAMLIT_APP="src/interface/streamlit_app/app.py"
if [[ "$UI_PAGE" == "dashboard" ]]; then
  STREAMLIT_APP="src/interface/streamlit_app/campaign_dashboard.py"
elif [[ "$UI_PAGE" == "product-mining" ]]; then
  STREAMLIT_APP="src/interface/streamlit_app/product_mining_dashboard.py"
fi

SELECTED_STREAMLIT_PORT="$(pick_free_port "$STREAMLIT_PORT")"
if [[ "$SELECTED_STREAMLIT_PORT" != "$STREAMLIT_PORT" ]]; then
  echo "Aviso: porta $STREAMLIT_PORT ocupada. Usando $SELECTED_STREAMLIT_PORT."
fi

echo "==> Iniciando UI (Streamlit) em background..."
nohup bash -lc "cd \"$ROOT_DIR\" && POSTGRES_DSN=\"$POSTGRES_DSN\" $PY_CMD -m streamlit run $STREAMLIT_APP --server.port $SELECTED_STREAMLIT_PORT --server.address 0.0.0.0" \
  > "$LOG_DIR/streamlit.log" 2>&1 &
STREAMLIT_PID=$!

cat <<EOF

Stack iniciada.

PIDs:
- API: $API_PID
- Streamlit: $STREAMLIT_PID

Acesse no browser:
- App (Streamlit): http://localhost:$SELECTED_STREAMLIT_PORT
- Tela selecionada: $UI_PAGE ($STREAMLIT_APP)
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Qdrant: http://localhost:6333
- Postgres DSN: $POSTGRES_DSN

Logs:
- $LOG_DIR/api.log
- $LOG_DIR/streamlit.log

EOF
