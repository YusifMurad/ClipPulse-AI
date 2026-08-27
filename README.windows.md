# 🪟 ClipPulse AI — Windows Installation Guide

This guide walks you through running **ClipPulse AI** on Windows 10/11 (64-bit).
ClipPulse is fully cross-platform — the same code runs on Linux, macOS, and Windows.

> 💡 **TL;DR:** Install Python + FFmpeg, then run **`start.ps1`** (PowerShell) or
> **`start.bat`** (Command Prompt). The script creates a virtual environment and
> installs everything for you.

---

## 1. What you need

| Requirement | Why | Optional? |
|-------------|-----|-----------|
| **Windows 10/11 64-bit** | — | Required |
| **Python 3.12+** | Runs the backend | Required |
| **FFmpeg** | Video cutting & subtitles | Required |
| **Git for Windows** | Clone the repo | Required |
| **Deno** | Better YouTube downloads | *Optional* (recommended) |
| **Google Gemini API key** | AI moment detection | Required (free) |

---

## 2. Install Python

1. Download the **Windows installer** from <https://www.python.org/downloads/windows/>.
2. Run it and **tick both boxes**:
   - ✅ *Add python.exe to PATH*
   - ✅ *Disable path length limit* (avoids long-path errors later)
3. Click *Install Now*.

**Verify** (open a new PowerShell / CMD window):

```powershell
python --version
# Python 3.12.x
```

> ⚠️ If `python` is not recognized, you probably installed Python from the
> Microsoft Store and it didn't add to PATH, or a Store alias is intercepting it.
> Re-run the installer and make sure *Add to PATH* is checked, or use the
> "App execution aliases" settings to disable the `python.exe` Store stub.

---

## 3. Install FFmpeg

Pick **one** method:

**Option A — Chocolatey (recommended):**

```powershell
choco install ffmpeg
```

**Option B — Winget:**

```powershell
winget install Gyan.FFmpeg
```

**Option C — Manual:**
1. Download `ffmpeg-master-latest-win64-gpl.zip` from <https://ffmpeg.org/download.html>.
2. Extract it (e.g. to `C:\ffmpeg`).
3. Add `C:\ffmpeg\bin` to your **Path** environment variable
   (Settings → System → About → Advanced system settings → Environment Variables →
   edit *Path* → New → `C:\ffmpeg\bin`).
4. Restart your terminal.

**Verify:**

```powershell
ffmpeg -version
# ffmpeg version ...
```

---

## 4. (Optional) Install Deno — for reliable YouTube downloads

YouTube's player uses JavaScript challenges. `yt-dlp` can solve them with the
**Deno** runtime. Without Deno, ClipPulse still tries fallback strategies, but
they are less reliable on YouTube.

```powershell
winget install DenoLand.Deno
# or
iwr https://deno.land/install.ps1 | iex
```

**Verify:**

```powershell
deno --version
```

If Deno is installed, ClipPulse detects it automatically — no configuration needed.

---

## 5. Get the code

```powershell
git clone https://github.com/YusifMurad/ClipPulse-AI.git
cd ClipPulse-AI
```

---

## 6. Run ClipPulse

### PowerShell (recommended)

```powershell
.\start.ps1
```

The first run will:
1. Create a Python virtual environment in `backend\venv`.
2. `pip install -r requirements.txt` (can take a few minutes — it pulls Flask,
   Faster-Whisper, yt-dlp, Google GenAI, etc.).
3. Start the web server.

### Command Prompt

```cmd
start.bat
```

When you see:

```
ClipPulse AI başlatılıyor...
Tarayıcıda açmak için: http://localhost:5555
```

open **http://localhost:5555** in your browser.

> The very first clip you generate also downloads the Whisper speech model
> (~150 MB), so the first job is slower. After that it's cached.

---

## 7. Add your Gemini API key

1. Get a free key: <https://aistudio.google.com/apikey>.
2. In ClipPulse, open **Settings** (sidebar) → paste the key → **Save Settings**.
3. The key is stored only on your machine (server-side). It is never sent to the browser.

You're done — paste a YouTube URL or drop in an MP4 and click **Create Clips**. 🎉

---

## 8. Running from Command Prompt vs PowerShell

| You want… | Use |
|-----------|-----|
| Modern shell, colored output | `start.ps1` (PowerShell) |
| Classic CMD | `start.bat` |

Both do exactly the same thing. `start.ps1` may prompt about script execution
policy the first time — it self-elevates with `Bypass` for the current process,
so you don't need to change system settings.

---

## 9. Stopping the server

Press **Ctrl + C** in the window where it's running. The Python virtualenv keeps
your installed packages for next time (restart is instant).

---

## 10. Docker on Windows (alternative)

If you have **Docker Desktop** (with WSL2 backend), you can skip Python/FFmpeg
installs entirely:

```powershell
docker run -p 5555:5555 -v "${PWD}/output:/app/output" ghcr.io/yusifmurad/clippulse-ai:latest
```

---

## 11. Troubleshooting

| Problem | Fix |
|---------|-----|
| `python` is not recognized | Reinstall Python with *Add to PATH* checked; or use the full path `C:\Python312\python.exe`. |
| `ffmpeg` is not recognized | FFmpeg not on PATH — reinstall (step 3) and restart the terminal. |
| `pip` fails with long path errors | Reinstall Python and tick *Disable path length limit*. |
| Port 5555 already in use | Close the other app, or edit `backend/server.py` (`port=5555`) and restart. |
| YouTube download fails on Windows | Install **Deno** (step 4) and retry; some videos need it. |
| First run is very slow | Normal — it's installing packages and downloading the Whisper model. |
| Blank page / can't connect | Make sure the server window is still open and visit `http://127.0.0.1:5555`. |
| Firewall prompt | Allow Python through the firewall for private networks. |

---

## 12. Building the desktop app (optional)

ClipPulse also ships an **Electron** wrapper (`electron/`). To run it on Windows
you need Node.js + the Python backend running:

```powershell
# terminal 1 — start the backend
.\start.ps1

# terminal 2 — start the desktop shell
cd electron
npm install
npm start
```

The Electron build invokes `backend\venv\Scripts\python.exe` automatically on
Windows, and `backend\venv\bin\python3` on Linux/macOS.

---

## 13. Updating

```powershell
git pull
.\start.ps1   # re-installs any new dependencies
```

---

Happy clipping! 🎬 If you get stuck, open an issue or a discussion on
[GitHub](https://github.com/YusifMurad/ClipPulse-AI/discussions).
