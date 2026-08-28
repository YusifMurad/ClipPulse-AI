# 🎬 ClipPulse AI

**Turn any long video into viral 9:16 clips for TikTok, Reels & Shorts — with AI.**

Paste a YouTube link or drop in your own video. ClipPulse uses **Google Gemini** to find the most engaging moments, generates **bold animated captions**, applies **auto zoom**, and drops everything into a built-in **clip editor** for fine-tuning. Everything runs **locally** — your videos never leave your machine.

> Building in public. Follow the journey on Threads [@yusifkishidir](https://www.threads.net/@yusifkishidir).

> 📘 **New here?** Full step-by-step tutorial (install, Gemini key, your first clip in 5 min): <https://docs.google.com/document/d/1FJCDa0gOhb5WGHNZhXCejX3ShV1lMpiTg2txsd16T5c/edit?tab=t.0#heading=h.o4q50hf8bf2>

---

## ✨ Why ClipPulse?

- 🧠 **AI Moment Finder** — Gemini scores every moment for virality and pulls the highlights (podcasts, gaming, sports, vlogs).
- 💬 **Animated Captions + Zoom** — word-synced subtitles with glow, gradient and auto zoom that locks onto the action.
- ✂️ **9:16 Clip Editor** — cut, split and delete on a timeline; retype captions; restyle colors; then re-render in one click.
- 🌍 **14 languages** — full UI in English, Türkçe, Deutsch, Français, Español, Italiano, Português, Русский, العربية, 日本語, 한국어, 中文, हिन्दी, Nederlands.
- 🚀 **Fast** — GPU-accelerated rendering with automatic CPU fallback.
- 🔒 **Private by design** — runs entirely in your browser + local server. Your Gemini key stays with you, files are processed locally, and there's no monthly lock-in.

## 🖥️ How it works

1. Paste a YouTube URL or upload an MP4/MOV/AVI.
2. ClipPulse downloads (or uses your file), transcribes the audio with Whisper, and asks Gemini to rank the viral moments.
3. Each moment is cut into a 9:16 clip with animated captions and zoom.
4. Open the **editor** to tweak text, colors, zoom focus and timing, then re-render.
5. Download your clips — done.

## 🚀 Quick start

### Requirements
- Python 3.10+
- [ffmpeg](https://ffmpeg.org/) on your `PATH`
- A [Google Gemini API key](https://aistudio.google.com/apikey) (free tier works)
- (optional) NVIDIA GPU for faster rendering

### Install & run

```bash
git clone https://github.com/YusifMurad/ClipPulse-AI.git
cd ClipPulse-AI
python3 -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt

# add your Gemini key (stored locally in backend/config/settings.json)
python3 backend/server.py  # then open http://localhost:5555 → Settings → paste key

# or set it directly
python3 - <<'PY'
import json, pathlib
p = pathlib.Path("backend/config/settings.json")
p.parent.mkdir(parents=True, exist_ok=True)
cfg = json.loads(p.read_text()) if p.exists() else {}
cfg["gemini_api_key"] = "YOUR_KEY_HERE"
p.write_text(json.dumps(cfg, indent=2))
PY

python3 backend/server.py
```

Open **http://localhost:5555** and start creating.

## ⚙️ Configuration

Settings (stored in `backend/config/settings.json`, git-ignored):

| Key | Description | Default |
|-----|-------------|---------|
| `gemini_api_key` | Google Gemini API key | — |
| `clip_count` | Clips generated per video | `6` |
| `whisper_model` | `tiny` / `base` / `small` | `base` |
| `language` | Transcription language (`""` = auto) | `""` |

## 🧩 Tech stack

- **Backend:** Flask, yt-dlp, OpenAI Whisper, Google Gemini, FFmpeg (libx264)
- **Frontend:** Vanilla JS, 14-language i18n, self-hosted Poppins, glassy dark UI

## 🗺️ Roadmap

- [ ] Brand kits (font / color / logo / caption style)
- [ ] Auto import + scheduling from YouTube/Twitch/Kick
- [ ] Multi-speaker labels & layout
- [ ] Landscape export presets
- [ ] One-click share to TikTok / Reels / Shorts

## 🤝 Contributing

PRs welcome! Run the translation parity check before opening a PR:

```bash
python3 scripts/check_translations.py
```

## 📄 License

MIT — do what you want, just keep the credits.
