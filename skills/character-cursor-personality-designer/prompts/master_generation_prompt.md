# 单格生成提示词

Attach the actual original target-character image, accepted transparent anchor, and corresponding SELECTED_TEMPLATE pose-reference cell(s). Use the full sheet to confirm order. Fill every variable from inspected references.

IDENTITY: {{CHARACTER_LOCK}}
The original target owns hair, eyes, skin, costume and accessories. Do not copy the purple reference character's identity. The anchor stabilizes rendering only.

POSE AND EXPRESSION: {{STATE_ACTION}} / {{STATE_EXPRESSION}}
Closely reproduce the specific template cell's head tilt, torso orientation, eye direction, mouth, hand contact points, palm orientation, leg crossing, foot direction, weight distribution and framing. Do not invent a semantically different pose. Clothing follows the target character, while anatomy and expression follow the pose template.

STYLE: match the template's chibi proportions, crisp dark outline and restrained cel shading. No golden/white sticker border, glow, outer shadow, realistic toy texture or figure stands. Keep consistent head scale and preserve aspect ratio.

SYMBOL PLAN: {{STATE_SYMBOL}}
Prefer character-only generation and deterministic separate symbols. If symbols are generated, match template location, scale, direction and spacing; their fill may follow target palette. No extra outer light border. Move/resize use separate outward-pointing triangles around the centered character.

OUTPUT: Generate one complete transparent square state. True transparency with full hair, fingers, feet and safe margins. No baked black backdrop. Preserve actual prompt and reference provenance. Do not claim pixel-exact replication.

CHECK (Reze template only; use the chosen template’s actual cells for other templates): handwriting stays hands-on-hips with chin raised and upward gaze; text stays side-seated operating the low keyboard; horizontal stays hands-behind-back; link stays palm-up invitation; the two diagonal seated poses remain distinct. Repair those differences individually after visual comparison.

PERSONALITY ROUTING: Selected template {{SELECTED_TEMPLATE}}. Evidence-backed personality summary {{PERSONALITY_SUMMARY}}. Use this template for all16 states; never silently fall back to Reze. Template-specific prop markings are not target identity. Check anatomically natural neck/shoulder alignment and consistent torso front/back.
