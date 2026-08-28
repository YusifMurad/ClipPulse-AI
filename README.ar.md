# 🎬 ClipPulse AI

> **احرص رابط يوتيوب ← الذكاء الاصطناعي يجد أفضل لحظاتك ← ترجمة متحركة ← جاهز لـ TikTok وReels وShorts.**
> مجاني. مفتوح المصدر. يُستضاف ذاتيًا. بدون بطاقة ائتمان. بدون حدود رفع.

> 📘 **جديد هنا؟** شرح كامل خطوة بخطوة (التثبيت، مفتاح Gemini، أول مقطع في 5 دقائق): <https://docs.google.com/document/d/1FJCDa0gOhb5WGHNZhXCejX3ShV1lMpiTg2txsd16T5c/edit?tab=t.0#heading=h.o4q50hf8bf2>

[![النجوم](https://img.shields.io/github/stars/YusifMurad/ClipPulse-AI?style=for-the-badge)](https://github.com/YusifMurad/ClipPulse-AI/stargazers)
[![النقاشات](https://img.shields.io/badge/Discussions-نشط-purple?logo=github&style=for-the-badge)](https://github.com/YusifMurad/ClipPulse-AI/discussions)

<p align="center" dir="rtl">
  <img src="https://github.com/user-attachments/assets/5ae92a0d-b851-48d2-a31d-a771aaf24488" alt="ClipPulse AI" width="900">
</p>

<div dir="rtl">

## ✨ لماذا ClipPulse AI؟

سجّلت بودكاست أو بثًا مباشرًا أو محاضرة مدتها 40 دقيقة. الذهب مدفون بداخلها — لكن
إيجاد وقطع الـ 5 مقاطع التي ستنتشر فعليًا يستغرق ساعات. **ClipPulse AI يفعل ذلك في دقائق.**

1. 🎯 **الذكاء الاصطناعي يجد اللحظات** (Gemini يقيّم كل جزء من 0–100)
2. 📱 **مقاطع عمودية 9:16** لكل منصة
3. ✨ **ترجمة متحركة بأسلوب OpusClip** (تمييز الكلمات)
4. 🧠 **نسخ بـ 14 لغة** (Faster-Whisper، بياناتك تبقى معك)
5. 🖱️ **محرر في المتصفح** — قص، أعد الكتابة، أعد التقييم

بدون اشتراكات. بدون علامات مائية. بدون "تجربة مجانية 30 ثانية".

## 🚀 البداية السريعة — 30 ثانية

```bash
git clone https://github.com/YusifMurad/ClipPulse-AI.git
cd ClipPulse-AI
chmod +x start.sh
./start.sh
```

افتح **http://localhost:5555**، الصق رابط يوتيوب واضغط **إنشاء المقاطع**.

### 🐳 أو عبر Docker

```bash
docker run -p 5555:5555 -v "$PWD/output:/app/output" ghcr.io/yusifmurad/clippulse-ai:latest
```

## 🎯 لمن هذا؟

| أنت… | يساعدك ClipPulse في… |
|------|---------------------|
| 🎥 **صانع محتوى** | تحويل فيديو واحد إلى 10+ مقاطع أسبوعيًا |
| 🏢 **وكالة** | معالجة فيديوهات العملاء بالجملة |
| 🎓 **معلم** | إبراز الشرح الأساسي |
| 🎙️ **مقدّم بودكاست** | الترويج للحلقات بشكل عمودي |

## 📦 المميزات

- 🎯 **اختيار المقاطع بالذكاء الاصطناعي** (Gemini)
- 📱 **تنسيق 9:16** — TikTok / Reels / Shorts
- ✨ **ترجمة متحركة** بأسلوب OpusClip
- 🔤 **14 لغة** — ar, en, tr, fr, de, es, it, pt, ru, zh, ja, ko, hi, nl
- 📁 **ملفات محلية** — ارفع MP4 الخاص بك، لا يغادر جهازك
- ✂️ **محرر مقاطع** في المتصفح
- 🔒 **خصوصية بالتصميم** — مفتاح API لا يُرسل للعميل

## 🤝 المساهمة

👉 **[CONTRIBUTING.md](CONTRIBUTING.md)** · **[النقاشات](https://github.com/YusifMurad/ClipPulse-AI/discussions)**

## 📄 الترخيص

[MIT](LICENSE) — استخدمه بحرية.

</div>
