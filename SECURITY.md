# Security Policy

## 🔒 Supported Versions

| Version | Supported |
|---------|-----------|
| `main`  | ✅ Yes    |
| older   | ❌ No     |

## 🐞 Reporting a Vulnerability

If you discover a security vulnerability in ClipPulse AI, **please do not open a
public issue.** Instead:

1. Go to the repository's **Security** tab → **Report a vulnerability**, or
2. Open a private [Security Advisory](https://github.com/YusifMurad/ClipPulse-AI/security/advisories/new), or
3. Reach the maintainer through a private [GitHub Discussion](https://github.com/YusifMurad/ClipPulse-AI/discussions).

We will acknowledge your report within **72 hours** and aim to provide a fix or
mitigation within **14 days**, depending on severity.

## 🛡️ Security notes for users

- Your **Gemini API key is stored only on the server** (`backend/config/settings.json`)
  and is **never sent to the browser**. The client only receives a masked value.
- `backend/config/` is git-ignored — your key is never committed.
- Local file uploads are processed on your own machine/instance; nothing is sent
  to a third party except the YouTube fetch (which goes through your instance) and
  the Gemini API call you explicitly configure.
- We recommend running ClipPulse AI behind a reverse proxy (nginx/Caddy) with HTTPS
  and, if exposed, adding authentication.
