# 整表生成提示词

Attach the actual original target-character image, accepted transparent anchor, and corresponding pose-reference cell(s). Use the full sheet to confirm order. Fill every variable from inspected references.

IDENTITY: {{CHARACTER_LOCK}}
The original target owns hair, eyes, skin, costume and accessories. Do not copy the purple reference character's identity. The anchor stabilizes rendering only.

POSE AND EXPRESSION: {{STATE_ACTION}} / {{STATE_EXPRESSION}}
Closely reproduce the specific template cell's head tilt, torso orientation, eye direction, mouth, hand contact points, palm orientation, leg crossing, foot direction, weight distribution and framing. Do not invent a semantically different pose. Clothing follows the target character, while anatomy and expression follow the pose template.

STYLE: match the template's chibi proportions, crisp dark outline and restrained cel shading. No golden/white sticker border, glow, outer shadow, realistic toy texture or figure stands. Keep consistent head scale and preserve aspect ratio.

SYMBOL PLAN: {{STATE_SYMBOL}}
Prefer character-only generation and deterministic separate symbols. If symbols are generated, match template location, scale, direction and spacing; their fill may follow target palette. No extra outer light border. Move/resize use separate outward-pointing triangles around the centered character.

OUTPUT: Generate 16 separated complete poses in a 4x4 concept sheet, in the exact order from state_map.md. No labels, text, borders or scenery. Do not exchange cells 12, 15 or 16. True transparency with full hair, fingers, feet and safe margins. No baked black backdrop. Preserve actual prompt and reference provenance. Do not claim pixel-exact replication.

CHECK: handwriting stays hands-on-hips with chin raised and upward gaze; text stays side-seated operating the low keyboard; horizontal stays hands-behind-back; link stays palm-up invitation; the two diagonal seated poses remain distinct. Repair those differences individually after visual comparison.
