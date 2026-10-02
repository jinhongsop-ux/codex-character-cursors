# Edge and color validation for finished state sheets

Retain an untouched source and reproducible crop/mask parameters. Crop all states from that source, not a previous recolored preview. Keep foreground interiors opaque and RGB-identical before resizing; record interior pixel mismatches rather than relying only on visual impressions.

Use a narrow edge trimap (two pixels was effective for the source sheet in this project; tune for other resolutions). Where source antialiasing mixed foreground with a pale background, solve the mixture in the edge band using an estimated background and neighboring foreground colors. State that edge RGB can change through mathematical de-matting, while opaque interior RGB is preserved. Do not promise that every RGB byte remains identical if resampling or edge decontamination was performed.

Exclude text and outer borders with crop/mask regions, preserving detached cursor glyphs belonging to each state. Background flood-fill must not leak into white clothing or remove black outlines. Inspect hair tips, boots, white shirt edges and gaps around arms at native resolution and enlarged scale against dark backgrounds. Avoid both white halos and dark erosion outlines.

For color QA, compare same-scale source crops and extracted sprites in a neutral preview. Track representative opaque colors and brightness; diagnose preview CSS filters, compositing backgrounds and resize interpolation before recoloring. If Windows is available, compare actual loaded cursor pixels and hotspots to the corresponding CUR frame. A photographed screen is useful for visible complaints but cannot establish original pixel equality.
