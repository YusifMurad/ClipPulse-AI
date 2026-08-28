import os
import re
import sys
import json
import time
import shutil
import subprocess
import tempfile
import threading
import traceback
from pathlib import Path

import yt_dlp
import google.genai as genai
from faster_whisper import WhisperModel

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ffmpeg / ffprobe binaries (override with FFMPEG_PATH / FFPROBE_PATH if not on PATH)
FFMPEG = os.environ.get("FFMPEG_PATH") or "ffmpeg"
FFPROBE = os.environ.get("FFPROBE_PATH") or "ffprobe"


# ---------------------------------------------------------------------------
# Performance / acceleration helpers (auto GPU where available, else tuned CPU)
# ---------------------------------------------------------------------------
def _cpu_count():
    try:
        return max(1, os.cpu_count() or 1)
    except Exception:
        return 1


_ENC_TYPE = None  # "nvenc" | "cpu"


def _detect_encoder_type():
    """Pick the best video encoder for this machine (cached)."""
    global _ENC_TYPE
    if _ENC_TYPE is not None:
        return _ENC_TYPE
    try:
        has_nv = (os.path.exists("/dev/nvidia0")
                  or subprocess.run(["nvidia-smi"], capture_output=True,
                                    timeout=10).returncode == 0)
    except Exception:
        has_nv = False
    _ENC_TYPE = "nvenc" if has_nv else "cpu"
    return _ENC_TYPE


def _video_codec_args(threads):
    """Return ffmpeg -c:v ... args using the detected encoder."""
    if _detect_encoder_type() == "nvenc":
        return ["-c:v", "h264_nvenc", "-preset", "p4", "-rc", "vbr",
                "-b:v", "0", "-cq", "23"]
    return ["-c:v", "libx264", "-preset", "veryfast",
            "-threads", str(max(1, threads)), "-crf", "23"]


def _cuda_available():
    try:
        import torch
        return bool(torch.cuda.is_available())
    except Exception:
        return False


