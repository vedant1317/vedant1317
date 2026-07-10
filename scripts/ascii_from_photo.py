#!/usr/bin/env python3
"""Convert a portrait photo to the ascii_art.txt used by generate_profile.py.

Run locally (the photo itself is never committed):
    pip install pillow
    python scripts/ascii_from_photo.py /path/to/photo.jpg
Then run scripts/generate_profile.py to redraw the SVGs.
"""
import sys
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

COLS, ROWS = 46, 44          # art grid
CHAR_AR = 0.52               # mono char width/height ratio
GAMMA = 1.35                 # >1 pushes midtones lighter (smoother face)
CHARSET = " ..,:;i|(?*!jxzkmwMN%$@@"   # light -> dense

def main(photo: str) -> None:
    img = Image.open(photo).convert("L")

    # crop to subject: bounding box of non-white pixels, with a small margin
    bw = img.point(lambda p: 0 if p > 235 else 255)
    l, t, r, b = bw.getbbox()
    mw, mh = int((r - l) * 0.04), int((b - t) * 0.02)
    img = img.crop((max(0, l - mw), max(0, t - mh),
                    min(img.width, r + mw), min(img.height, b + mh)))

    # fit to the grid's aspect ratio, sharpen, normalize
    target_ar = (COLS * CHAR_AR) / ROWS
    img = ImageOps.fit(img, (int(1000 * target_ar), 1000), centering=(0.5, 0.35))
    img = img.filter(ImageFilter.UnsharpMask(radius=3, percent=120))
    img = ImageOps.autocontrast(img, cutoff=1)
    img = img.resize((COLS, ROWS))

    px = img.load()
    lines = []
    for y in range(ROWS):
        row = "".join(
            CHARSET[int((((255 - px[x, y]) / 255) ** GAMMA) * (len(CHARSET) - 1))]
            for x in range(COLS)
        )
        lines.append(row.rstrip())

    out = Path(__file__).resolve().parent.parent / "ascii_art.txt"
    out.write_text("\n".join(lines))
    print(f"wrote {out} ({ROWS} rows) — now run scripts/generate_profile.py")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/ascii_from_photo.py <photo>")
    main(sys.argv[1])
