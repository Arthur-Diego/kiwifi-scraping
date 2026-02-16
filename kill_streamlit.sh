#!/usr/bin/env bash
set -euo pipefail

echo "==> Encerrando processos Streamlit (sem mexer em Docker/Qdrant)..."

# 1) Linux/WSL process kill by command signature
pkill -f "streamlit run" 2>/dev/null || true
pkill -f "python3.*streamlit" 2>/dev/null || true
pkill -f "Python311/python.exe.*streamlit" 2>/dev/null || true

# 2) Free the common Streamlit port on Linux side
if command -v fuser >/dev/null 2>&1; then
  fuser -k 8501/tcp >/dev/null 2>&1 || true
fi

# 3) If running under WSL, try to kill on Windows side too
if grep -qi "microsoft" /proc/version 2>/dev/null; then
  WIN_TASKKILL="/mnt/c/Windows/System32/taskkill.exe"
  WIN_CMD="/mnt/c/Windows/System32/cmd.exe"
  if [[ -x "$WIN_TASKKILL" ]]; then
    "$WIN_TASKKILL" /F /IM streamlit.exe >/dev/null 2>&1 || true
    "$WIN_TASKKILL" /F /FI "WINDOWTITLE eq Kiwifi Streamlit*" >/dev/null 2>&1 || true
    "$WIN_TASKKILL" /F /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq Kiwifi Streamlit*" >/dev/null 2>&1 || true
  fi

  # Optional: kill PID bound to 8501 in Windows networking stack
  if [[ -x "$WIN_CMD" ]]; then
    "$WIN_CMD" /c "for /f \"tokens=5\" %a in ('netstat -ano ^| findstr :8501 ^| findstr LISTENING') do taskkill /F /PID %a" >/dev/null 2>&1 || true
  fi
fi

echo "✅ Streamlit encerrado (quando encontrado). Docker/Qdrant seguem ativos."