def _ffmpeg_encode(input_args, vf, output_path, threads=None, audio_args=None, audio_filter=None):
    """Encode a clip with the auto-selected encoder; fall back to CPU on failure."""
    threads = max(1, threads or _cpu_count())
    if audio_args is None:
        audio_args = ["-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
    out_tmp = str(output_path) + ".tmp.mp4"
    base = [FFMPEG, "-y"] + list(input_args)
    if vf:
        base += ["-vf", vf]
    base += _video_codec_args(threads) + audio_args
    if audio_filter:
        base += ["-af", audio_filter]
    base += ["-movflags", "+faststart", out_tmp]
    try:
        subprocess.run(base, capture_output=True, check=True)
    except subprocess.CalledProcessError:
        if _detect_encoder_type() != "cpu":
            cpu_args = ["-c:v", "libx264", "-preset", "veryfast",
                        "-threads", str(_cpu_count()), "-crf", "23"]
            fallback = [FFMPEG, "-y"] + list(input_args) + (["-vf", vf] if vf else []) + cpu_args + audio_args
            if audio_filter:
                fallback += ["-af", audio_filter]
            fallback += ["-movflags", "+faststart", out_tmp]
            subprocess.run(fallback, capture_output=True, check=True)
        else:
            raise
    os.replace(out_tmp, str(output_path))


def _find_deno():
    """Locate the deno binary (optional, used by yt-dlp for YouTube)."""
    env = os.environ.get("DENO_BIN")
    if env and os.path.exists(env):
        return env
    return shutil.which("deno")


def download_video(url, job_dir, progress_cb=None, status_cb=None):
    """Download video from YouTube using yt-dlp CLI with retries.

    Resolution is capped at 1080p so downloads stay reasonably fast (selecting
    `bestvideo+bestaudio/best` can pull a multi-GB 4K file that looks "stuck").
    If `progress_cb(percent)` is given, download progress is streamed live;
    `status_cb(stage, **kw)` reports stage changes (e.g. "merging") so the UI
    never looks frozen.
    """
    yt_dl = [sys.executable, "-m", "yt_dlp"]
    deno = _find_deno()
    base_fmt = "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"

    # Strategies that work without a JS runtime. Prefer a single-file (progressive)
    # mp4 to skip the ffmpeg merge entirely; fall back to 1080p DASH + merge.
    strategies = [
        ["--impersonate", "chrome", "-f", "best[height<=1080][ext=mp4]/best[height<=1080]"],
        ["-f", "best[height<=1080][ext=mp4]/best[height<=1080]"],
        ["--impersonate", "chrome", "-f", base_fmt],
        ["-f", base_fmt],
    ]
    # If deno is available, prepend strategies that use it (better YouTube support)
    if deno:
        deno_rt = f"deno:{deno}"
        strategies = [
            ["--js-runtimes", deno_rt, "--impersonate", "chrome", "--remote-components", "ejs:github",
             "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best[height<=1080]"],
            ["--js-runtimes", deno_rt, "--impersonate", "chrome", "--extractor-args", "youtube:player_client=ios,web",
             "-f", base_fmt],
        ] + strategies

    # Use aria2c for max download throughput when available (falls back to the
    # built-in downloader automatically if aria2c is missing or fails).
    if shutil.which("aria2c"):
        aria = ["--external-downloader", "aria2c",
                "--external-downloader-args", "-x 16 -s 16 -k 1M"]
        strategies = [s + aria for s in strategies] + strategies

    output_template = str(job_dir / "source.%(ext)s")
    pct_re = re.compile(r"\[download\]\s*([\d.]+)%")
    last_err = None
    for strat in strategies:
        for attempt in range(2):
            cmd = [
                *yt_dl,
                *strat,
                "--merge-output-format", "mp4",
                "--no-warnings",
                "--no-check-certificates",
                "--newline",
                "--progress",
                "--concurrent-fragments", "16",
                "--socket-timeout", "30",
                "--retries", "2",
                "-o", output_template,
                "--print", "after_move:filepath",
                "--print", "title",
                url,
            ]
            try:
                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, bufsize=1,
                )
            except Exception as e:
                last_err = str(e)
                time.sleep(3)
                continue
            # Stream stderr for live download %; scan stdout (which yt-dlp uses for
            # the "[Merger] Merging formats" message) in a background thread so we
            # can surface a "merging" stage while the post-download merge runs.
            last_line = ""
            merging_emitted = [False]
            stdout_buf = []

            def _scan_stdout():
                try:
                    for ln in proc.stdout:
                        stdout_buf.append(ln)
                        if status_cb and not merging_emitted[0] and ("Merg" in ln or "erge" in ln):
                            merging_emitted[0] = True
                            try:
                                status_cb("merging", progress=99)
                            except Exception:
                                pass
                except Exception:
                    pass

            _t = threading.Thread(target=_scan_stdout, daemon=True)
            _t.start()
            while True:
                line = proc.stderr.readline()
                if not line:
                    break
                last_line = line
                m = pct_re.search(line)
                if m and progress_cb:
                    try:
                        progress_cb(min(99.0, float(m.group(1))))
                    except (ValueError, TypeError):
                        pass
                if status_cb and not merging_emitted[0] and ("Merger" in line or "Merging formats" in line):
                    merging_emitted[0] = True
                    try:
                        status_cb("merging", progress=99)
                    except Exception:
                        pass
            _t.join()
            try:
                proc.wait(timeout=600)
            except subprocess.TimeoutExpired:
                proc.kill()
                last_err = "Download timed out"
                time.sleep(3)
                continue
            if proc.returncode != 0:
                last_err = last_line.strip()
                time.sleep(3)
                continue
            out = "".join(stdout_buf).strip()
            lines = [l for l in out.split("\n") if l.strip()]
            filename = lines[-2].strip() if len(lines) >= 2 else None
            title = lines[-1].strip() if len(lines) >= 2 else "video"
            if not filename or not os.path.exists(filename):
                candidates = list(job_dir.glob("source.*"))
                if candidates:
                    filename = str(candidates[0])
                else:
                    last_err = "Downloaded file not found"
                    time.sleep(3)
                    continue
            return filename, title

    raise RuntimeError(f"yt-dlp failed: {last_err}")


def transcribe(video_path, model_size="base", language=None):
    """Transcribe video with faster-whisper. If language given, skips detection (faster)."""
    n = _cpu_count()
    device = "cuda" if _cuda_available() else "cpu"
    compute = "float16" if device == "cuda" else "int8"
    model = WhisperModel(model_size, device=device, compute_type=compute,
                         cpu_threads=n, num_workers=1)
    transcribe_kwargs = {"beam_size": 5, "word_timestamps": True}
    if language:
        transcribe_kwargs["language"] = language
    segments, info = model.transcribe(video_path, **transcribe_kwargs)
    all_segments = []
    for seg in segments:
        all_segments.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip(),
            "words": [
                {"word": w.word, "start": w.start, "end": w.end}
                for w in (seg.words or [])
            ],
        })
    return all_segments, info.language


def build_transcript_text(segments):
    lines = []
    for s in segments:
        lines.append(f"[{s['start']:.1f}-{s['end']:.1f}] {s['text']}")
    return "\n".join(lines)


LANG_NAMES = {
    "en": "English", "tr": "Turkish", "de": "German", "fr": "French",
    "es": "Spanish", "it": "Italian", "pt": "Portuguese", "ru": "Russian",
    "ar": "Arabic", "ja": "Japanese", "ko": "Korean", "zh": "Chinese",
    "hi": "Hindi", "nl": "Dutch", "pl": "Polish", "sv": "Swedish",
    "uk": "Ukrainian", "fa": "Persian", "id": "Indonesian", "vi": "Vietnamese",
    "th": "Thai", "cs": "Czech", "el": "Greek",
}


