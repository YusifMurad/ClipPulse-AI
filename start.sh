#!/bin/bash
# ClipForge - Başlatma scripti
cd "$(dirname "$0")"
export PATH="$HOME/.deno/bin:$PATH"
echo "ClipForge başlatılıyor..."
echo "Tarayıcıda açmak için: http://localhost:5555"
echo "Durdurmak için: Ctrl+C"
echo ""
cd backend
./venv/bin/python3 server.py
