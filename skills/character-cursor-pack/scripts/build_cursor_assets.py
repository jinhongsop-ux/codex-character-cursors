"""Build transparent multi-size Windows CUR files and a preview from PNG poses."""
from __future__ import annotations

import argparse
from html import escape
import json
import math
import re
import struct
from pathlib import Path

from PIL import Image, ImageDraw


DEFAULT_SIZES = (32, 48, 64, 96)


def dib(image: Image.Image) -> bytes:
    size = image.width
    pixels = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM).tobytes("raw", "BGRA")
    stride = ((size + 31) // 32) * 4
    mask = bytearray(stride * size)
    alpha = image.getchannel("A")
    alpha_data = alpha.get_flattened_data()
    for y in range(size):
        for x in range(size):
            if alpha_data[(size - 1 - y) * size + x] == 0:
                mask[y * stride + x // 8] |= 0x80 >> (x % 8)
    header = struct.pack("<IiiHHIIiiII", 40, size, size * 2, 1, 32, 0,
                         len(pixels) + len(mask), 0, 0, 0, 0)
    return header + pixels + mask


def load_manifest(path: Path) -> tuple[list[int], int, list[dict]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    sizes = sorted(set(int(n) for n in data.get("sizes", DEFAULT_SIZES)))
    if not sizes or any(n < 16 or n > 256 for n in sizes):
        raise ValueError("sizes must be between 16 and 256 pixels")
    padding = int(data.get("padding", 0))
    if padding < 0 or padding * 2 >= min(sizes):
        raise ValueError("padding must be non-negative and smaller than half the smallest size")
    roles = data.get("roles")
    if not isinstance(roles, list) or not roles:
        raise ValueError("manifest needs a non-empty roles list")
    names = [item.get("role", "") for item in roles]
    if len(set(names)) != len(names) or any(not re.fullmatch(r"[A-Za-z0-9_-]+", n) for n in names):
        raise ValueError("role names must be unique ASCII filename-safe identifiers")
    known = set()
    for item in roles:
        if item.get("alias_of"):
            if item["alias_of"] not in known:
                raise ValueError(f"alias {item['role']} must refer to an earlier role")
        else:
            image_path = (path.parent / item["image"]).resolve()
            try:
                image_path.relative_to(path.parent.resolve())
            except ValueError as exc:
                raise ValueError(f"image path must stay inside manifest folder: {item['image']}") from exc
            if not image_path.is_file():
                raise FileNotFoundError(image_path)
            hot = item.get("hotspot")
            if not isinstance(hot, list) or len(hot) != 2:
                raise ValueError(f"{item['role']} needs hotspot: [x, y] in source-image pixels")
        known.add(item["role"])
    return sizes, padding, roles


def build_sprite(source: Image.Image, size: int, padding: int, base_size: int) -> tuple[Image.Image, tuple[int, int]]:
    w, h = source.size
    frame_padding = round(padding * size / base_size)
    scale = (size - 2 * frame_padding) / max(w, h)
    rw, rh = max(1, round(w * scale)), max(1, round(h * scale))
    resized = source.resize((rw, rh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    offset = ((size - rw) // 2, (size - rh) // 2)
    canvas.alpha_composite(resized, offset)
    return canvas, offset


def write_cur(path: Path, frames: list[tuple[int, Image.Image, tuple[int, int]]],
              source_hotspot: tuple[float, float], source_size: tuple[int, int], padding: int) -> dict:
    base_size = max(n for n, _, _ in frames)
    w, h = source_size
    base_scale = (base_size - 2 * padding) / max(w, h)
    base_w, base_h = max(1, round(w * base_scale)), max(1, round(h * base_scale))
    base_pos = ((base_size - base_w) // 2, (base_size - base_h) // 2)
    hot_base = (round(base_pos[0] + source_hotspot[0] * base_scale),
                round(base_pos[1] + source_hotspot[1] * base_scale))

    entries, blobs, hotspots = [], [], {}
    offset = 6 + 16 * len(frames)
    for size, image, _ in frames:
        hot = tuple(max(0, min(size - 1, math.ceil(v * size / base_size))) for v in hot_base)
        blob = dib(image)
        dim = 0 if size == 256 else size
        entries.append(struct.pack("<BBBBHHII", dim, dim, 0, 0, hot[0], hot[1], len(blob), offset))
        blobs.append(blob)
        hotspots[str(size)] = list(hot)
        offset += len(blob)
    path.write_bytes(struct.pack("<HHH", 0, 2, len(frames)) + b"".join(entries) + b"".join(blobs))
    return hotspots


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="JSON manifest; see references/manifest-schema.md")
    parser.add_argument("output", type=Path, help="new or empty output directory")
    args = parser.parse_args()
    manifest_path = args.manifest.resolve()
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"Output folder is not empty; choose a new folder: {output}")
    sizes, padding, roles = load_manifest(manifest_path)
    cursor_dir = output / "cursors"
    cursor_dir.mkdir(parents=True, exist_ok=True)
    records, preview_records = [], []

    for item in roles:
        role = item["role"]
        if item.get("alias_of"):
            target = item["alias_of"]
            for suffix in (".cur", ".png"):
                (cursor_dir / f"{role}{suffix}").write_bytes((cursor_dir / f"{target}{suffix}").read_bytes())
            target_record = next(r for r in records if r["role"] == target)
            records.append({**target_record, "role": role, "label": item.get("label", role), "alias_of": target})
            preview_records.append((role, item.get("label", role), Image.open(cursor_dir / f"{role}.png").convert("RGBA"), target_record["hotspots"]))
            continue

        image_path = (manifest_path.parent / item["image"]).resolve()
        source = Image.open(image_path).convert("RGBA")
        if source.getchannel("A").getextrema() == (0, 0):
            raise ValueError(f"{role} image is fully transparent")
        hx, hy = (float(item["hotspot"][0]), float(item["hotspot"][1]))
        if not (0 <= hx < source.width and 0 <= hy < source.height):
            raise ValueError(f"{role} hotspot is outside its source image")
        frames = []
        for size in sizes:
            frame, offset = build_sprite(source, size, padding, max(sizes))
            frames.append((size, frame, offset))
            (output / "frames" / str(size)).mkdir(parents=True, exist_ok=True)
            frame.save(output / "frames" / str(size) / f"{role}.png")
        hot = write_cur(cursor_dir / f"{role}.cur", frames, (hx, hy), source.size, padding)
        display_size = 64 if 64 in sizes else max(sizes)
        frames_by_size = {n: im for n, im, _ in frames}
        display = frames_by_size[display_size]
        display.save(cursor_dir / f"{role}.png")
        record = {"role": role, "label": item.get("label", role), "image": item["image"],
                  "hotspots": hot, "sizes": sizes, "alias_of": None}
        records.append(record)
        preview_records.append((role, item.get("label", role), frames_by_size[max(sizes)], hot))

    cols, card_w, card_h = 4, 250, 220
    rows = math.ceil(len(preview_records) / cols)
    preview = Image.new("RGB", (cols * card_w, rows * card_h), "#f3eef8")
    draw = ImageDraw.Draw(preview)
    for i, (role, label, frame, hot) in enumerate(preview_records):
        x, y = (i % cols) * card_w, (i // cols) * card_h
        for bx, color in ((x + 12, "#ffffff"), (x + 132, "#26212e")):
            tile = Image.new("RGBA", (108, 108), color)
            tile.alpha_composite(frame)
            preview.paste(tile.convert("RGB"), (bx, y + 32))
        draw.text((x + 15, y + 155), role, fill="#342342")
        draw.text((x + 15, y + 174), label, fill="#584468")
    output.mkdir(parents=True, exist_ok=True)
    preview.save(output / "Preview.png")
    out_manifest = {"theme": json.loads(manifest_path.read_text(encoding="utf-8")).get("theme", "Character Cursor"),
                    "sizes": sizes, "roles": records}
    (output / "manifest.json").write_text(json.dumps(out_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    cards = []
    for r in records:
        size_key = str(64 if 64 in sizes else max(sizes))
        hx, hy = r["hotspots"][size_key]
        label = escape(r["label"])
        cards.append(f'<div class="card" style="cursor:url(\'cursors/{r["role"]}.png\') {hx} {hy},default"><img src="cursors/{r["role"]}.png" alt=""><b>{label}</b><small>{r["role"]}</small></div>')
    theme_title = escape(str(out_manifest["theme"]))
    html = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Cursor Preview</title><style>body{font:16px system-ui;background:#f4f0f8;color:#332341;margin:32px}main{max-width:1000px;margin:auto}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px}.card{display:flex;align-items:center;flex-direction:column;background:white;border:1px solid #ded3e8;border-radius:14px;padding:18px;gap:8px}.card img{width:64px;height:64px}small{color:#80688e}</style><main><h1>' + theme_title + '</h1><div class="grid">' + ''.join(cards) + '</div></main></html>'
    (output / "Preview.html").write_text(html, encoding="utf-8")
    print(f"Built {len(records)} cursor roles, {len(sizes)} sizes each, in {output}")


if __name__ == "__main__":
    main()
