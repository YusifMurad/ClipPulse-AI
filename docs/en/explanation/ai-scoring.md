# Explanation: How AI Scoring Works

ClipPulse AI ranks moments by *virality potential* using a two-stage pipeline.

## Stage 1 — Transcription

The audio is transcribed locally with **Faster-Whisper** (a quantized Whisper
implementation). This yields timestamped words in the chosen language. No audio
leaves your machine.

## Stage 2 — Moment selection (Gemini)

The transcript is sent to **Gemini 3.6 Flash**, which is prompted to:

1. Split the video into candidate segments (hooks, punchlines, insights).
2. Score each on a **0–100 viral potential** scale.
3. Return start/end timestamps + a short reason.

The model is instructed to favor: strong openings, emotional peaks, clear
payoffs, and self-contained context (so a clip makes sense on its own).

## Stage 3 — Rendering

Each selected segment is:

- cut with FFmpeg,
- reframed to **9:16** (center-crop, with padding fallback),
- overlaid with **animated ASS subtitles** (word-by-word highlight),
- given a generated **thumbnail**.

## Why local transcription + cloud scoring?

Keeping transcription local protects privacy and avoids per-minute API cost for
the heavy lifting, while the (cheap) Gemini call does the creative ranking where
a large model shines.

## Tuning

You can change `clip_count`, the transcription `language`, and (in code) the Gemini
prompt in `backend/pipeline.py` to bias toward different content types
(gaming, education, sermons, etc.).