def find_moments_gemini(transcript_text, api_key, title="", num_clips=8, language=None, on_retry=None):
    """Ask Gemini to find the best viral moments using professional clip editing algorithm."""
    client = genai.Client(api_key=api_key)

    lang_name = LANG_NAMES.get((language or "").lower(), language or "English")
    lang_note = (
        f"\nÇIKTI DİLİ: {lang_name}\n"
        f"- \"hook_title\" ve \"reason\" alanlarını {lang_name} dilinde yaz.\n"
        f"- \"hook_sentence\" ve \"closing_sentence\" transkriptten birebir alıntıdır; "
        f"orijinal dillerinde (çeviri yapmadan) yaz."
    )

    prompt = f"""Sen profesyonel bir video klip editörü AI'sın. Görevin uzun videoları, izleyiciyi en çok etkileyen viral kısa kliplere dönüştürmek.

Video başlığı: {title}

Transkript (timestamp formatında [start-end]):
{transcript_text}
{lang_note}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ALGORİTMA — Aşağıdaki adımları eksiksiz uygula:
━━━━━━━━━━━━━━━━━━━━━━━━━━

BÖLÜM 1 — KONUŞMA ANALİZİ
Her cümle için hesapla:
• HOOK SKORU: Soru ile başlıyor mu? Karşıt sav içeriyor mu? Rakam/istatistik var mı? Kişisel itiraf/dramatik an var mı?
• TEMPO & ENERJİ: Dakikada kelime sayısı 120+ mı? Ses yükselip alçalıyor mu? Duraklama (≥0.8sn sessizlik) var mı?
• KAPANIŞ NOKTASI: Doğal sonuç cümlesi, gülüş/alkış, güçlü son cümle var mı?

BÖLÜM 2 — ANLAM BÜTÜNLÜĞÜ
Her klip adayı için kontrol et:
✅ Bağlam bilmeden biri konuyu anlayabilir mi?
✅ Bir fikri başlatıp bitiriyor mu?
✅ İzleyici tatmin hissediyor mu?
Hayır ise → başlangıç 5-10sn geri veya bitiş 5-10sn ileri al.

BÖLÜM 3 — VİRAL POTANSİYEL SKORU (0-100)
• Hook gücü → max 30 puan
• Duygusal yoğunluk → max 25 puan (komik/şok edici/ilham verici/tartışmalı)
• Uzunluk uyumu → max 20 puan (15-60sn ideal, 60-90sn kabul edilebilir)
• Anlaşılırlık → max 15 puan (bağlamsız izlenebilir mi?)
• Kapanış gücü → max 10 puan (güçlü son cümle var mı?)
Skoru 70'in üzerindeki klipleri önceliklendir.

BÖLÜM 4 — ZOOM İN EFEKTİ (her klibin başına)
• Süre: 0.6 saniye
• Başlangıç scale: 1.12 → Bitiş: 1.00
• Easing: ease-out

BÖLÜM 5 — ÇIKTI FORMATI
{num_clips} klip döndür. Her klibin start/end zamanını transcript'teki gerçek timestamp'lerden al.

Return ONLY a JSON array (no markdown, no explanation) with objects like:
[
  {{
    "clip_id": 1,
    "start": 272.0,
    "end": 318.0,
    "hook_sentence": "İlk cümle buraya",
    "closing_sentence": "Son cümle buraya",
    "viral_score": 84,
    "hook_title": "5 kelimelik başlık",
    "reason": "Bu klibi seçme gerekçen (1 cümle)",
    "zoom_in": {{
      "start": "0.0s",
      "end": "0.6s",
      "from_scale": 1.12,
      "to_scale": 1.00
    }}
  }}
]

Kurallar:
- Timestamp'ler transcript'teki gerçek zamanlardan olmalı
- Çeşitli anlar seç (hepsi aynı bölümde olmasın)
- Her klip bağımsız olarak anlamlı olmalı
- hook_title ve reason {lang_name} dilinde, hook_sentence/closing_sentence orijinal dilinde
- Sadece JSON array döndür, başka bir şey yazma"""

    response = None
    max_retries = 6
    backoff = 3.0
    last_err = None
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash", contents=prompt
            )
            break
        except Exception as e:  # noqa: BLE001
            last_err = e
            code = getattr(e, "code", None)
            status = str(getattr(e, "status", "") or "")
            msg = str(e)
            retryable = (
                code in (429, 500, 502, 503, 504)
                or "503" in msg
                or "UNAVAILABLE" in status
                or "RESOURCE_EXHAUSTED" in status
                or "429" in msg
                or "DeadlineExceeded" in status
            )
            if not retryable or attempt == max_retries - 1:
                raise
            wait = backoff * (2 ** attempt)
            if on_retry:
                try:
                    on_retry(attempt + 1, max_retries, wait, msg)
                except Exception:
                    pass
            time.sleep(wait)
    if response is None:
        raise RuntimeError(f"Gemini yanıt vermedi (deneme sayısı aşıldı): {last_err}")
    text = response.text.strip()
    # Strip markdown code fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    moments = json.loads(text)
    return moments


