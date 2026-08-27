#!/bin/bash
# ClipPulse AI - Başlatma scripti (Linux / macOS)
set -e
cd "$(dirname "$0")"
cd backend

# yt-dlp, YouTube indirmek için deno JS runtime kullanıyorsa PATH'e ekle
if [ -x "$HOME/.deno/bin/deno" ]; then
  export PATH="$HOME/.deno/bin:$PATH"
fi

if [ ! -d "venv" ]; then
  echo "Virtual environment oluşturuluyor..."
  python3 -m venv venv
fi
# shellcheck disable=SC1091
source venv/bin/activate

echo "Bağımlılıklar yükleniyor..."
pip install -r requirements.txt

echo ""
echo "ClipPulse AI başlatılıyor..."
echo "Tarayıcıda açmak için: http://localhost:5555"
echo "Durdurmak için: Ctrl+C"
echo ""
python server.py
