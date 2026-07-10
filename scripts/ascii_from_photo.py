#!/usr/bin/env python3
"""Convert a portrait photo to the ascii_art.txt used by generate_profile.py.

Works best on a subject isolated on a plain background. For photos with busy
backgrounds, first cut out the subject with macOS Vision (on-device):

    swift scripts/subject_mask.swift photo.jpg subject.png

then run this on the cutout:

    pip install pillow
    python scripts/ascii_from_photo.py subject.png --box 398 570 618 884

The --box is the face-tight crop (left top right bottom) in source pixels;
pick it so the face fills most of the frame. The photo itself is never
committed — only the resulting ascii_art.txt is.
"""
import argparse
from pathlib import Path

from PIL import Image, ImageFilter

COLS, ROWS = 84, 62
GAMMA = 0.72
LO, HI = 0.04, 0.55          # tone stretch: face -> dense, shadows -> sparse
SOFT_CAP = 0.80              # blown-out highlights (white shirt) get capped
CHARSET = " ..,:;i|(?*!jxzkmwMN%$@@"

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("--box", nargs=4, type=int, metavar=("L", "T", "R", "B"),
                    help="face-tight crop in source pixels")
    args = ap.parse_args()

    img = Image.open(args.photo).convert("L")
    if args.box:
        img = img.crop(tuple(args.box))
    img = img.filter(ImageFilter.UnsharpMask(radius=4, percent=150))
    img = img.resize((COLS, ROWS))

    px = img.load()
    lines = []
    for y in range(ROWS):
        row = ""
        for x in range(COLS):
            raw = px[x, y] / 255
            v = min(max((raw - LO) / (HI - LO), 0.0), 1.0)
            if raw > SOFT_CAP:
                v = 0.82
            row += CHARSET[int((v ** GAMMA) * (len(CHARSET) - 1))]
        lines.append(row.rstrip())

    out = Path(__file__).resolve().parent.parent / "ascii_art.txt"
    out.write_text("\n".join(lines))
    print(f"wrote {out} ({ROWS} rows) — now run scripts/generate_profile.py")

if __name__ == "__main__":
    main()