def create_srt(segments, start_offset, end_offset):
    """Create SRT subtitle content for a clipped segment."""
    srt_lines = []
    idx = 1
    for seg in segments:
        seg_start = seg["start"]
        seg_end = seg["end"]
        # Only include words within the clip window
        if seg_end < start_offset or seg_start > end_offset:
            continue
        clipped_start = max(0, seg_start - start_offset)
        clipped_end = min(end_offset - start_offset, seg_end - start_offset)
        if clipped_end <= clipped_start:
            continue
        srt_lines.append(str(idx))
        srt_lines.append(f"{fmt_srt_time(clipped_start)} --> {fmt_srt_time(clipped_end)}")
        srt_lines.append(seg["text"])
        srt_lines.append("")
        idx += 1
    return "\n".join(srt_lines)


def fmt_ass_time(seconds):
    """Format seconds to ASS time (h:mm:ss.cc)."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds - int(seconds)) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def create_ass(segments, start_offset, end_offset, aspect="9:16"):
    """Create animated ASS subtitles with word-by-word highlight (OpusClip-style).

    Each word is rendered in white; the currently spoken word animates to
    yellow/green via a \\t transform over its own duration, giving a
    karaoke-style pop effect.
    """
    pr = _aspect_res(aspect)
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {pr[0]}
PlayResY: {pr[1]}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Word, Arial, 74, &H00FFFFFF, &H00FFFFFF, &H00000000, &H00000000, 1, 0, 0, 0, 100, 100, 0, 0, 1, 14, 8, 2, 60, 60, 100, 1
WrapStyle: 1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events = []
    for seg in segments:
        seg_start = seg["start"]
        seg_end = seg["end"]
        if seg_end < start_offset or seg_start > end_offset:
            continue
        words = seg.get("words") or []
        if not words:
            clipped_start = max(0, seg_start - start_offset)
            clipped_end = min(end_offset - start_offset, seg_end - start_offset)
            if clipped_end <= clipped_start:
                continue
            text = f"{{\\be2}}{{\\c&H00FFFF&\\b1}}{seg['text']}{{\\b0}}"
            events.append(f"Dialogue: 0,{fmt_ass_time(clipped_start)},{fmt_ass_time(clipped_end)},Word,,0,0,0,,{text}")
            continue

        line_text_words = []
        for w in words:
            w_start = max(0, w["start"] - start_offset)
            w_end = min(end_offset - start_offset, w["end"] - start_offset)
            if w_end <= w_start:
                continue
            word_text = (
                f"{{\\be2}}{{\\1c&HFFFFFF&\\t({w_start:.2f},{w_end:.2f},\\1c&H00FFFF&)}}{w['word'].strip()}"
            )
            line_text_words.append(word_text)

        if not line_text_words:
            continue

        # Join all words in the segment into one dialogue line with wrapping
        text = " ".join(line_text_words)
        clipped_start = max(0, seg_start - start_offset)
        clipped_end = min(end_offset - start_offset, seg_end - start_offset)
        if clipped_end <= clipped_start:
            continue
            
        events.append(f"Dialogue: 0,{fmt_ass_time(clipped_start)},{fmt_ass_time(clipped_end)},Word,,0,0,0,,{text}")

    return header + "\n".join(events)


def hex_to_ass(hex_color):
    """Convert '#RRGGBB' to ASS colour format '&HBBGGRR&'."""
    h = (hex_color or "#ffffff").lstrip("#")
    if len(h) >= 6:
        r, g, b = h[0:2], h[2:4], h[4:6]
    else:
        r, g, b = "ff", "ff", "ff"
    return f"&H{b}{g}{r}&"


def lerp_color(c1, c2, t):
    """Interpolate between two '#RRGGBB' colours. t in [0,1]."""
    def p(c):
        c = c.lstrip("#")
        return [int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)]
    a, b = p(c1), p(c2)
    return "#" + "".join(f"{int(a[i] + (b[i] - a[i]) * t):02X}" for i in range(3))


def _aspect_res(aspect):
    if aspect == "16:9":
        return (1920, 1080)
    if aspect == "1:1":
        return (1080, 1080)
    return (1080, 1920)


def build_ass_header(style, playres=(1080, 1920)):
    primary = hex_to_ass(style.get("primary", "#ffffff"))
    secondary = hex_to_ass(style.get("secondary", "#ffff00"))
    outline = hex_to_ass(style.get("outline", "#000000"))
    back = hex_to_ass(style.get("back", "#000000"))
    fontsize = int(style.get("fontsize", 74))
    bold = 1 if style.get("bold", True) else 0
    outline_w = int(style.get("outline_w", 14))
    shadow = int(style.get("shadow", 8))
    marginv = int(style.get("marginv", 100))
    fontname = style.get("fontname", "Arial")
    style_line = (
        f"Style: Word, {fontname}, {fontsize}, {primary}, {secondary}, {outline}, {back}, "
        f"{bold}, 0, 0, 0, 100, 100, 0, 0, 1, {outline_w}, {shadow}, 2, 60, 60, {marginv}, 1"
    )
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: {playres[0]}
PlayResY: {playres[1]}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{style_line}
WrapStyle: 1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def build_ass_with_style(words, start_offset, end_offset, new_text, style, aspect="9:16"):
    """Build animated ASS from new caption text + style, mapped onto word timings."""
    header = build_ass_header(style, playres=_aspect_res(aspect))
    nw = (new_text or "").split()
    if not nw:
        return header
    n = len(nw)

    if len(words) == n:
        ranges = [
            (max(0.0, w["start"] - start_offset), min(end_offset - start_offset, w["end"] - start_offset))
            for w in words
        ]
    else:
        total = max(0.1, end_offset - start_offset)
        dur = total / n
        ranges = [(i * dur, (i + 1) * dur) for i in range(n)]

    grad = style.get("gradient", False)
    grad_a = style.get("gradient_a", "#ec4899")
    grad_b = style.get("gradient_b", "#a855f7")
    primary = hex_to_ass(style.get("primary", "#ffffff"))
    active = hex_to_ass("#FFFFFF") if grad else hex_to_ass(style.get("secondary", "#ffff00"))

    events = []
    for i, nwi in enumerate(nw):
        ws, we = ranges[i]
        if we <= ws:
            continue
        idle = hex_to_ass(lerp_color(grad_a, grad_b, i / max(1, n - 1))) if grad else primary
        text = (
            f"{{\\be2}}{{\\1c{idle}\\t({ws:.2f},{we:.2f},\\1c{active})}}{nwi}"
        )
        events.append(
            f"Dialogue: 0,{fmt_ass_time(ws)},{fmt_ass_time(we)},Word,,0,0,0,,{text}"
        )
    return header + "\n".join(events)


def rebuild_clip_ass(job_dir, start, end, new_text, style, aspect="9:16"):
    """Regenerate a clip's ASS from stored transcript words + new text/style."""
    seg_path = job_dir / "segments.json"
    if not seg_path.exists():
        raise RuntimeError("Transcript not found for this job (re-process to enable text editing).")
    data = json.loads(seg_path.read_text(encoding="utf-8"))
    segments = data.get("segments", [])
    window_words = []
    for seg in segments:
        if seg["end"] < start or seg["start"] > end:
            continue
        for w in (seg.get("words") or []):
            ws = max(start, w["start"])
            we = min(end, w["end"])
            if we > ws:
                window_words.append({"word": w["word"], "start": ws, "end": we})
    if not window_words:
        # Fall back to segment-level text if no word timestamps
        for seg in segments:
            if seg["end"] < start or seg["start"] > end:
                continue
            window_words.append({"word": seg["text"], "start": max(start, seg["start"]), "end": min(end, seg["end"])})
    return build_ass_with_style(window_words, start, end, new_text, style, aspect=aspect)


