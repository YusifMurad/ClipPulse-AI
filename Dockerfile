FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/root/.deno/bin:${PATH}"

WORKDIR /app

# System deps: FFmpeg + tools needed by yt-dlp / faster-whisper
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    git \
    ca-certificates \
    unzip \
    fonts-dejavu \
    fonts-liberation \
    fonts-noto-core \
    fonts-noto-color-emoji \
    fonts-freefont-ttf \
    fonts-roboto \
    fonts-open-sans \
    fonts-montserrat \
    fonts-crosextra-carlito \
    && rm -rf /var/lib/apt/lists/*

# Deno (for yt-dlp JS runtime challenges)
RUN curl -fsSL https://deno.land/install.sh | sh

# Python deps
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/backend/requirements.txt

# App code
COPY backend/ /app/backend/
COPY app.js index.html styles.css /app/
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

ENV OUTPUT_DIR=/app/output
RUN mkdir -p /app/output

EXPOSE 5555

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:5555/api/health')" || exit 1

CMD ["sh", "-c", "cd /app/backend && python3 server.py"]
