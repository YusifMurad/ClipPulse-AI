# 🎬 ClipPulse AI

> **粘贴 YouTube 链接 → AI 找到最佳时刻 → 动画字幕 → 准备好发布到 TikTok、Reels 和 Shorts。**
> 免费。开源。自托管。无需信用卡。无上传限制。

[![Stars](https://img.shields.io/github/stars/YusifMurad/ClipPulse-AI?style=for-the-badge)](https://github.com/YusifMurad/ClipPulse-AI/stargazers)
[![Discussions](https://img.shields.io/badge/Discussions-活跃-purple?logo=github&style=for-the-badge)](https://github.com/YusifMurad/ClipPulse-AI/discussions)

<p align="center">
  <img src="https://github.com/user-attachments/assets/5ae92a0d-b851-48d2-a31d-a771aaf24488" alt="ClipPulse AI" width="900">
</p>

## ✨ 为什么选择 ClipPulse AI？

你录制了一期 40 分钟的播客、直播或讲座。精华藏在里面——但找出并剪辑出
真正会爆火的 5 个片段要花好几个小时。**ClipPulse AI 只需几分钟。**

1. 🎯 **AI 找出精彩时刻**（Gemini 为每个片段打分 0–100）
2. 📱 **9:16 竖屏片段** 适配各平台
3. ✨ **OpusClip 风格动画字幕**（逐词高亮）
4. 🧠 **14 种语言转录**（Faster-Whisper，数据留在本地）
5. 🖱️ **浏览器编辑器** —— 剪辑、重写、重新打分

无订阅。无 watermarks。无"30 秒免费试用"。

## 🚀 快速开始 — 30 秒

```bash
git clone https://github.com/YusifMurad/ClipPulse-AI.git
cd ClipPulse-AI
chmod +x start.sh
./start.sh
```

打开 **http://localhost:5555**，粘贴 YouTube 链接，点击 **创建片段**。

### 🐳 或使用 Docker

```bash
docker run -p 5555:5555 -v "$PWD/output:/app/output" ghcr.io/yusifmurad/clippulse-ai:latest
```

## 🎯 适合谁？

| 你是… | ClipPulse 帮你… |
|------|----------------|
| 🎥 **创作者** | 一周从一个长视频产出 10+ 片段 |
| 🏢 **机构** | 批量处理客户视频 |
| 🎓 **教师** | 突出讲解重点 |
| 🎙️ **播客主** | 用竖屏片段宣传节目 |

## 📦 功能

- 🎯 **AI 片段选择**（Gemini）
- 📱 **9:16 竖屏** — TikTok / Reels / Shorts
- ✨ **动画字幕** OpusClip 风格
- 🔤 **14 种语言** — zh, en, tr, fr, de, es, it, pt, ru, ar, ja, ko, hi, nl
- 📁 **本地文件** — 上传你的 MP4，数据不出本机
- ✂️ **浏览器片段编辑器**
- 🔒 **隐私优先** — API 密钥不发送到客户端

## 🤝 贡献

👉 **[CONTRIBUTING.md](CONTRIBUTING.md)** · **[讨论区](https://github.com/YusifMurad/ClipPulse-AI/discussions)**

## 📄 许可证

[MIT](LICENSE) — 自由使用。
