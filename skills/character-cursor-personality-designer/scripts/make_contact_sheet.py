#!/usr/bin/env python3
import argparse
import json
import math
from pathlib import Path
from PIL import Image


def main():
    p = argparse.ArgumentParser(description="Build a contact sheet from cursor-state PNGs using manifest order.")
    p.add_argument("root", help="Output root containing manifest.json and states/")
    p.add_argument("--columns", type=int, default=4)
    p.add_argument("--padding", type=int, default=24)
    p.add_argument("--background", default="#111111", help="Preview background color")
    p.add_argument("--output", default="contact_sheet.png")
    args = p.parse_args()

    root = Path(args.root)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    states = manifest["states"]
    imgs = []
    for s in states:
        path = root / s["file"]
        imgs.append(Image.open(path).convert("RGBA"))

    cell_w = max(i.width for i in imgs)
    cell_h = max(i.height for i in imgs)
    cols = max(1, args.columns)
    rows = math.ceil(len(imgs) / cols)
    w = cols * cell_w + (cols + 1) * args.padding
    h = rows * cell_h + (rows + 1) * args.padding
    sheet = Image.new("RGBA", (w, h), args.background)

    for idx, im in enumerate(imgs):
        r, c = divmod(idx, cols)
        x = args.padding + c * (cell_w + args.padding) + (cell_w - im.width) // 2
        y = args.padding + r * (cell_h + args.padding) + (cell_h - im.height) // 2
        sheet.alpha_composite(im, (x, y))

    out = root / args.output
    sheet.save(out)
    print(out)


if __name__ == "__main__":
    main()
