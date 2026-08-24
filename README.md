# ClipPulse AI 🎬

AI destekli video klip editörü. YouTube videolarından veya yerel MP4 dosyalarından, en viral anları otomatik bulup 9:16 dikey formatlarda.animasyonlu altyazılı klipler oluşturur.

![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python)
![FFmpeg](https://img.shields.io/badge/FFmpeg-g Mandatory-green?logo=ffmpeg)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Özellikler

- 🎯 **AI Klip Seçimi** — Gemini AI ile viral potansiyeli yüksek anları otomatik bulur
- 📱 **9:16 Dikey Format** — TikTok, Instagram Reels, YouTube Shorts için hazır
- ✨ **Animasyonlu Altyazılar** — Kelime kelime renk animasyonu (OpusClip tarzı)
- 📊 **Viral Skor** — Her klip için 0-100 arası potansiyel skoru
- 🔤 **Dil Desteği** — 14 dilde transkripsiyon
- 📁 **Yerel Dosya Desteği** — Bilgisayarınızdaki MP4'leri işleyin
- ✂️ **Klip Editörü** — Klipleri tarayıcıdan düzenleyin
- 🧹 **Otomatik Temizlik** — Disk alanını otomatik korur

## Kurulum

### Gereksinimler

- Python 3.12+
- FFmpeg
- Deno (YouTube JS çözümü için)
- Google Gemini API Key ([Ücretsiz](https://aistudio.google.com/apikey))

### Adımlar

```bash
# 1. Repoyu klonla
git clone https://github.com/KULLANICI_ADIN/clipforge.git
cd clipforge

# 2. Python virtualenv oluştur
cd backend
python3 -m venv venv
source venv/bin/activate

# 3. Bağımlılıkları kur
pip install flask flask-cors yt-dlp faster-whisper google-genai curl_cffi==0.15.0

# 4. Deno kur (yt-dlp için)
curl -fsSL https://deno.land/install.sh | sh
export PATH="$HOME/.deno/bin:$PATH"

# 5. FFmpeg kur (yoksa)
sudo apt install ffmpeg

# 6. Sunucuyu başlat
python3 server.py
```

### Hızlı Başlangıç

```bash
# Bir tıkla başlat
chmod +x start.sh
./start.sh
```

Tarayıcıda aç: **http://localhost:5555**

## Kullanım

1. Ayarlar'dan Google Gemini API key girin
2. YouTube linki yapıştırın veya MP4 dosyası yükleyin
3. "Clip Oluştur" butonuna basın
4. Klipleri önizleyin, düzenleyin ve indirin

## Teknoloji

| Katman | Teknoloji |
|--------|-----------|
| Backend | Python, Flask |
| AI Analiz | Google Gemini |
| Transkripsiyon | faster-whisper |
| Video İndirme | yt-dlp |
| Video İşleme | FFmpeg |
| Frontend | Vanilla JS, HTML, CSS |

## API

```bash
# API Key oluştur
curl -X POST http://localhost:5555/api/v1/keys/create \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","plan":"free"}'

# Clip oluştur
curl -X POST http://localhost:5555/api/v1/generate \
  -H "X-API-Key: cf_xxxxx" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://youtube.com/watch?v=xxx","clip_count":3}'
```

## Lisans

MIT License — Özgürce kullan, değiştir ve paylaş.
