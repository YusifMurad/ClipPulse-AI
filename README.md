# ClipPulse AI 🎬

Takes long videos, finds the most engaging moments with AI, and turns them into TikTok/Reels/Shorts clips. Animated subtitles, vertical format, fully automatic.

> Paste a YouTube link or upload an MP4 — AI handles the rest.

![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python)
![FFmpeg](https://img.shields.io/badge/FFmpeg-green?logo=ffmpeg)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- 🎯 **AI Clip Selection** — Finds viral moments automatically using Gemini AI
- 📱 **9:16 Vertical Format** — Ready for TikTok, Instagram Reels, YouTube Shorts
- ✨ **Animated Subtitles** — Word-by-word color animation (OpusClip-style)
- 📊 **Viral Score** — 0-100 potential score for each clip
- 🔤 **Multi-language** — 14 languages for transcription
- 📁 **Local File Support** — Upload your own MP4 files
- ✂️ **Clip Editor** — Edit clips directly in the browser
- 🧹 **Auto Cleanup** — Automatically frees up disk space

## Setup

### Requirements

- Python 3.12+
- FFmpeg
- Deno (for YouTube JS challenges)
- Google Gemini API Key ([Free](https://aistudio.google.com/apikey))

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/YusifMurad/ClipPulse-AI.git
cd ClipPulse-AI

# 2. Create Python virtualenv
cd backend
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install flask flask-cors yt-dlp faster-whisper google-genai curl_cffi==0.15.0

# 4. Install Deno (for yt-dlp)
curl -fsSL https://deno.land/install.sh | sh
export PATH="$HOME/.deno/bin:$PATH"

# 5. Install FFmpeg (if not installed)
sudo apt install ffmpeg

# 6. Start the server
python3 server.py
```

### Quick Start

```bash
chmod +x start.sh
./start.sh
```

Open in browser: **http://localhost:5555**

## Usage

1. Enter your Google Gemini API key in Settings
2. Paste a YouTube link or upload an MP4 file
3. Click "Create Clips"
4. Preview, edit, and download your clips

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask |
| AI Analysis | Google Gemini |
| Transcription | faster-whisper |
| Video Download | yt-dlp |
| Video Processing | FFmpeg |
| Frontend | Vanilla JS, HTML, CSS |

## API

```bash
# Create an API key
curl -X POST http://localhost:5555/api/v1/keys/create \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","plan":"free"}'

# Generate clips
curl -X POST http://localhost:5555/api/v1/generate \
  -H "X-API-Key: cf_xxxxx" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://youtube.com/watch?v=xxx","clip_count":3}'
```

## License

MIT License — Use it freely.
