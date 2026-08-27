@echo off
REM ClipPulse AI - Windows başlatma scripti
cd /d "%~dp0backend"

if not exist "venv" (
  echo Virtual environment oluşturuluyor...
  python -m venv venv
)
call venv\Scripts\activate.bat

echo Bağımlılıklar yükleniyor...
pip install -r requirements.txt

echo.
echo ClipPulse AI başlatılıyor...
echo Tarayıcıda açmak için: http://localhost:5555
echo Durdurmak için: Ctrl+C
echo.
python server.py
