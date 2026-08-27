# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Auto GPU acceleration** — NVIDIA NVENC for video encoding and CUDA for Whisper when available, with automatic CPU fallback.
- **Parallel clip cutting** across all CPU cores (thread pool, load-balanced).
- **Download acceleration** via `aria2c` (auto-detected) or multi-fragment `yt-dlp` (16 concurrent fragments).
- **Full 14-language UI localization** with native-language selector labels and a CI translation guard (`scripts/check_translations.py`) that fails the build if any string is missing/untranslated.
- **Cross-platform launchers** (`start.sh` / `start.bat` / `start.ps1`) and first-class Windows support.

### Fixed
- UI no longer shows raw i18n keys (e.g. `tab_youtube`) — robust fallback keeps the original text.
- Repaired leaked placeholder tokens (`{cur}`, `{n}`…) in CJK languages.
- Corrected a Turkish "YouTube" tab label mistranslation.

## [0.1.0] - 2026-08-20

### Added
- Initial public release: paste a YouTube link or upload an MP4 → AI finds the best moments → animated subtitles → 9:16 clips for TikTok / Reels / Shorts.
- OpusClip-style word-by-word animated subtitles, viral-score ranking, in-browser clip editor, auto thumbnails, and auto disk cleanup.
- Self-hosted Flask backend + single-page web UI; Docker / Docker Compose images; optional Electron desktop wrapper.
