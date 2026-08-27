import os
import re
import json
import time
import subprocess
import tempfile
import traceback
from pathlib import Path

import yt_dlp
import google.genai as genai
from faster_whisper import WhisperModel

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def download_video(url, job_dir):
    """Download video from YouTube using yt-dlp CLI with retries."""
    yt_dlp_bin = str(Path(__file__).parent / "venv" / "bin" / "yt-dlp")
    output_template = str(job_dir / "source.%(ext)s")

    # Different strategies to try in order
    strategies = [
        ["--js-runtimes", "deno:/home/yusif/.deno/bin/deno", "--impersonate", "chrome", "--remote-components", "ejs:github", "-f", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best"],
        ["--js-runtimes", "deno:/home/yusif/.deno/bin/deno", "--impersonate", "chrome", "--extractor-args", "youtube:player_client=ios,web", "-f", "bestvideo[height<=720]+bestaudio/best"],
        ["--impersonate", "chrome", "-f", "bestvideo+bestaudio/best"],
        ["-f", "bestvideo+bestaudio/best"],
    ]

    last_err = None
    for strat in strategies:
        for attempt in range(2):
            cmd = [
                yt_dlp_bin,
                *strat,
                "--merge-output-format", "mp4",
                "--no-warnings",
                "--no-check-certificates",
                "--concurrent-fragments", "4",
                "--socket-timeout", "30",
                "--retries", "2",
                "-o", output_template,
                "--print", "after_move:filepath",
                "--print", "title",
                url,
            ]
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=600,
                env={**os.environ, "PATH": f"/home/yusif/.deno/bin:/usr/local/bin:/usr/bin:/bin:{os.environ.get('PATH', '')}"}
            )
            if proc.returncode == 0:
                lines = proc.stdout.strip().split("\n")
                filename = lines[-2].strip() if len(lines) >= 2 else None
                title = lines[-1].strip() if len(lines) >= 2 else "video"
                if not filename or not os.path.exists(filename):
                    candidates = list(job_dir.glob("source.*"))
                    if candidates:
                        filename = str(candidates[0])
                    else:
                        last_err = "Downloaded file not found"
                        continue
                return filename, title
            else:
                last_err = proc.stderr.strip()
            time.sleep(3)

    raise RuntimeError(f"yt-dlp failed: {last_err}")


def transcribe(video_path, model_size="base", language=None):
    """Transcribe video with faster-whisper. If language given, skips detection (faster)."""
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
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


def find_moments_gemini(transcript_text, api_key, title="", num_clips=8):
    """Ask Gemini to find the best viral moments using professional clip editing algorithm."""
    client = genai.Client(api_key=api_key)

    prompt = f"""Sen profesyonel bir video klip editörü AI'sın. Görevin uzun videoları, izleyiciyi en çok etkileyen viral kısa kliplere dönüştürmek.

Video başlığı: {title}

Transkript (timestamp formatında [start-end]):
{transcript_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ALGORİTMA — Aşağıdaki adımları eksiksiz uygula:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
• Süre: 0.5 saniye
• Başlangıç scale: 1.08 → Bitiş: 1.00
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
      "end": "0.5s",
      "from_scale": 1.08,
      "to_scale": 1.00
    }}
  }}
]

Kurallar:
- Timestamp'ler transcript'teki gerçek zamanlardan olmalı
- Çeşitli anlar seç (hepsi aynı bölümde olmasın)
- Her klip bağımsız olarak anlamlı olmalı
- Sadece JSON array döndür, başka bir şey yazma"""

    response = client.models.generate_content(
        model="gemini-3.6-flash", contents=prompt
    )
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