def extract_cues(segments, start, end):
    """Build a list of editable subtitle cues (clip-relative seconds) from the transcript."""
    cues = []
    for seg in segments:
        if seg["end"] < start or seg["start"] > end:
            continue
        cs = max(0.0, seg["start"] - start)
        ce = min(end - start, seg["end"] - start)
        if ce > cs:
            cues.append({"start": round(cs, 3), "end": round(ce, 3),
                         "text": (seg.get("text") or "").strip()})

    # Ensure at least two cues so the editor always shows intervals
    if len(cues) == 1:
        c = cues[0]
        words = (c["text"] or "").split()
        if len(words) > 1:
            mid = int(len(words) / 2)
            mid_t = (c["start"] + c["end"]) / 2
            cues = [
                {"start": c["start"], "end": round(mid_t, 3), "text": " ".join(words[:mid])},
                {"start": round(mid_t, 3), "end": c["end"], "text": " ".join(words[mid:])},
            ]
        else:
            mid = (c["start"] + c["end"]) / 2
            cues = [
                {"start": c["start"], "end": round(mid, 3), "text": c["text"]},
                {"start": round(mid, 3), "end": c["end"], "text": c["text"]},
            ]
    elif len(cues) == 0:
        cues = [
            {"start": 0.0, "end": 1.0, "text": ""},
            {"start": 1.0, "end": 2.0, "text": ""},
        ]
    return cues


