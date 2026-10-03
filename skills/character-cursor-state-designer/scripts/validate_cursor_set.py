#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from PIL import Image


def main():
    p = argparse.ArgumentParser(description="Validate cursor-state PNG assets and manifest linkage.")
    p.add_argument("root", help="Output root containing manifest.json and states/")
    args = p.parse_args()

    root = Path(args.root)
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        raise SystemExit("FAIL: manifest.json not found")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    states = manifest.get("states", [])
    if not states:
        raise SystemExit("FAIL: manifest contains no states")

    expected_size = manifest.get("canvas_px")
    errors = []
    seen_sizes = set()
    files = [s.get('file') for s in states]
    indices = [s.get('index') for s in states]
    if len(files) != len(set(files)) or len(indices) != len(set(indices)):
        errors.append('duplicate file or state index')
    if len(states) == 16:
        roles = ['Arrow','Help','AppStarting','Wait','Crosshair','IBeam','NWPen','No','SizeAll','SizeWE','SizeNESW','UpArrow','SizeNS','SizeNWSE','Hand','Extra']
        if [s.get('role') for s in states] != roles or indices != list(range(1,17)):
            errors.append('16-cell order or role mapping does not match template')
    system = manifest.get('system_roles', {})
    expected_system = {'Arrow','Help','AppStarting','Wait','Crosshair','IBeam','NWPen','No','SizeAll','SizeWE','SizeNESW','UpArrow','SizeNS','SizeNWSE','Hand','Pin','Person'}
    if system and (set(system) != expected_system or any(f not in files for f in system.values())):
        errors.append('invalid 17-role system mapping or alias linkage')

    for item in states:
        rel = item.get("file")
        name = item.get("state", rel)
        if not rel:
            errors.append(f"{name}: missing file path in manifest")
            continue
        path = root / rel
        if not path.exists():
            errors.append(f"{name}: missing {rel}")
            continue
        try:
            with Image.open(path) as im:
                if im.format != "PNG":
                    errors.append(f"{name}: expected PNG, got {im.format}")
                if im.width != im.height:
                    errors.append(f"{name}: not square ({im.width}x{im.height})")
                if expected_size and (im.width != expected_size or im.height != expected_size):
                    errors.append(f"{name}: expected {expected_size}x{expected_size}, got {im.width}x{im.height}")
                seen_sizes.add((im.width, im.height))
                if "A" not in im.getbands() and "transparency" not in im.info:
                    errors.append(f"{name}: no alpha/transparency channel")
                else:
                    alpha = im.convert('RGBA').getchannel('A')
                    low, high = alpha.getextrema()
                    bbox = alpha.point(lambda a:255 if a > 8 else 0).getbbox()
                    if low != 0 or high == 0 or not bbox:
                        errors.append(f'{name}: expected nonempty art and truly transparent background')
                    elif min(bbox[0],bbox[1],im.width-bbox[2],im.height-bbox[3]) < 2:
                        errors.append(f'{name}: visible art touches boundary or lacks safe padding')
        except Exception as e:
            errors.append(f"{name}: cannot open image: {e}")

    if len(seen_sizes) > 1:
        errors.append(f"inconsistent canvas sizes: {sorted(seen_sizes)}")

    if errors:
        print("VALIDATION FAILED")
        for e in errors:
            print("-", e)
        raise SystemExit(1)

    print(f"PASS: {len(states)} state assets validated")
    if len(states) == 16:
        print("Note: 16-state bundled reference set detected.")
    if system:
        print('Note: 17 Windows system roles mapped; Pin/Person aliases are explicit.')


if __name__ == "__main__":
    main()
