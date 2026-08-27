# 🎬 ClipPulse AI

> **Pega un enlace de YouTube → la IA encuentra tus mejores momentos → subtítulos animados → listo para TikTok, Reels y Shorts.**
> Gratis. Código abierto. Auto-alojado. Sin tarjeta. Sin límites de subida.

[![Estrellas](https://img.shields.io/github/stars/YusifMurad/ClipPulse-AI?style=for-the-badge)](https://github.com/YusifMurad/ClipPulse-AI/stargazers)
[![Discussions](https://img.shields.io/badge/Discussions-activo-purple?logo=github&style=for-the-badge)](https://github.com/YusifMurad/ClipPulse-AI/discussions)

<p align="center">
  <img src="https://github.com/user-attachments/assets/5ae92a0d-b851-48d2-a31d-a771aaf24488" alt="ClipPulse AI" width="900">
</p>

## ✨ ¿Por qué ClipPulse AI?

Grabaste un podcast, directo o clase de 40 minutos. El oro está enterrado dentro — pero
encontrar y cortar los 5 clips que realmente se vuelven virales lleva horas. **ClipPulse AI lo hace en minutos.**

1. 🎯 **La IA encuentra los momentos** (Gemini puntúa cada segmento 0–100)
2. 📱 **Clips verticales 9:16** para cada plataforma
3. ✨ **Subtítulos animados estilo OpusClip** (resaltado palabra por palabra)
4. 🧠 **Transcripción en 14 idiomas** (Faster-Whisper, tus datos son tuyos)
5. 🖱️ **Editor en el navegador** — recorta, re-escribe, re-puntúa

Sin suscripciones. Sin marcas de agua. Sin "prueba gratis de 30 segundos".

## 🚀 Inicio rápido — 30 segundos

```bash
git clone https://github.com/YusifMurad/ClipPulse-AI.git
cd ClipPulse-AI
chmod +x start.sh
./start.sh
```

Abre **http://localhost:5555**, pega un enlace de YouTube y pulsa **Crear Clips**.

### 🐳 O con Docker

```bash
docker run -p 5555:5555 -v "$PWD/output:/app/output" ghcr.io/yusifmurad/clippulse-ai:latest
```

## 🎯 ¿Para quién es?

| Tú eres… | ClipPulse te ayuda a… |
|----------|----------------------|
| 🎥 **Creador** | Convertir un vídeo largo en 10+ clips por semana |
| 🏢 **Agencia** | Procesar vídeos de clientes en lote |
| 🎓 **Educador** | Resaltar explicaciones clave |
| 🎙️ **Podcaster** | Promocionar episodios en vertical |

## 📦 Características

- 🎯 **Selección IA de clips** (Gemini)
- 📱 **Formato 9:16** — TikTok / Reels / Shorts
- ✨ **Subtítulos animados** estilo OpusClip
- 🔤 **14 idiomas** — es, en, tr, fr, de, it, pt, ru, ar, zh, ja, ko, hi, nl
- 📁 **Archivos locales** — sube tu MP4, nada sale de tu máquina
- ✂️ **Editor de clips** en el navegador
- 🔒 **Privado por diseño** — la clave de API nunca va al cliente

## 🤝 Contribuir

👉 **[CONTRIBUTING.md](CONTRIBUTING.md)** · **[Discussions](https://github.com/YusifMurad/ClipPulse-AI/discussions)**

## 📄 Licencia

[MIT](LICENSE) — úsalo libremente.