def create_ass(segments, start_offset, end_offset):
    """Create animated ASS subtitles with word-by-word highlight (OpusClip-style).

    Each word is rendered in white; the currently spoken word animates to
    yellow/green via a \\t transform over its own duration, giving a
    karaoke-style pop effect.
    """
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Word, Arial, 74, &H00FFFFFF, &H00FFFFFF, &H00000000, &H00000000, 1, 0, 0, 0, 100, 100, 0, 0, 1, 4, 2, 2, 60, 60, 100, 1
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
            text = f"{{\\c&H00FFFF&\\b1}}{seg['text']}{{\\b0}}"
            events.append(f"Dialogue: 0,{fmt_ass_time(clipped_start)},{fmt_ass_time(clipped_end)},Word,,0,0,0,,{text}")
            continue

        line_text_words = []
        for w in words:
            w_start = max(0, w["start"] - start_offset)
            w_end = min(end_offset - start_offset, w["end"] - start_offset)
            if w_end <= w_start:
                continue
            word_text = (
                f"{{\\1c&HFFFFFF&\\t({w_start:.2f},{w_end:.2f},\\1c&H00FFFF&)}}{w['word'].strip()}"
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


def build_ass_header(style):
    primary = hex_to_ass(style.get("primary", "#ffffff"))
    secondary = hex_to_ass(style.get("secondary", "#ffff00"))
    outline = hex_to_ass(style.get("outline", "#000000"))
    back = hex_to_ass(style.get("back", "#000000"))
    fontsize = int(style.get("fontsize", 74))
    bold = 1 if style.get("bold", True) else 0
    outline_w = int(style.get("outline_w", 4))
    shadow = int(style.get("shadow", 2))
    marginv = int(style.get("marginv", 100))
    style_line = (
        f"Style: Word, Arial, {fontsize}, {primary}, {secondary}, {outline}, {back}, "
        f"{bold}, 0, 0, 0, 100, 100, 0, 0, 1, {outline_w}, {shadow}, 2, 60, 60, {marginv}, 1"
    )
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{style_line}
WrapStyle: 1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def build_ass_with_style(words, start_offset, end_offset, new_text, style):
    """Build animated ASS from new caption text + style, mapped onto word timings."""
    header = build_ass_header(style)
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
            f"{{\\1c{idle}\\t({ws:.2f},{we:.2f},\\1c{active})}}{nwi}"
        )
        events.append(
            f"Dialogue: 0,{fmt_ass_time(ws)},{fmt_ass_time(we)},Word,,0,0,0,,{text}"
        )
    return header + "\n".join(events)


def rebuild_clip_ass(job_dir, start, end, new_text, style):
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
    return build_ass_with_style(window_words, start, end, new_text, style)


def fmt_srt_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def cut_clip(video_path, start, end, srt_content, output_path, ass_content=None):
    """Cut clip, crop to 9:16, burn (animated) subtitles, and create thumbnail."""
    duration = end - start

    # Generate thumbnail (at 2s into the clip)
    thumb_path = output_path.with_suffix(".jpg")
    thumb_cmd = [
        "ffmpeg", "-y",
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
    else:
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

    # FFmpeg: crop to 9:16 (center crop), add subtitles
    vf = (
        f"scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920,"
        f"{sub_filter}"
    )

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-i", video_path,
        "-t", str(duration),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(output_path),
    ]
    subprocess.run(cmd, capture_output=True, check=True)


def srt_path_escape(p):
    return p.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def recut_clip(video_path, job_dir, clip_name, start, end, new_ass_content):
    """Re-cut an existing clip with new timings and subtitles."""
    import shutil
    clip_output = job_dir / clip_name
    
    # Create new ASS file
    sub_path = str(clip_output) + ".ass"
    with open(sub_path, "w", encoding="utf-8") as f:
        f.write(new_ass_content)
    
    # Re-cut the video
    # Note: start/end are relative to the ORIGINAL source video
    cut_clip(video_path, start, end, None, clip_output, ass_content=new_ass_content)
    return True


def process_video(url, api_key, clip_count=6, callback=None, job_id=None, local_file=None, whisper_model="base", language=None):
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
            video_path, title = download_video(url, job_dir)
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
        moments = find_moments_gemini(transcript_text, api_key, title, clip_count)
        emit("moments_found", count=len(moments), progress=70)

        clips = []
        total = len(moments)
        for i, moment in enumerate(moments):
            emit("cutting_clip", clip_index=i, total=total, progress=70 + int(25 * i / total))
            hook = moment.get("hook_title", f"clip_{i+1}")
            safe_hook = re.sub(r'[^\w\s-]', '', hook)[:40].strip().replace(" ", "_")
            clip_name = f"{i+1:02d}_{safe_hook}.mp4"
            clip_output = job_dir / clip_name

            srt = create_srt(segments, moment["start"], moment["end"])
            ass = create_ass(segments, moment["start"], moment["end"])
            cut_clip(video_path, moment["start"], moment["end"], srt, clip_output, ass_content=ass)

            clips.append({
                "filename": clip_name,
                "hook": moment.get("hook_title", ""),
                "hook_sentence": moment.get("hook_sentence", ""),
                "closing_sentence": moment.get("closing_sentence", ""),
                "reason": moment.get("reason", ""),
                "viral_score": moment.get("viral_score", 0),
                "start": moment["start"],
                "end": moment["end"],
                "zoom_in": moment.get("zoom_in", {}),
            })

        emit("done", clips=clips, progress=100)
        return {"status": "done", "title": title, "clips": clips, "job_dir": str(job_dir)}

    except Exception as e:
        tb = traceback.format_exc()
        print(f"[ClipPulse ERROR] {e}\n{tb}")
        emit("error", error=str(e))
        return {"status": "error", "error": str(e)}
