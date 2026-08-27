# How-to: Subtitles

ClipPulse AI generates OpusClip-style animated subtitles using the ASS format.

## Editing captions

1. After clips are generated, open a clip in the browser editor.
2. Click the caption text to edit the words.
3. Save — the ASS file is regenerated and the clip re-rendered.

## Style notes

- **Word-by-word highlight**: the current word is colored; others stay neutral.
- **Smart wrapping**: `WrapStyle=1` keeps long lines inside the 9:16 frame.
- **Position**: subtitles sit in the lower third to avoid covering faces.

## Customizing

The ASS style lives in `backend/pipeline.py` (`create_ass`). Key parameters:

| Parameter | Meaning |
|-----------|---------|
| `FontName` | Subtitle font (default system sans) |
| `PrimaryColour` / `SecondaryColour` | idle vs active word color (ASS &H format, BGR) |
| `FontSize` | base size in pixels |
| `Bold` | `1` for bold |
| `Alignment` | `2` = bottom-center |
| `MarginV` | vertical margin from bottom |

Change these and re-run **Create Clips** to see the new look.
