# 🎬 ClipPulse AI

> **Paste a YouTube link → AI finds your best moments → Animated subtitles → Ready for TikTok, Reels & Shorts.**
> Free. Open source. Self-hosted. No credit card. No upload limits.

[![Stars](https://img.shields.io/github/stars/YusifMurad/ClipPulse-AI?style=for-the-badge)](https://github.com/YusifMurad/ClipPulse-AI/stargazers)
[![Forks](https://img.shields.io/github/forks/YusifMurad/ClipPulse-AI?style=for-the-badge)](https://github.com/YusifMurad/ClipPulse-AI/network/members)
[![License](https://img.shields.io/github/license/YusifMurad/ClipPulse-AI?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python&style=for-the-badge)](https://www.python.org)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-ready-green?logo=ffmpeg&style=for-the-badge)](https://ffmpeg.org)
[![Docker](https://img.shields.io/badge/Docker-ready-blue?logo=docker&style=for-the-badge)](https://github.com/YusifMurad/ClipPulse-AI/pkgs/container/clippulse-ai)
[![Discussions](https://img.shields.io/badge/Discussions-active-purple?logo=github&style=for-the-badge)](https://github.com/YusifMurad/ClipPulse-AI/discussions)
[![Twitter](https://img.shields.io/badge/Twitter-@yusifkishidir-1DA1F2?logo=twitter&style=for-the-badge)](https://twitter.com/yusifkishidir)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=for-the-badge)](CONTRIBUTING.md)
[![Last Commit](https://img.shields.io/github/last-commit/YusifMurad/ClipPulse-AI?style=for-the-badge)](https://github.com/YusifMurad/ClipPulse-AI/commits/main)

<p align="center">
  <a href="README.tr.md"><img src="https://img.shields.io/badge/lang-TR-red" alt="Türkçe"></a>
  <a href="README.es.md"><img src="https://img.shields.io/badge/lang-ES-orange" alt="Español"></a>
  <a href="README.ar.md"><img src="https://img.shields.io/badge/lang-AR-green" alt="العربية"></a>
  <a href="README.zh.md"><img src="https://img.shields.io/badge/lang-ZH-blue" alt="中文"></a>
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/5ae92a0d-b851-48d2-a31d-a771aaf24488" alt="ClipPulse AI Screenshot" width="900">
</p>

---

## ✨ Why ClipPulse AI?

You recorded a 40-minute podcast, livestream, or lecture. The gold is buried inside it — but
finding and cutting the 5 clips that will actually go viral takes hours. **ClipPulse AI does it in minutes.**

1. 🎯 **AI finds the moments** that hook viewers (Gemini scores each segment 0–100)
2. 📱 **9:16 vertical clips** formatted for every short-video platform
3. ✨ **OpusClip-style animated subtitles** (word-by-word color highlight)
4. 🧠 **14-language transcription** via Faster-Whisper (runs locally, your data stays yours)
5. 🖱️ **Browser editor** — trim, re-caption, re-score without leaving the tab

No subscriptions. No watermarks. No "free trial that clips 30 seconds." Yours to keep.

---

## 🚀 Quick Start — 30 seconds

```bash
git clone https://github.com/YusifMurad/ClipPulse-AI.git
cd ClipPulse-AI
chmod +x start.sh
./start.sh
```

Now open **http://localhost:5555**, paste a YouTube URL (or drop in an MP4), and hit **Create Clips**.

> 💡 First run installs a Python virtualenv automatically. You only need a free
> [Google Gemini API key](https://aistudio.google.com/apikey) (paste it once in Settings).

### 🐳 Or with Docker (one line)

```bash
docker run -p 5555:5555 -v "$PWD/output:/app/output" ghcr.io/yusifmurad/clippulse-ai:latest
```

### ☁️ Or in your browser (GitHub Codespaces)

[![Open in Codespaces](https://img.shields.io/badge/Open_in-Codespaces-blue?logo=github&style=for-the-badge)](https://codespaces.new/YusifMurad/ClipPulse-AI)

---

## 🎯 Who is this for?

| You are… | ClipPulse helps you… |
|----------|----------------------|
| 🎥 **Content Creator** | Turn one long video into 10+ shareable clips per week |
| 🏢 **Agency** | Batch-process client footage without manual editing |
| 🎓 **Educator** | Highlight key explanations from lectures |
| 🎙️ **Podcaster** | Promote episodes with punchy vertical snippets |
| ⛪ **Community / Non-profit** | Repurpose sermons and talks for social reach |
| 🛠️ **Developer** | Self-host a clip tool you fully control & can extend |

---

## ⚙️ How it works

```
YouTube / MP4
     │
     ▼
[1] Download / Accept upload      (yt-dlp + Deno JS runtime)
     │
     ▼
[2] Transcribe                      (Faster-Whisper, 14 langs, local)
     │
     ▼
[3] AI moment scoring              (Gemini 3.6 Flash → 0–100 viral score)
     │
     ▼
[4] Cut + reframe to 9:16           (FFmpeg)
     │
     ▼
[5] Animated ASS subtitles          (word-by-word highlight)
     │
     ▼
[6] Thumbnail + browser editor      (preview, trim, re-caption, download)
```

---

## 📦 Features

- 🎯 **AI Clip Selection** — automatic viral-moment detection (Gemini)
- 📱 **9:16 Vertical** — TikTok / Reels / Shorts ready
- ✨ **Animated Subtitles** — OpusClip-style word highlight, smart wrapping
- 📊 **Viral Score** — 0–100 potential per clip
- 🔤 **14 Languages** — en, tr, es, fr, de, it, pt, ru, ar, zh, ja, ko, hi, nl
- 📁 **Local Files** — upload your own MP4, nothing leaves your machine
- ✂️ **Clip Editor** — trim & re-caption in the browser
- 🖼️ **Auto Thumbnails** — cover image generated per clip
- 🧹 **Auto Cleanup** — disk space reclaimed automatically
- 🔒 **Private by design** — API key stored server-side, never sent to the client

---

## 🖥️ Installation (detailed)

### Requirements

- Python 3.12+
- FFmpeg
- Deno (for YouTube's JS challenges)
- A free [Google Gemini API key](https://aistudio.google.com/apikey)

### Manual

```bash
git clone https://github.com/YusifMurad/ClipPulse-AI.git
cd ClipPulse-AI/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
curl -fsSL https://deno.land/install.sh | sh
export PATH="$HOME/.deno/bin:$PATH"   # add to ~/.bashrc for permanence
sudo apt install ffmpeg               # or brew install ffmpeg
python3 server.py                    # → http://localhost:5555
```

### Docker Compose (recommended for prod)

```bash
git clone https://github.com/YusifMurad/ClipPulse-AI.git
cd ClipPulse-AI
docker compose up -d --build         # → http://localhost:5555
```

---

## 🧰 Usage

1. Open Settings → paste your Gemini API key (stored locally on the server).
2. Paste a YouTube link **or** upload an MP4.
3. Choose clip count & language → click **Create Clips**.
4. Preview, edit, and download your clips.

### REST API

```bash
# Create an API key
curl -X POST http://localhost:5555/api/v1/keys/create \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","plan":"free"}'

# Generate clips
curl -X POST http://localhost:5555/api/v1/generate \
  -H "X-API-Key: cf_xxxxx" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://youtube.com/watch?v=xxx","clip_count":3}'
```

---

## 🗺️ Roadmap

We plan in the open. 👉 **[Public Roadmap](ROADMAP.md)** ·
[Discussions · Ideas](https://github.com/YusifMurad/ClipPulse-AI/discussions/categories/ideas)

- [ ] Auto-reframe speaker tracking
- [ ] Batch folder processing
- [ ] Preset subtitle styles
- [ ] One-click direct upload to TikTok/Reels
- [ ] GPU transcription acceleration

---

## 🤝 Contributing

We love contributions — from a typo fix to a new AI model backend.

- Read **[CONTRIBUTING.md](CONTRIBUTING.md)** (5-minute dev setup)
- Pick a **[good first issue](https://github.com/YusifMurad/ClipPulse-AI/labels/good%20first%20issue)**
- Join the conversation in **[Discussions](https://github.com/YusifMurad/ClipPulse-AI/discussions)**

---

## 💬 Community

- 💡 Questions & ideas → **[GitHub Discussions](https://github.com/YusifMurad/ClipPulse-AI/discussions)**
- 🐦 Updates → **[@yusifkishidir](https://twitter.com/yusifkishidir)**
- 🐞 Bugs → **[Issues](https://github.com/YusifMurad/ClipPulse-AI/issues)**

---

## 🌟 Used by

> _Clipping for creators, agencies, educators and communities worldwide._
> Using ClipPulse AI? Open a
> [discussion](https://github.com/YusifMurad/ClipPulse-AI/discussions) and we'll add you here.

<!-- USED_BY_START -->
| User | Type |
|------|------|
| [Your Name / Brand](https://github.com/YusifMurad/ClipPulse-AI/discussions) | Creator |
<!-- USED_BY_END -->

---

## 📈 Star History

<a href="https://star-history.com/#YusifMurad/ClipPulse-AI&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=YusifMurad/ClipPulse-AI&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=YusifMurad/ClipPulse-AI&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=YusifMurad/ClipPulse-AI&type=Date" />
  </picture>
</a>

---

## 📚 Documentation

Full guides (tutorials, how-tos, API reference, architecture) →
🌐 **[docs.clippulse.ai](https://yusifmurad.github.io/ClipPulse-AI/)**
(multilingual: EN · TR · ES · AR · ZH)

---

## ❓ FAQ

**Is it really free?** Yes — MIT licensed, no paywalls in the code.
**Does my video leave my machine?** Local files are processed on your server.
YouTube fetches go through your instance only.
**Which AI model?** Gemini 3.6 Flash by default (free tier available).
**Can I run it on a VPS?** Yes — it's a standard Flask app behind any reverse proxy.

---

## 📄 License

[MIT](LICENSE) — use it freely, just keep the attribution.

<p align="center">
  Made with ❤️ by <a href="https://github.com/YusifMurad">Yusif Murad</a> and contributors.
</p>
