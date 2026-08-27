#!/bin/bash
# ClipPulse AI — demo recorder
# Records a screen region to assets/demo.mp4 (and optionally a .gif).
# Usage:
#   ./scripts/record-demo.sh            # interactive: pick region, 20s
#   ./scripts/record-demo.sh 30         # record 30 seconds
#   ./scripts/record-demo.sh 30 gif     # also produce assets/demo.gif
#
# Requirements: ffmpeg, x11grab (Linux/X11). On Wayland use wl-screenrec or OBS.
set -e

SECONDS="${1:-20}"
MAKE_GIF="${2:-}"

mkdir -p assets

echo "Move your mouse to the TOP-LEFT of the area you want to record,"
echo "then press Enter. Then move to the BOTTOM-RIGHT and press Enter again."
read -r -p "Top-left (Enter when ready): " _
eval "$(xdotool getmouselocation --shell)"
X1=$X; Y1=$Y
read -r -p "Bottom-right (Enter when ready): " _
eval "$(xdotool getmouselocation --shell)"
X2=$X; Y2=$Y

W=$((X2 - X1)); H=$((Y2 - Y1))
echo "Recording ${W}x${H} for ${SECONDS}s into assets/demo.mp4 ..."
ffmpeg -y -f x11grab -framerate 30 -video_size "${W}x${H}" -i ":0.0+${X1},${Y1}" \
  -c:v libx264 -pix_fmt yuv420p -movflags +faststart "assets/demo.mp4" &
FFPID=$!
sleep "$SECONDS"
kill -INT "$FFPID" 2>/dev/null || true
wait "$FFPID" 2>/dev/null || true

if [ "$MAKE_GIF" = "gif" ]; then
  echo "Converting to assets/demo.gif (this may take a bit)..."
  ffmpeg -y -i assets/demo.mp4 -vf "fps=15,scale=540:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
    -loop 0 assets/demo.gif
fi

echo "Done → assets/demo.mp4$( [ "$MAKE_GIF" = "gif" ] && echo ' + assets/demo.gif' )"
