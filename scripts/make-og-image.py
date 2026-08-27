#!/usr/bin/env python3
"""Generate the social preview (OG) image as an SVG.

Usage:  python3 scripts/make-og-image.py  > assets/og-image.svg
Then reference assets/og-image.svg in the docs <meta> and GitHub Pages.
For Twitter/OpenGraph cards you'll want a PNG; convert with:
    rsvg-convert assets/og-image.svg -o assets/og-image.png
or use the HTML generator at docs/assets/og-image-generator.html.
"""
WIDTH, HEIGHT = 1280, 640


def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build(stars: str = "★") -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1a0b2e"/>
      <stop offset="100%" stop-color="#3b0764"/>
    </linearGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#ec4899"/>
      <stop offset="100%" stop-color="#a855f7"/>
    </linearGradient>
  </defs>
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#bg)"/>
  <circle cx="1080" cy="120" r="260" fill="#a855f7" opacity="0.15"/>
  <circle cx="180" cy="560" r="200" fill="#ec4899" opacity="0.12"/>
  <text x="80" y="250" font-family="Segoe UI, Arial, sans-serif" font-size="92" font-weight="800" fill="#ffffff">ClipPulse AI</text>
  <text x="82" y="330" font-family="Segoe UI, Arial, sans-serif" font-size="40" fill="#e9d5ff">Turn any video into viral clips</text>
  <rect x="82" y="380" width="640" height="14" rx="7" fill="url(#accent)"/>
  <text x="82" y="450" font-family="Segoe UI, Arial, sans-serif" font-size="34" fill="#f5d0fe">YouTube → AI moments → animated subtitles</text>
  <text x="82" y="510" font-family="Segoe UI, Arial, sans-serif" font-size="34" fill="#f5d0fe">Free · Open source · Self-hosted</text>
  <text x="82" y="580" font-family="Segoe UI, Arial, sans-serif" font-size="30" fill="url(#accent)" font-weight="700">github.com/YusifMurad/ClipPulse-AI</text>
</svg>'''


if __name__ == "__main__":
    import sys
    stars = sys.argv[1] if len(sys.argv) > 1 else "★"
    print(build(stars))
