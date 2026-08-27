import os
import uuid
import json
import time
import threading
import atexit
import shutil
import hashlib
from pathlib import Path
from functools import wraps

from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS

from pipeline import process_video, OUTPUT_DIR, recut_clip, rebuild_clip_ass

app = Flask(__name__)
CORS(app)

# --- Rate Limiting ---
_rate_store = {}
RATE_LIMIT = 30  # requests per minute per IP
RATE_WINDOW = 60

def rate_limit(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        ip = request.remote_addr
        now = time.time()
        if ip not in _rate_store:
            _rate_store[ip] = []
        _rate_store[ip] = [t for t in _rate_store[ip] if now - t < RATE_WINDOW]
        if len(_rate_store[ip]) >= RATE_LIMIT:
            return jsonify({"error": "Rate limit exceeded. Try again later."}), 429
        _rate_store[ip].append(now)
        return f(*args, **kwargs)
    return wrapper

# --- Kalıcılık (persist) ---
# Outputs are kept across restarts; results are mirrored to disk so editing
# metadata survives a server restart.
def persist_job(job_id):
    try:
        job = jobs.get(job_id)
        if not job:
            return
        path = OUTPUT_DIR / job_id / "_result.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(job, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

def load_persisted(job_id):
    """Load a finished job's result from disk if it's not in memory."""
    if job_id in jobs:
        return True
    path = OUTPUT_DIR / job_id / "_result.json"
    if path.exists():
        try:
            jobs[job_id] = json.loads(path.read_text(encoding="utf-8"))
            return True
        except Exception:
            pass
    return False


def _ass_sec(t):
    """Parse ASS timestamp 'h:mm:ss.cc' to seconds."""
    h, m, rest = t.split(":")
    s, cs = rest.split(".")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(cs) / 100.0

# --- Temizlik ---
def cleanup():
    print("Sunucu kapanıyor.")

atexit.register(cleanup)
# ----------------

jobs = {}

UPLOAD_DIR = OUTPUT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

CONFIG_DIR = Path(__file__).parent / "config"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def load_api_key():
    """Load API key from server-side config only — never from client."""
    settings_path = CONFIG_DIR / "settings.json"
    if settings_path.exists():
        with open(settings_path) as f:
            data = json.load(f)
        return data.get("api_key", "")
    return ""


@app.route("/api/upload", methods=["POST"])
@rate_limit
def upload_file():
    """Save an uploaded video file and return its server-side path."""
    if "file" not in request.files:
        return jsonify({"error": "file alanı eksik"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Dosya seçilmedi"}), 400

    # Sanitize filename, keep extension
    original = f.filename
    ext = Path(original).suffix.lower()
    if ext not in (".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"):
        return jsonify({"error": f"Desteklenmeyen format: {ext}. MP4 kullan."}), 400

    fname = f"{uuid.uuid4().hex[:8]}{ext}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOAD_DIR / fname
    f.save(str(dest))
    return jsonify({"path": str(dest), "name": original})


def run_job(job_id, url, api_key, clip_count, local_file=None, whisper_model="base", language=None):
    def callback(job_id, status, **kwargs):
        jobs[job_id]["status"] = status
        jobs[job_id].update(kwargs)

    result = process_video(url, api_key, clip_count, callback=callback, job_id=job_id,
                           local_file=local_file, whisper_model=whisper_model, language=language)
    jobs[job_id]["result"] = result
    jobs[job_id]["status"] = result.get("status", "done")
    persist_job(job_id)


@app.route("/api/process", methods=["POST"])
@rate_limit
def start_process():
    data = request.json
    url = data.get("url", "").strip()
    clip_count = data.get("clip_count", 6)
    local_file = data.get("local_file", "").strip()
    whisper_model = data.get("whisper_model", "base")
    language = data.get("language", "").strip() or None

    # API key comes from server config only — never from client
    api_key = load_api_key()
    if not api_key:
        return jsonify({"error": "No API key configured. Add one in Settings."}), 400
    if not url and not local_file:
        return jsonify({"error": "URL or file is required"}), 400

    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "starting", "progress": 0}

    thread = threading.Thread(target=run_job, args=(job_id, url, api_key, clip_count, local_file, whisper_model, language))
    thread.daemon = True
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/api/status/<job_id>")
def get_status(job_id):
    if not load_persisted(job_id):
        return jsonify({"error": "Job not found"}), 404
    return jsonify(jobs[job_id])


@app.route("/api/jobs")
def list_jobs():
    return jsonify(jobs)


@app.route("/api/clips/<job_id>")
def list_clips(job_id):
    job_dir = OUTPUT_DIR / job_id
    if not job_dir.exists():
        return jsonify({"error": "Job not found"}), 404
    load_persisted(job_id)
    result = jobs.get(job_id, {}).get("result", {})
    return jsonify(result)


@app.route("/api/download/<job_id>/<filename>")
def download_clip(job_id, filename):
    job_dir = OUTPUT_DIR / job_id
    file_path = job_dir / filename
    if not file_path.exists():
        return jsonify({"error": "File not found"}), 404
    return send_file(str(file_path), as_attachment=True, download_name=filename)


@app.route("/api/preview/<job_id>/<filename>")
def preview_clip(job_id, filename):
    job_dir = OUTPUT_DIR / job_id
    file_path = job_dir / filename
    if not file_path.exists():
        return jsonify({"error": "File not found"}), 404
    return send_file(str(file_path), mimetype="video/mp4")


@app.route("/api/thumbnail/<job_id>/<filename>")
def get_thumbnail(job_id, filename):
    """Serve the thumbnail for a specific clip."""
    job_dir = OUTPUT_DIR / job_id
    # filename is like "01_Title.mp4", thumbnail is "01_Title.jpg"
    thumb_name = Path(filename).with_suffix(".jpg")
    file_path = job_dir / thumb_name
    if not file_path.exists():
        return jsonify({"error": "Thumbnail not found"}), 404
    return send_file(str(file_path), mimetype="image/jpeg")


@app.route("/api/clip_data/<job_id>/<filename>")
def get_clip_data(job_id, filename):
    """Get clip ASS content and source video path."""
    job_dir = OUTPUT_DIR / job_id
    if not job_dir.exists():
        return jsonify({"error": "Job not found"}), 404
    
    # Source video (may be gone after cleanup; editing works off the clip file)
    source = list(job_dir.glob("source.*"))
    
    ass_path = job_dir / (filename + ".ass")
    ass_content = ""
    if ass_path.exists():
        with open(ass_path, "r", encoding="utf-8") as f:
            ass_content = f.read()

    # Plain caption text (tags stripped) for the editor textarea
    plain_text = ""
    for line in ass_content.splitlines():
        if line.startswith("Dialogue:"):
            txt = line.split(",", 9)[-1] if "," in line else ""
            import re as _re
            txt = _re.sub(r"\{[^}]*\}", "", txt)
            plain_text += txt.strip() + " "
    plain_text = plain_text.strip()

    # Editable subtitle cues: prefer the sidecar the user last edited (clean
    # re-edit); otherwise parse them back from the current clip's ASS.
    cues = None
    cues_path = job_dir / (filename + ".cues.json")
    if cues_path.exists():
        try:
            cues = json.loads(cues_path.read_text(encoding="utf-8"))
        except Exception:
            cues = None
    if not isinstance(cues, list) or not cues:
        import re as _re2
        cues = []
        for line in ass_content.splitlines():
            if line.startswith("Dialogue:"):
                parts = line.split(",", 9)
                if len(parts) < 10:
                    continue
                try:
                    st = _ass_sec(parts[1])
                    en = _ass_sec(parts[2])
                except Exception:
                    continue
                txt = _re2.sub(r"\{[^}]*\}", "", parts[9]).strip()
                if txt:
                    cues.append({"start": round(st, 3), "end": round(en, 3), "text": txt})

    # Current style parsed from the ASS Style line (so editor starts with real values)
    current_style = {}
    import re as _re
    sm = _re.search(r"^Style:\s*(.*)$", ass_content, _re.MULTILINE)
    if sm:
        def ass_to_hex(a):
            a = a[2:].rstrip("&")
            if len(a) == 8:
                a = a[2:]  # strip alpha
            b, g, r = a[0:2], a[2:4], a[4:6]
            return "#" + r + g + b
        parts = [p.strip() for p in sm.group(1).split(",")]
        # V4+ Style field order: Name,Fontname,Fontsize,Primary,Secondary,Outline,Back,
        # Bold,Italic,Underline,Strike,ScaleX,ScaleY,Spacing,Angle,BorderStyle,
        # Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
        try:
            current_style = {
                "fontsize": int(parts[2]),
                "primary": ass_to_hex(parts[3]),
                "secondary": ass_to_hex(parts[4]),
                "outline": ass_to_hex(parts[5]),
                "back": ass_to_hex(parts[6]),
                "bold": parts[7] == "1",
                "outline_w": int(parts[16]),
                "shadow": int(parts[17]),
                "marginv": int(parts[21]),
            }
        except (IndexError, ValueError):
            current_style = {}

    # Get clip metadata from jobs dict (load from disk if restarted)
    load_persisted(job_id)
    job_data = jobs.get(job_id, {}).get("result", {})
    clip_meta = next((c for c in job_data.get("clips", []) if c["filename"] == filename), {})

    return jsonify({
        "source": str(source[0]) if source else "",
        "filename": filename,
        "ass_content": ass_content,
        "plain_text": plain_text,
        "cues": cues,
        "current_style": current_style,
        "effect": clip_meta.get("effect", "none"),
        "start": clip_meta.get("start", 0),
        "end": clip_meta.get("end", 0),
        "hook": clip_meta.get("hook", "")
    })

@app.route("/api/update_clip/<job_id>/<filename>", methods=["POST"])
def update_clip(job_id, filename):
    """Update clip with new timings, cut-out regions, style and subtitles."""
    data = request.json
    job_dir = OUTPUT_DIR / job_id
    if not job_dir.exists():
        return jsonify({"error": "Job not found"}), 404

    load_persisted(job_id)

    # Editing operates on the CURRENT clip file (self-contained, no source needed)
    clip_path = job_dir / filename
    if not clip_path.exists():
        return jsonify({"error": "Clip video not found"}), 404

    dur = float(data.get("dur") or 0) or (
        float(data.get("end", 0)) - float(data.get("start", 0)))
    start, end = 0.0, dur
    ass_content = data.get("ass_content", "")

    # Build ASS from the user's cue list (exact times + text) when provided
    cues = data.get("cues")
    style = data.get("style")
    if cues is not None and style is not None:
        try:
            from pipeline import build_ass_from_cues
            ass_content = build_ass_from_cues(cues, style)
        except Exception as e:
            return jsonify({"error": "Subtitle build failed: " + str(e)}), 500
    else:
        # Legacy: rebuild from a single caption + transcript word timings
        text = data.get("text")
        if text is not None and style is not None:
            try:
                ass_content = rebuild_clip_ass(job_dir, start, end, text, style)
            except Exception as e:
                return jsonify({"error": "Subtitle rebuild failed: " + str(e)}), 500
    effect = data.get("effect", "none")
    cuts = data.get("cuts") or []

    try:
        recut_clip(str(clip_path), job_dir, filename, start, end, ass_content,
                   effect=effect, cuts=cuts)
        # Persist the user's last-edited cues in a sidecar so re-editing is clean
        # (clip-relative). After a cut the clip changes, so fall back to ASS parsing.
        cues_path = job_dir / (filename + ".cues.json")
        if cuts:
            cues_path.unlink(missing_ok=True)
        elif isinstance(cues, list):
            cues_path.write_text(json.dumps(cues, ensure_ascii=False), encoding="utf-8")
        # Keep effect in sync for re-editing
        load_persisted(job_id)
        for c in jobs.get(job_id, {}).get("result", {}).get("clips", []):
            if c.get("filename") == filename:
                c["effect"] = effect
                break
        persist_job(job_id)
        return jsonify({"ok": True, "message": "Clip updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/settings", methods=["POST"])
@rate_limit
def save_settings():
    data = request.json
    settings_path = CONFIG_DIR / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing settings
    existing = {}
    if settings_path.exists():
        with open(settings_path) as f:
            existing = json.load(f)
    
    # If api_key field is empty, keep the existing one
    if not data.get("api_key", "").strip():
        data["api_key"] = existing.get("api_key", "")
    else:
        data["api_key"] = data["api_key"].strip()
    
    with open(settings_path, "w") as f:
        json.dump(data, f)
    return jsonify({"ok": True})


@app.route("/api/settings")
@rate_limit
def get_settings():
    settings_path = CONFIG_DIR / "settings.json"
    if settings_path.exists():
        with open(settings_path) as f:
            data = json.load(f)
        # Mask the API key — never return it in full
        if "api_key" in data and data["api_key"]:
            key = data["api_key"]
            data["api_key_masked"] = key[:6] + "..." + key[-4:] if len(key) > 10 else "***"
            data["has_api_key"] = True
        else:
            data["api_key_masked"] = ""
            data["has_api_key"] = False
        data.pop("api_key", None)
        return jsonify(data)
    return jsonify({"has_api_key": False})


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


FRONTEND_DIR = Path(__file__).parent.parent


@app.route("/")
def index():
    return send_file(str(FRONTEND_DIR / "index.html"))


@app.route("/styles.css")
def styles():
    return send_file(str(FRONTEND_DIR / "styles.css"))


@app.route("/app.js")
def app_js():
    return send_file(str(FRONTEND_DIR / "app.js"))


@app.route("/api/cleanup", methods=["POST"])
def manual_cleanup():
    cleanup()
    return jsonify({"ok": True})


if __name__ == "__main__":
    print("ClipPulse starting on http://localhost:5555")
    app.run(host="0.0.0.0", port=5555, debug=False)
