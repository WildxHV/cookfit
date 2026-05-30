"""Google Gemini lookup for foods missing from our DB.

Asks Gemini (free tier) for structured nutrition data, using a strict JSON
response schema. This module ONLY fetches + parses — every value is re-checked
by `ai_validation` before anything touches the database. Nothing here is
trusted on faith.
"""

from __future__ import annotations

import json

import httpx

from app.core.config import get_settings

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


class GeminiError(RuntimeError):
    """Raised when the Gemini call fails or returns unusable output."""


# ---- Response schemas (OpenAPI subset accepted by Gemini) -------------------

_MACRO_FIELDS = ["calories", "protein_g", "fiber_g", "carbs_g", "fat_g"]

_FACTS_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "form": {"type": "string", "enum": ["raw", "cooked"]},
            **{f: {"type": "number"} for f in _MACRO_FIELDS},
        },
        "required": ["form", *_MACRO_FIELDS],
    },
}

_UNITS_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "label": {"type": "string"},
            "grams": {"type": "number"},
        },
        "required": ["label", "grams"],
    },
}

_INGREDIENT_SCHEMA = {
    "type": "object",
    "properties": {
        "is_food": {"type": "boolean"},
        "is_vegetarian": {"type": "boolean"},
        "name": {"type": "string"},
        "category": {"type": "string"},
        "aliases": {"type": "array", "items": {"type": "string"}},
        "default_unit": {"type": "string"},
        "default_form": {"type": "string", "enum": ["raw", "cooked"]},
        "units": _UNITS_SCHEMA,
        "facts": _FACTS_SCHEMA,
    },
    "required": [
        "is_food", "is_vegetarian", "name", "category",
        "default_unit", "default_form", "units", "facts",
    ],
}

_RECIPE_SCHEMA = {
    "type": "object",
    "properties": {
        "is_recipe": {"type": "boolean"},
        "is_vegetarian": {"type": "boolean"},
        "name": {"type": "string"},
        "aliases": {"type": "array", "items": {"type": "string"}},
        "meal_type": {
            "type": "string",
            "enum": ["breakfast", "lunch", "dinner", "snack", "dessert", "drink"],
        },
        "prep_time_min": {"type": "integer"},
        "instructions": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "ingredient_name": {"type": "string"},
                    "quantity": {"type": "number"},
                    "unit_label": {"type": "string"},
                    "form": {"type": "string", "enum": ["raw", "cooked"]},
                    "note": {"type": "string"},
                },
                "required": ["ingredient_name", "quantity", "unit_label", "form"],
            },
        },
        # Full nutrition for every ingredient used above, so we can insert any
        # that we don't already have and guarantee units resolve.
        "ingredients": {
            "type": "array",
            "items": _INGREDIENT_SCHEMA,
        },
    },
    "required": [
        "is_recipe", "is_vegetarian", "name", "meal_type",
        "instructions", "items", "ingredients",
    ],
}


_INGREDIENT_PROMPT = """You are a nutrition database for an Indian vegetarian \
home-cooking app. The user searched for an ingredient: "{query}".

Return structured JSON for this single food ingredient.

Rules:
- If "{query}" is NOT a real food ingredient, set is_food=false and leave other \
fields with placeholder values.
- If it is a non-vegetarian item (meat, fish, poultry, egg), set \
is_vegetarian=false.
- All nutrition is PER 100 GRAMS. Use realistic values from standard food \
tables (IFCT 2017 / USDA). calories must be roughly 4*protein_g + 4*carbs_g + \
9*fat_g.
- Provide a "raw" facts entry always; add "cooked" only if it is normally eaten \
cooked and the values differ.
- units: 2-4 common household measures with their gram weights. Each label \
MUST be a SINGLE plain word from: katori, cup, tbsp, tsp, piece, clove, glass, \
slice, bowl, bunch (no extra words like "cup, sliced" or "piece (medium)"). \
default_unit must be exactly one of these labels, or "g".
- category: one short word like dal, legume, grain, flour, vegetable, fruit, \
dairy, nuts, fat, spice, sweetener, beverage.
- name: use the form "English Name (common Indian name)" whenever the food has \
a well-known Hindi/Indian name that differs, e.g. "Asafoetida (hing)", \
"Fenugreek Seeds (methi dana)", "Clarified Butter (ghee)". If the common name \
is already the English name (e.g. Paneer, Quinoa, Oats), just use it plainly. \
Also list the common Indian name(s) in aliases.
- Keep numbers plausible (calories 0-900; each macro 0-100 g per 100 g)."""


_RECIPE_PROMPT = """You are a recipe + nutrition database for an Indian \
vegetarian home-cooking app. The user searched for a dish: "{query}".

Return structured JSON for this single dish, scaled to ONE serving (one person).

Rules:
- If "{query}" is NOT a real cooked dish/recipe, set is_recipe=false.
- If the dish is non-vegetarian (meat, fish, poultry, egg), set \
is_vegetarian=false.
- items: the ingredients for ONE serving. Each item references an ingredient by \
ingredient_name. Prefer unit_label "g" with a gram quantity; you may use \
household units (tsp, tbsp, piece, clove, katori) when natural.
- ingredients: for EVERY distinct ingredient_name used in items, include one \
full ingredient entry (per-100g nutrition + household units). Unit labels MUST \
be single plain words (katori, cup, tbsp, tsp, piece, clove, glass, slice, \
bowl, bunch) or "g". The unit_label used in items MUST be "g" or appear in that \
ingredient's units list.
- ingredient names: use the form "English Name (common Indian name)" when a \
well-known Hindi name differs (e.g. "Asafoetida (hing)", "Coriander Leaves \
(hara dhania)"); otherwise the plain name. Use the same ingredient_name in \
items and in the ingredients entry.
- All nutrition PER 100 GRAMS, realistic (calories ~ 4*protein + 4*carbs + \
9*fat).
- meal_type one of breakfast/lunch/dinner/snack/dessert/drink. tags like \
high_protein, high_fiber, vegetarian, low_fat. Keep it healthy and authentic."""


def _call_gemini(prompt: str, schema: dict) -> dict:
    settings = get_settings()
    if not settings.ai_enabled:
        raise GeminiError("AI lookup is disabled (no GEMINI_API_KEY configured).")

    url = GEMINI_URL.format(model=settings.gemini_model)
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema,
            "temperature": 0.2,
        },
    }
    try:
        resp = httpx.post(
            url,
            params={"key": settings.gemini_api_key},
            json=body,
            timeout=settings.gemini_timeout_s,
        )
    except httpx.HTTPError as exc:
        raise GeminiError(f"Gemini request failed: {exc}") from exc

    if resp.status_code != 200:
        raise GeminiError(
            f"Gemini returned {resp.status_code}: {resp.text[:300]}"
        )

    try:
        payload = resp.json()
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)
    except (KeyError, IndexError, json.JSONDecodeError, TypeError) as exc:
        raise GeminiError(f"Could not parse Gemini response: {exc}") from exc


def lookup_ingredient(query: str) -> dict:
    """Fetch structured ingredient data from Gemini. Unvalidated."""
    return _call_gemini(_INGREDIENT_PROMPT.format(query=query), _INGREDIENT_SCHEMA)


def lookup_recipe(query: str) -> dict:
    """Fetch structured recipe data (+ its ingredients) from Gemini. Unvalidated."""
    return _call_gemini(_RECIPE_PROMPT.format(query=query), _RECIPE_SCHEMA)
