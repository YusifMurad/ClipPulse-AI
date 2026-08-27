# Getting Started

There are three ways to run ClipPulse AI.

## 1. Local (recommended for development)

Requirements: Python 3.12+, FFmpeg, Deno, a free Gemini API key.

```bash
git clone https://github.com/YusifMurad/ClipPulse-AI.git
cd ClipPulse-AI
chmod +x start.sh
./start.sh
```

Open **http://localhost:5555**. On first run a Python virtualenv is created for you.

### Manual setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export PATH="$HOME/.deno/bin:$PATH"   # Deno for yt-dlp
sudo apt install ffmpeg               # or: brew install ffmpeg
python3 server.py
```

## 2. Docker

```bash
docker compose up -d --build
# → http://localhost:5555
```

Or pull the prebuilt image:

```bash
docker run -p 5555:5555 -v "$PWD/output:/app/output" \
  ghcr.io/yusifmurad/clippulse-ai:latest
```

## 3. GitHub Codespaces

Click **Open in Codespaces** on the repo, wait ~2 minutes, then open the
forwarded port `5555` in your browser.

## First run

1. Settings → paste your Gemini API key (stored server-side, never sent to the client).
2. Paste a YouTube URL or upload an MP4.
3. Click **Create Clips**.
4. Preview, edit, and download.
