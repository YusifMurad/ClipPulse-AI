# 🎬 ClipPulse AI

> **YouTube linki yapıştır → AI en iyi anları bulur → Animasyonlu altyazı → TikTok, Reels ve Shorts'a hazır.**
> Ücretsiz. Açık kaynak. Kendi sunucunda. Kredi kartı yok. Yükleme sınırı yok.

[![Yıldız](https://img.shields.io/github/stars/YusifMurad/ClipPulse-AI?style=for-the-badge)](https://github.com/YusifMurad/ClipPulse-AI/stargazers)
[![Discussions](https://img.shields.io/badge/Discussions-aktif-purple?logo=github&style=for-the-badge)](https://github.com/YusifMurad/ClipPulse-AI/discussions)
[![Docker](https://img.shields.io/badge/Docker-hazır-blue?logo=docker&style=for-the-badge)](https://github.com/YusifMurad/ClipPulse-AI/pkgs/container/clippulse-ai)

<p align="center">
  <img src="https://github.com/user-attachments/assets/5ae92a0d-b851-48d2-a31d-a771aaf24488" alt="ClipPulse AI Ekran Görüntüsü" width="900">
</p>

---

## ✨ Neden ClipPulse AI?

40 dakikalık bir podcast, canlı yayın veya ders kaydettin. Altın içinde gömülü — ama
viral olacak 5 clip'i bulup kesmek saatler sürer. **ClipPulse AI bunu dakikalara indirir.**

1. 🎯 **AI anları bulur** (Gemini her segmenti 0–100 skorlar)
2. 📱 **9:16 dikey clip** — her kısa video platformuna uygun
3. ✨ **OpusClip tarzı animasyonlu altyazı** (kelime kelime renk vurgusu)
4. 🧠 **14 dilde transkript** (Faster-Whisper, verileriniz sizde kalır)
5. 🖱️ **Tarayıcı editörü** — kes, yeniden yaz, yeniden skorla

Abonelik yok. Filigran yok. "30 saniye kısıtlayan ücretsiz deneme" yok.

---

## 🚀 Hızlı Başlangıç — 30 saniye

```bash
git clone https://github.com/YusifMurad/ClipPulse-AI.git
cd ClipPulse-AI
chmod +x start.sh
./start.sh
```

**http://localhost:5555** adresini aç, YouTube URL yapıştır (veya MP4 bırak), **Clipleri Oluştur**'a bas.

> 💡 İlk çalıştırmada Python sanal ortamı otomatik kurulur. Sadece ücretsiz
> [Google Gemini API anahtarı](https://aistudio.google.com/apikey) gereklidir (Ayarlar'a bir kez yapıştır).

### 🐳 Veya Docker ile

```bash
docker run -p 5555:5555 -v "$PWD/output:/app/output" ghcr.io/yusifmurad/clippulse-ai:latest
```

---

## 🎯 Kimler için?

| Sen… | ClipPulse sana… |
|------|-----------------|
| 🎥 **İçerik Üreticisi** | Haftada bir uzun videodan 10+ paylaşılabilir clip |
| 🏢 **Ajans** | Müşteri videolarını toplu işle |
| 🎓 **Eğitmen** | Derslerden önemli anları vurgula |
| 🎙️ **Podcaster** | Bölümleri dikey snippet'lerle tanıt |

---

## 📦 Özellikler

- 🎯 **AI Clip Seçimi** — otomatik viral an tespit (Gemini)
- 📱 **9:16 Dikey** — TikTok / Reels / Shorts hazır
- ✨ **Animasyonlu Altyazı** — OpusClip tarzı kelime vurgusu, akıllı sarma
- 🔤 **14 Dil** — tr, en, es, fr, de, it, pt, ru, ar, zh, ja, ko, hi, nl
- 📁 **Yerel Dosya** — kendi MP4'unu yükle, verin makineden çıkmaz
- ✂️ **Clip Editörü** — tarayıcıda kes & yeniden yaz
- 🖼️ **Otomatik Küçük Resim** — her clip için kapak görseli
- 🔒 **Gizlilik öncelikli** — API anahtarı sunucuda, istemciye gönderilmez

---

## 🤝 Katkı

Katkılardan memnuniyet duyarız. 👉 **[CONTRIBUTING.md](CONTRIBUTING.md)** ·
**[Discussions](https://github.com/YusifMurad/ClipPulse-AI/discussions)**

## 📄 Lisans

[MIT](LICENSE) — özgürce kullan.
