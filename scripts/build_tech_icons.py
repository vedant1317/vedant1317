#!/usr/bin/env python3
"""Draw the handful of tech logos that no icon service renders as a tile.

skillicons.dev and go-skill-icons cover almost the whole stack, but a few
brands are missing from both (OpenAI and Twilio were pulled from simple-icons'
CDN over trademark policy; the rest were never added). Rather than fall back to
flat text badges — which look nothing like the tiles around them — this redraws
them in skillicons' exact geometry: a 256x256 tile, rx=60, laid out on a 300px
pitch, so the row is indistinguishable from the service-rendered ones.

Glyph paths come from the simple-icons npm package at build time. Stdlib-only.
Run: python scripts/build_tech_icons.py
"""
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

CDN = "https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/{}.svg"

# (simple-icons slug, tile background). Glyphs are drawn white on top.
# #242938 is skillicons' neutral tile, used for brands whose mark is monochrome.
ICONS = [
    ("openai", "#242938"),
    ("twilio", "#F22F46"),
    ("razorpay", "#3395FF"),
    ("jinja", "#B41717"),
    ("i18next", "#26A69A"),
]

TILE, PITCH, GLYPH = 256, 300, 148  # glyph box centred inside the tile


def glyph_path(slug):
    with urllib.request.urlopen(CDN.format(slug), timeout=30) as r:
        svg = r.read().decode()
    m = re.search(r'<path[^>]*\sd="([^"]+)"', svg)
    if not m:
        raise SystemExit(f"no path found in simple-icons SVG for {slug}")
    return m.group(1)


def main():
    n = len(ICONS)
    w = PITCH * n - (PITCH - TILE)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w / TILE * 48:.1f}" '
           f'height="48" viewBox="0 0 {w} {TILE}" fill="none">']
    # simple-icons ship on a 24x24 grid; scale and centre them in the tile.
    scale = GLYPH / 24
    off = (TILE - GLYPH) / 2
    for i, (slug, bg) in enumerate(ICONS):
        out.append(f'<g transform="translate({i * PITCH}, 0)">')
        out.append(f'<rect width="{TILE}" height="{TILE}" rx="60" fill="{bg}"/>')
        out.append(f'<g transform="translate({off:.1f}, {off:.1f}) scale({scale:.4f})">'
                   f'<path fill="#fff" d="{glyph_path(slug)}"/></g>')
        out.append("</g>")
    out.append("</svg>")
    (ASSETS / "tech-extra.svg").write_text("\n".join(out))
    print(f"wrote assets/tech-extra.svg ({n} tiles)")


if __name__ == "__main__":
    main()
