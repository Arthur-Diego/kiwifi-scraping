#!/usr/bin/env bash
set -euo pipefail

echo "==> Finalizando somente Streamlit..."
pkill -f "Python311/python.exe.*streamlit" || true
pkill -f "python3.*streamlit" || true

echo "✅ Streamlit finalizado. Docker/Qdrant continuam ativos."
