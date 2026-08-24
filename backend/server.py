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

from pipeline import process_video, OUTPUT_DIR, recut_clip

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

# --- Temizlik ---
def cleanup():
    print("Sunucu kapanıyor, output dizini temizleniyor...")
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
        OUTPUT_DIR.mkdir()

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
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


@app.route("/api/jobs")
def list_jobs():
    return jsonify(jobs)


@app.route("/api/clips/<job_id>")
def list_clips(job_id):
    job_dir = OUTPUT_DIR / job_id
    if not job_dir.exists():
        return jsonify({"error": "Job not found"}), 404
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
    
    # Find source video
    source = list(job_dir.glob("source.*"))
    if not source:
        return jsonify({"error": "Source video not found"}), 404
    
    ass_path = job_dir / (filename + ".ass")
    ass_content = ""
    if ass_path.exists():
        with open(ass_path, "r", encoding="utf-8") as f:
            ass_content = f.read()
            
    # Get clip metadata from jobs dict
    job_data = jobs.get(job_id, {}).get("result", {})
    clip_meta = next((c for c in job_data.get("clips", []) if c["filename"] == filename), {})
    
    return jsonify({
        "source": str(source[0]),
        "filename": filename,
        "ass_content": ass_content,
        "start": clip_meta.get("start", 0),
        "end": clip_meta.get("end", 0),
        "hook": clip_meta.get("hook", "")
    })

@app.route("/api/update_clip/<job_id>/<filename>", methods=["POST"])
def update_clip(job_id, filename):
    """Update clip with new timings and subtitles."""
    data = request.json
    job_dir = OUTPUT_DIR / job_id
    if not job_dir.exists():
        return jsonify({"error": "Job not found"}), 404
        
    source = list(job_dir.glob("source.*"))
    if not source:
        return jsonify({"error": "Source video not found"}), 404
        
    start = float(data.get("start", 0))
    end = float(data.get("end", 0))
    ass_content = data.get("ass_content", "")
    
    try:
        recut_clip(str(source[0]), job_dir, filename, start, end, ass_content)
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