def build_ass_from_cues(cues, style, aspect="9:16"):
    """Build animated ASS strictly from the user's cue list (start/end/text).

    Each cue is split into words that animate idle -> active across the cue's
    own time window, so the timing the user sets is honoured exactly.
    """
    header = build_ass_header(style, playres=_aspect_res(aspect))
    grad = style.get("gradient", False)
    grad_a = style.get("gradient_a", "#ec4899")
    grad_b = style.get("gradient_b", "#a855f7")
    primary = hex_to_ass(style.get("primary", "#ffffff"))
    active = hex_to_ass("#FFFFFF") if grad else hex_to_ass(style.get("secondary", "#ffff00"))

    events = []
    for cue in cues:
        try:
            cs = float(cue.get("start", 0))
            ce = float(cue.get("end", cs + 1))
        except (TypeError, ValueError):
            continue
        text = (cue.get("text") or "").strip()
        if not text or ce <= cs:
            continue
        words = text.split()
        n = len(words)
        if n == 0:
            continue
        if n == 1:
            idle = hex_to_ass(lerp_color(grad_a, grad_b, 0)) if grad else primary
            line = f"{{\\1c{idle}\\t({cs:.2f},{ce:.2f},\\1c{active})}}{words[0]}"
            events.append(f"Dialogue: 0,{fmt_ass_time(cs)},{fmt_ass_time(ce)},Word,,0,0,0,,{line}")
            continue
        dur = (ce - cs) / n
        for i, w in enumerate(words):
            ws = cs + i * dur
            we = cs + (i + 1) * dur
            if we <= ws:
                continue
            idle = hex_to_ass(lerp_color(grad_a, grad_b, i / (n - 1))) if grad else primary
            line = f"{{\\1c{idle}\\t({ws:.2f},{we:.2f},\\1c{active})}}{w}"
            events.append(f"Dialogue: 0,{fmt_ass_time(ws)},{fmt_ass_time(we)},Word,,0,0,0,,{line}")
    return header + "\n".join(events)


def fmt_srt_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _probe_fps(video_path):
    try:
        out = subprocess.run(
            [FFPROBE, "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=r_frame_rate", "-of", "default=nw=1:nk=1", video_path],
            capture_output=True, text=True,
        )
        num, _, den = out.stdout.strip().partition("/")
        n = float(num or 30)
        d = float(den or 1)
        return max(10.0, min(120.0, n / d if d else 30.0))
    except Exception:
        return 30.0


def build_zoom_filter(effect, w, h, duration, fps, focus=(0.5, 0.5), strength=1.3, length_frac=1.0):
    """Return a ffmpeg zoompan filter for the given effect (or '' for none).

    focus: (fx, fy) normalized point (0..1) the zoom centers on.
    strength: max zoom factor (>=1).
    length_frac: fraction of the clip the zoom animation ramps over (then holds).
    """
    if effect in (None, "none", ""):
        return ""
    fx, fy = focus if isinstance(focus, (list, tuple)) and len(focus) == 2 else (0.5, 0.5)
    try:
        fx = max(0.0, min(1.0, float(fx)))
        fy = max(0.0, min(1.0, float(fy)))
    except Exception:
        fx, fy = 0.5, 0.5
    try:
        strength = max(1.0, float(strength))
    except Exception:
        strength = 1.3
    try:
        length_frac = max(0.05, min(1.0, float(length_frac)))
    except Exception:
        length_frac = 1.0
    fps = max(1.0, fps)
    span = max(1, int(length_frac * max(0.1, duration) * fps))
    p = f"min(in,{span})/{span}"
    if effect == "zoom-out":
        z = f"{strength:.4f} - ({strength:.4f} - 1.0)*({p})"
    elif effect == "pop":
        z = f"1.0 + ({strength:.4f} - 1.0)*sin(3.14159*{p})"
    else:  # zoom-in / ken-burns (continuous push centered on focus)
        z = f"1.0 + ({strength:.4f} - 1.0)*({p})"
    x = f"max(0, min(iw - iw/zoom, {fx:.4f}*iw - (iw/zoom)/2))"
    y = f"max(0, min(ih - ih/zoom, {fy:.4f}*ih - (ih/zoom)/2))"
    return (f"zoompan=z='{z}':d=1:s={w}x{h}:fps={fps:.0f}"
            f":x='{x}':y='{y}'")


def _ass_to_sec(t):
    h, m, rest = t.split(":")
    s, cs = rest.split(".")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(cs) / 100.0


def retime_ass(ass_text, cuts_relative):
    """Drop subtitle events inside removed segments and shift later ones back.

    cuts_relative: list of [ra, rb] in clip-relative seconds to remove.
    """
    def shift(t):
        shift_amt = 0.0
        for a, b in cuts_relative:
            if t >= b:
                shift_amt += (b - a)
            elif a <= t < b:
                return None
        return t - shift_amt

    out = []
    for line in ass_text.splitlines():
        if line.startswith("Dialogue:"):
            parts = line.split(",", 9)
            if len(parts) < 10:
                out.append(line)
                continue
            try:
                st = _ass_to_sec(parts[1])
                en = _ass_to_sec(parts[2])
            except Exception:
                out.append(line)
                continue
            ns = shift(st)
            ne = shift(en)
            if ns is None or ne is None:
                continue
            parts[1] = fmt_ass_time(ns)
            parts[2] = fmt_ass_time(ne)
            out.append(",".join(parts[:9]) + "," + parts[9])
            continue
        out.append(line)
    return "\n".join(out)


