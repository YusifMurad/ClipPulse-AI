# Contributing to ClipPulse AI 🎬

First off — thank you for taking the time to contribute. Every PR, bug report and idea makes
ClipPulse AI better for creators everywhere.

This guide gets you from zero to a running dev environment in about 5 minutes.

---

## 🧰 Prerequisites

- Python 3.12+
- FFmpeg (`sudo apt install ffmpeg` / `brew install ffmpeg`)
- Deno (`curl -fsSL https://deno.land/install.sh | sh`)
- A free [Google Gemini API key](https://aistudio.google.com/apikey)

---

## 🚀 Local dev setup

```bash
git clone https://github.com/YusifMurad/ClipPulse-AI.git
cd ClipPulse-AI

# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export PATH="$HOME/.deno/bin:$PATH"
python3 server.py          # → http://localhost:5555

# (Optional) Frontend dev — static files are served by the Flask backend,
# but you can also open index.html directly while the server runs.
```

The simplest path is just `./start.sh` from the repo root — it does the venv dance for you.

---

## 🌿 Branch & PR workflow

1. Fork & create a branch: `git checkout -b fix/subtitle-wrap` or `feat/auto-reframe`
2. Make your change. Keep PRs focused (one logical change per PR).
3. Run the checks locally:
   ```bash
   cd backend && source venv/bin/activate
   pip install ruff
   ruff check .
   ```
4. Commit with a clear message:
   - `feat:` new feature · `fix:` bug fix · `docs:` documentation · `chore:` maintenance
5. Open a Pull Request against `main`. Fill in the PR template.

---

## 🐳 Testing with Docker

```bash
docker compose up -d --build
```

---

## 🧭 Where to start

- [Good first issues](https://github.com/YusifMurad/ClipPulse-AI/labels/good%20first%20issue)
- [Help wanted](https://github.com/YusifMurad/ClipPulse-AI/labels/help%20wanted)
- [Discussions · Ideas](https://github.com/YusifMurad/ClipPulse-AI/discussions/categories/ideas)

---

## 📐 Code style

- **Python**: `ruff` (line length 100), type hints encouraged.
- **JS/CSS**: match the existing vanilla-JS style in `app.js` / `styles.css`.
- Keep the API key **server-side only** — never expose it to the client.
- Add a test or doc note for any user-facing behaviour change.

---

## 💬 Not sure where to start?

Open a [Discussion](https://github.com/YusifMurad/ClipPulse-AI/discussions) and ask.
We're happy to help you find a first task. 💜
