# ClipPulse AI - Windows (PowerShell) başlatma scripti
$ErrorActionPreference = "Stop"
Set-ExecutionPolicy -Scope Process Bypass -Force
Set-Location (Join-Path $PSScriptRoot "backend")

if (-not (Test-Path "venv")) {
  Write-Host "Virtual environment oluşturuluyor..."
  python -m venv venv
}
& "venv\Scripts\Activate.ps1"

Write-Host "Bağımlılıklar yükleniyor..."
pip install -r requirements.txt

Write-Host ""
Write-Host "ClipPulse AI başlatılıyor..."
Write-Host "Tarayıcıda açmak için: http://localhost:5555"
Write-Host "Durdurmak için: Ctrl+C"
Write-Host ""
python server.py