def cut_clip(video_path, start, end, srt_content, output_path, ass_content=None, effect="none",
              focus=(0.5, 0.5), strength=1.3, length_frac=1.0, fps=None, threads=None, aspect="9:16"):
    """Cut clip, crop to target aspect, burn (animated) subtitles, and create thumbnail."""
    duration = end - start
    TW, TH = _aspect_res(aspect)

    # Generate thumbnail (at 2s into the clip)
    thumb_path = output_path.with_suffix(".jpg")
    thumb_cmd = [
        FFMPEG, "-y",
        "-ss", str(start + min(duration, 2)),
        "-i", video_path,
        "-vframes", "1",
        "-q:v", "2",
        str(thumb_path)
    ]
    subprocess.run(thumb_cmd, capture_output=True)

    if ass_content:
        # Use ASS for animated word-by-word subtitles
        sub_path = str(output_path) + ".ass"
        with open(sub_path, "w", encoding="utf-8") as f:
            f.write(ass_content)
        # Force styles: WrapStyle=1 (smart wrapping), MarginV (bottom position)
        sub_filter = f"ass={sub_path.replace('\\', '/')}"
    elif srt_content and srt_content.strip():
        # Fallback to plain SRT
        sub_path = str(output_path) + ".srt"
        with open(sub_path, "w", encoding="utf-8") as f:
            f.write(srt_content)
        srt_escaped = srt_path_escape(sub_path)
        sub_filter = (
            f"subtitles='{srt_escaped}':force_style='"
            f"FontName=Arial,FontSize=22,PrimaryColour=&H00FFFFFF,"
            f"OutlineColour=&H00000000,Outline=2,Shadow=1,"
            f"Alignment=2,MarginV=80'"
        )
    else:
        sub_filter = ""

    # Optional video zoom effect (keeps frame count 1:1 to preserve audio sync)
    zoom = ""
    if effect not in (None, "none", ""):
        fps = fps or _probe_fps(video_path)
        zoom = build_zoom_filter(effect, TW, TH, duration, fps,
                                 focus=focus, strength=strength, length_frac=length_frac)
    crop_part = f"crop={TW}:{TH}"
    vf1 = f"scale={TW}:{TH}:force_original_aspect_ratio=increase,{crop_part}"
    if zoom:
        vf1 += "," + zoom

    # Gentle edge fades remove start/end clicks/pops caused by hard cuts
    audio_filter = None
    if duration > 0.3:
        fade_out_st = max(0.0, duration - 0.1)
        audio_filter = f"afade=t=in:d=0.05,afade=t=out:st={fade_out_st:.3f}:d=0.1"
    input_args = ["-ss", str(start), "-i", video_path, "-t", str(duration)]

    if sub_filter:
        # Two-pass render: first the video (with zoom) WITHOUT subtitles, then
        # burn the freshly timed subtitles onto the already-rendered clip. This
        # guarantees captions stay perfectly in sync with the final video instead
        # of drifting when the zoom filter alters the frame timeline.
        video_tmp = output_path.with_suffix(".vtmp.mp4")
        _ffmpeg_encode(input_args, vf1, video_tmp, threads=threads, audio_filter=audio_filter)
        _ffmpeg_encode(["-i", str(video_tmp)], sub_filter, output_path, threads=threads)
        try:
            video_tmp.unlink()
        except OSError:
            pass
    else:
        _ffmpeg_encode(input_args, vf1, output_path, threads=threads, audio_filter=audio_filter)


def srt_path_escape(p):
    return p.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def recut_clip(video_path, job_dir, clip_name, start, end, new_ass_content, effect="none", cuts=None,
               focus=(0.5, 0.5), strength=1.3, length_frac=1.0, fps=None, aspect="9:16"):
    """Re-cut an existing clip with new timings, optional cut-out regions and subtitles."""
    import shutil
    clip_output = job_dir / clip_name

    # Create new ASS file
    sub_path = str(clip_output) + ".ass"
    with open(sub_path, "w", encoding="utf-8") as f:
        f.write(new_ass_content)

    cuts = cuts or []
    # Normalise cuts to the clip window [start, end] (absolute seconds)
    rel_cuts = sorted(
        [(max(start, a), min(end, b)) for a, b in cuts if b > a and b > start and a < end]
    )
    rel_cuts = [(a, b) for a, b in rel_cuts if b - a > 0.05]

    if not rel_cuts:
        cut_clip(video_path, start, end, None, clip_output, ass_content=new_ass_content,
                 effect=effect, focus=focus, strength=strength, length_frac=length_frac, fps=fps)
        return True

    # Build the kept segments (everything outside the cut regions)
    pts = [start]
    for a, b in rel_cuts:
        pts.append(a)
        pts.append(b)
    pts.append(end)
    segs = [(pts[i], pts[i + 1]) for i in range(0, len(pts) - 1, 2)]
    segs = [(s, e) for s, e in segs if e - s > 0.05]
    if not segs:
        segs = [(start, end)]

    tmpdir = job_dir / (clip_name + "_parts")
    tmpdir.mkdir(exist_ok=True)
    try:
        part_files = []
        for idx, (s, e) in enumerate(segs):
            p = tmpdir / f"part{idx}.mp4"
            _ffmpeg_encode(["-ss", str(s), "-i", video_path, "-t", str(e - s)],
                           None, str(p))
            part_files.append(str(p))

        listfile = tmpdir / "list.txt"
        listfile.write_text("\n".join(f"file '{p}'" for p in part_files), encoding="utf-8")
        concat_path = tmpdir / "concat.mp4"
        # Re-encode (not copy) so timestamps/duration are clean after splicing
        _ffmpeg_encode(["-f", "concat", "-safe", "0", "-i", str(listfile)],
                       None, str(concat_path))

        # Re-time subtitles to the stitched timeline
        cuts_rel = [(a - start, b - start) for a, b in rel_cuts]
        new_ass_content = retime_ass(new_ass_content, cuts_rel)
        with open(sub_path, "w", encoding="utf-8") as f:
            f.write(new_ass_content)

        kept_duration = (end - start) - sum(b - a for a, b in rel_cuts)
        cut_clip(str(concat_path), 0, kept_duration, None, clip_output,
                 ass_content=new_ass_content, effect=effect, focus=focus,
                 strength=strength, length_frac=length_frac, fps=fps, aspect=aspect)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return True


