"""
ClipForge API Satış Sistemi
- API key ile kimlik doğrulama
- Ücretsiz/Sınırsız plan
- Kullanım takibi
- Rate limiting
"""

import os
import json
import uuid
import time
import hashlib
from pathlib import Path
from functools import wraps

API_DB = Path(__file__).parent / "config" / "api_keys.json"
USAGE_DB = Path(__file__).parent / "config" / "api_usage.json"


def load_db(path):
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def save_db(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def generate_api_key():
    return "cf_" + hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:32]


def register_api_routes(app, run_job_func, jobs_dict):
    """Tüm API satış endpoint'lerini Flask app'e ekle."""

    def require_api_key(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            key = request.headers.get("X-API-Key") or request.args.get("api_key")
            if not key:
                return jsonify({"error": "X-API-Key header gerekli"}), 401
            keys = load_db(API_DB)
            if key not in keys:
                return jsonify({"error": "Geçersiz API key"}), 401
            # Usage tracking
            usage = load_db(USAGE_DB)
            user_usage = usage.get(key, {"count": 0, "last_reset": 0})
            plan = keys[key].get("plan", "free")
            # Free plan: 5 clips/month
            if plan == "free":
                now = time.time()
                if now - user_usage.get("last_reset", 0) > 30 * 86400:
                    user_usage = {"count": 0, "last_reset": now}
                if user_usage["count"] >= 5:
                    return jsonify({
                        "error": "Ücretsiz plan limiti aşıldı (ayda 5 clip). Pro plana yükselt.",
                        "upgrade": "https://yourdomain.com/pricing"
                    }), 429
                user_usage["count"] += 1
                usage[key] = user_usage
                save_db(USAGE_DB, usage)
            return f(*args, **kwargs)
        return decorated

    # --- PUBLIC API ENDPOINTS ---

    @app.route("/api/v1/generate", methods=["POST"])
    @require_api_key
    def api_generate_clips():
        """
        POST /api/v1/generate
        Body: { "url": "youtube url", "clip_count": 6 }
        Header: X-API-Key: cf_xxxxx
        """
        data = request.json or {}
        url = data.get("url", "").strip()
        clip_count = min(int(data.get("clip_count", 6)), 10)

        if not url:
            return jsonify({"error": "url gerekli"}), 400

        # API key'den Gemini key al
        keys = load_db(API_DB)
        api_key = request.headers.get("X-API-Key")
        gemini_key = keys[api_key].get("gemini_key", "")

        if not gemini_key:
            return jsonify({"error": "Bu API key için Gemini key ayarlanmamış"}), 400

        job_id = str(uuid.uuid4())[:8]
        jobs_dict[job_id] = {"status": "starting", "progress": 0}

        thread = threading.Thread(
            target=run_job_func,
            args=(job_id, url, gemini_key, clip_count)
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            "job_id": job_id,
            "status_url": f"/api/v1/status/{job_id}",
            "clips_url": f"/api/v1/clips/{job_id}"
        })

    @app.route("/api/v1/status/<job_id>")
    @require_api_key
    def api_status(job_id):
        """GET /api/v1/status/{job_id}"""
        job = jobs_dict.get(job_id)
        if not job:
            return jsonify({"error": "Job bulunamadı"}), 404
        return jsonify({
            "status": job.get("status"),
            "progress": job.get("progress", 0)
        })

    @app.route("/api/v1/clips/<job_id>")
    @require_api_key
    def api_clips(job_id):
        """GET /api/v1/clips/{job_id} - Klipleri ve download linklerini döndür"""
        job = jobs_dict.get(job_id)
        if not job or job.get("status") != "done":
            return jsonify({"error": "Klipler henüz hazır değil"}), 400
        result = job.get("result", {})
        clips = []
        for c in result.get("clips", []):
            clips.append({
                "filename": c["filename"],
                "hook": c.get("hook", ""),
                "viral_score": c.get("viral_score", 0),
                "start": c.get("start", 0),
                "end": c.get("end", 0),
                "download_url": f"/api/v1/download/{job_id}/{c['filename']}"
            })
        return jsonify({"title": result.get("title"), "clips": clips})

    @app.route("/api/v1/download/<job_id>/<filename>")
    @require_api_key
    def api_download(job_id, filename):
        """GET /api/v1/download/{job_id}/{filename}"""
        from pipeline import OUTPUT_DIR
        file_path = OUTPUT_DIR / job_id / filename
        if not file_path.exists():
            return jsonify({"error": "Dosya bulunamadı"}), 404
        return send_file(str(file_path), as_attachment=True, download_name=filename)

    # --- API KEY YÖNETİMİ ---

    @app.route("/api/v1/keys/create", methods=["POST"])
    def api_create_key():
        """
        Demo amaçlı: Ücretsiz API key oluştur.
        Gerçek hayatta: Ödeme sistemi buraya bağlanır.
        """
        data = request.json or {}
        email = data.get("email", "demo@user.com")
        gemini_key = data.get("gemini_key", "")
        plan = data.get("plan", "free")

        new_key = generate_api_key()
        keys = load_db(API_DB)
        keys[new_key] = {
            "email": email,
            "plan": plan,
            "gemini_key": gemini_key,
            "created": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        save_db(API_DB, keys)

        return jsonify({
            "api_key": new_key,
            "plan": plan,
            "docs": "POST /api/v1/generate với header X-API-Key",
            "limits": {
                "free": "5 clip/ay",
                "pro": "sınırsız"
            }.get(plan, "sınırsız")
        })

    @app.route("/api/v1/keys/<key>/usage")
    def api_key_usage(key):
        """API key kullanım bilgisi"""
        keys = load_db(API_DB)
        if key not in keys:
            return jsonify({"error": "Geçersiz key"}), 404
        usage = load_db(API_DB)
        user_usage = usage.get(key, {"count": 0})
        return jsonify({
            "plan": keys[key]["plan"],
            "used": user_usage.get("count", 0),
            "limit": 999999 if keys[key]["plan"] == "pro" else 5
        })
