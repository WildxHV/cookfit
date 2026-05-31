"""Suggest dishes a user can cook from the ingredients they have on hand.

Unlike the catalog lookup, these are ephemeral ideas (authentic + fusion), not
stored in the DB. We assume common pantry staples are available and ask Gemini
for realistic vegetarian dishes.
"""

from __future__ import annotations

from app.services.ai_lookup import _call_gemini

# Everyday items we assume the user already has, so dishes aren't limited to a
# literal reading of their list.
PANTRY_STAPLES = [
    "salt", "oil", "ghee", "water", "sugar", "cumin (jeera)",
    "mustard seeds (rai)", "turmeric (haldi)", "red chili powder",
    "coriander powder", "garam masala", "black pepper", "green chili",
    "ginger", "garlic", "onion",
]

_SUGGEST_SCHEMA = {
    "type": "object",
    "properties": {
        "suggestions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "kind": {"type": "string", "enum": ["authentic", "fusion"]},
                    "description": {"type": "string"},
                    "uses": {"type": "array", "items": {"type": "string"}},
                    "pantry": {"type": "array", "items": {"type": "string"}},
                    "steps": {"type": "array", "items": {"type": "string"}},
                    "tags": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["name", "kind", "description", "uses", "steps"],
            },
        }
    },
    "required": ["suggestions"],
}

_PROMPT = """You are a creative vegetarian Indian home cook helping someone use \
what they already have.

They have these ingredients: {have}.

Assume these everyday pantry staples are ALSO available: {pantry}.

Suggest 4-6 VEGETARIAN dishes they can realistically make right now. Include a \
mix of authentic Indian dishes AND creative fusion / original ideas (for \
example, with palak + paneer + pasta you might suggest a high-protein \
palak-paneer pasta where the palak and paneer are blended into the sauce).

Rules:
- Only suggest dishes that are genuinely makeable from the listed ingredients \
plus the pantry staples. Do not require major ingredients they don't have.
- Every dish MUST be vegetarian (no meat, fish, poultry, egg).
- For each dish: a short appetizing name; kind = "authentic" or "fusion"; a \
one-line description; uses = the subset of THEIR listed ingredients it uses; \
pantry = the staples it relies on; steps = 4-7 short cooking steps; tags like \
high_protein, quick, fusion, comfort_food.
- Prefer dishes that use several of their ingredients together. Make at least \
one a fun fusion idea when the ingredients allow it."""


def suggest_dishes(ingredients: list[str]) -> list[dict]:
    """Ask Gemini for dishes makeable from `ingredients` (+ pantry staples)."""
    have = ", ".join(i.strip() for i in ingredients if i.strip()) or "basic staples"
    prompt = _PROMPT.format(have=have, pantry=", ".join(PANTRY_STAPLES))
    data = _call_gemini(prompt, _SUGGEST_SCHEMA)

    out: list[dict] = []
    for s in data.get("suggestions", []):
        name = str(s.get("name", "")).strip()
        steps = [str(x).strip() for x in s.get("steps", []) if str(x).strip()]
        if not name or not steps:
            continue
        kind = s.get("kind", "authentic")
        out.append({
            "name": name,
            "kind": kind if kind in ("authentic", "fusion") else "authentic",
            "description": str(s.get("description", "")).strip(),
            "uses": [str(x).strip() for x in s.get("uses", []) if str(x).strip()],
            "pantry": [str(x).strip() for x in s.get("pantry", []) if str(x).strip()],
            "steps": steps,
            "tags": [str(x).strip() for x in s.get("tags", []) if str(x).strip()][:6],
        })
    return out