def process_video(url, api_key, clip_count=6, callback=None, job_id=None, local_file=None, whisper_model="base", language=None, aspect="9:16"):
    """Full pipeline: download → transcribe → find moments → cut clips."""
    job_dir = OUTPUT_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    def emit(status, **kwargs):
        if callback:
            callback(job_id, status, **kwargs)

    try:
        if local_file:
            # Local file: copy into job dir
            import shutil
            src = Path(local_file)
            if not src.exists():
                raise RuntimeError(f"Dosya bulunamadı: {local_file}")
            video_path = str(job_dir / ("source" + src.suffix))
            shutil.copyfile(str(src), video_path)
            title = src.stem
            emit("downloaded", title=title, progress=15)
        else:
            emit("downloading", progress=0)
            video_path, title = download_video(
                url, job_dir,
                progress_cb=lambda p: emit("downloading", progress=p),
                status_cb=lambda s, **kw: emit(s, **kw),
            )
            emit("downloaded", title=title, progress=15)

        emit("transcribing", progress=20)
        segments, language = transcribe(video_path, model_size=whisper_model, language=language)
        # Persist transcript (incl. word timings) so captions can be re-edited later
        (job_dir / "segments.json").write_text(
            json.dumps({"segments": segments, "language": language}, ensure_ascii=False),
            encoding="utf-8",
        )
        emit("transcribed", segment_count=len(segments), progress=50)

        emit("analyzing", progress=55)
        transcript_text = build_transcript_text(segments)
        moments = find_moments_gemini(
            transcript_text, api_key, title, clip_count, language=language,
            on_retry=lambda a, m, w, err: emit(
                "retrying", progress=55, attempt=a, max_retries=m, wait=w,
                message="Gemini geçici olarak meşgul, yeniden deneniyor..."
            ),
        )
        emit("moments_found", count=len(moments), progress=70)

        total = len(moments)
        max_workers = max(1, min(_cpu_count(), total))
        per_threads = max(1, _cpu_count() // max_workers)

        def _do_cut(i, moment):
            hook = moment.get("hook_title", f"clip_{i+1}")
            safe_hook = re.sub(r'[^\w\s-]', '', hook)[:40].strip().replace(" ", "_")
            clip_name = f"{i+1:02d}_{safe_hook}.mp4"
            clip_output = job_dir / clip_name
            srt = create_srt(segments, moment["start"], moment["end"])
            ass = create_ass(segments, moment["start"], moment["end"])
            clip_effect = "zoom-in" if moment.get("zoom_in") else "none"
            cut_clip(video_path, moment["start"], moment["end"], srt, clip_output,
                     ass_content=ass, effect=clip_effect, threads=per_threads, aspect=aspect)
            return {
                "filename": clip_name,
                "hook": moment.get("hook_title", ""),
                "hook_sentence": moment.get("hook_sentence", ""),
                "closing_sentence": moment.get("closing_sentence", ""),
                "reason": moment.get("reason", ""),
                "viral_score": moment.get("viral_score", 0),
                "start": moment["start"],
                "end": moment["end"],
                "effect": clip_effect,
                "zoom_in": moment.get("zoom_in", {}),
                "aspect": aspect,
            }

        import concurrent.futures as _cf
        results = {}
        done = 0
        with _cf.ThreadPoolExecutor(max_workers=max_workers) as ex:
            futs = {ex.submit(_do_cut, i, m): i for i, m in enumerate(moments)}
            for f in _cf.as_completed(futs):
                res = f.result()
                results[futs[f]] = res
                done += 1
                emit("cutting_clip", clip_index=done, total=total,
                     progress=70 + int(25 * done / total))
        clips = [results[i] for i in range(total)]

        emit("done", clips=clips, progress=100)
        return {"status": "done", "title": title, "clips": clips, "job_dir": str(job_dir)}

    except Exception as e:
        tb = traceback.format_exc()
        print(f"[ClipPulse ERROR] {e}\n{tb}")
        emit("error", error=str(e))
        return {"status": "error", "error": str(e)}
