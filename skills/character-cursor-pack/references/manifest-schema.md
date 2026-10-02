# Asset-builder manifest

`scripts/build_cursor_assets.py` turns transparent pose PNGs into CUR files and previews. Save a JSON manifest next to a `sprites/` folder and give the builder a new, empty output directory.

```json
{
  "theme": "Original Character Cursor",
  "sizes": [32, 48, 64, 96],
  "padding": 0,
  "roles": [
    {
      "role": "Arrow",
      "label": "普通选择",
      "image": "sprites/Arrow.png",
      "hotspot": [12, 18]
    },
    {
      "role": "Help",
      "label": "帮助",
      "image": "sprites/Help.png",
      "hotspot": [14, 20]
    },
    {
      "role": "Pin",
      "label": "位置选择",
      "alias_of": "Arrow"
    }
  ]
}
```

- `role` is a unique ASCII filename-safe identifier. `label` is the user-facing state name.
- `image` is a transparent PNG path relative to the manifest. Every non-alias role requires a `hotspot` in source-image pixel coordinates, starting at the top-left.
- `alias_of` reuses an earlier role's CUR and PNG when a Windows role has no distinct pose. An alias does not need `image` or `hotspot`.
- `sizes` defaults to 32, 48, 64, and 96. Values must be 16–256. `padding` is the transparent margin in pixels at the largest size; it defaults to 0 to keep the character large.
- The output folder must be new or empty. The builder writes `cursors/*.cur`, preview PNGs, a contact-sheet preview, an HTML preview, and a normalized manifest. It will not erase a non-empty output folder.

Run from the skill folder or pass absolute paths:

```text
python scripts/build_cursor_assets.py <path-to-manifest.json> <new-output-folder>
```

The helper requires Pillow. It does not invent, recolor, or remove backgrounds from the supplied pose art; inspect transparent edges on both light and dark backgrounds before shipping.
