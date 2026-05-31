"""AI lookup for foods/recipes missing from our DB.

Asks an LLM for structured JSON using a strict response schema. To keep calls
from failing on a single provider's rate limit, this tries a pool of backends
(multiple Gemini models, plus optional OpenAI / Grok / Groq — all configured by
env keys) in round-robin with fallback. This module ONLY fetches + parses —
every value is re-checked by `ai_validation` before anything touches the DB.
"""

from __future__ import annotations

import itertools
import json
import logging
from dataclasses import dataclass

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


class GeminiError(RuntimeError):
    """Raised when ALL configured AI backends fail. (Name kept for callers.)"""


# Public alias so call sites read naturally regardless of provider.
AIError = GeminiError


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
        "tags": {"type": "array", "items": {"type": "string"}},
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
- tags: 2-6 short health labels for this food. Use "gluten-free" when it has no \
gluten, "high protein"/"high fiber" when notably so, and the key vitamins/ \
minerals it is a good source of (e.g. "Vitamin C", "Potassium", "Iron", \
"Calcium", "Omega-3"). Only include what is genuinely true.
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


class _BackendError(RuntimeError):
    """One backend failed; the orchestrator should try the next."""


@dataclass(frozen=True)
class _Backend:
    label: str          # for logs/errors, e.g. "gemini:gemini-2.5-flash"
    kind: str           # "gemini" | "openai"
    model: str
    api_key: str
    base_url: str | None = None  # OpenAI-compatible base URL


# Round-robin cursor so we don't always start at the same backend.
_rr = itertools.count()


def _build_backends(settings) -> list[_Backend]:
    """Every configured backend, Gemini models first, then OpenAI-compatibles."""
    backends: list[_Backend] = []
    if settings.gemini_api_key.strip():
        for model in settings.gemini_model_list:
            backends.append(
                _Backend(f"gemini:{model}", "gemini", model, settings.gemini_api_key)
            )
    if settings.openai_api_key.strip():
        backends.append(
            _Backend("openai", "openai", settings.openai_model,
                     settings.openai_api_key, settings.openai_base_url)
        )
    if settings.xai_api_key.strip():
        backends.append(
            _Backend("grok", "openai", settings.xai_model,
                     settings.xai_api_key, settings.xai_base_url)
        )
    if settings.groq_api_key.strip():
        backends.append(
            _Backend("groq", "openai", settings.groq_model,
                     settings.groq_api_key, settings.groq_base_url)
        )
    return backends


def _gemini_generate(
    b: _Backend, prompt: str, schema: dict, max_output_tokens: int | None, timeout: float
) -> dict:
    gen_config: dict = {
        "responseMimeType": "application/json",
        "responseSchema": schema,
        "temperature": 0.2,
    }
    if max_output_tokens is not None:
        gen_config["maxOutputTokens"] = max_output_tokens
        # Spend the token budget on output, not internal "thinking", so large
        # arrays in batch responses aren't cut off.
        gen_config["thinkingConfig"] = {"thinkingBudget": 0}
    body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": gen_config}
    try:
        resp = httpx.post(
            GEMINI_URL.format(model=b.model),
            params={"key": b.api_key}, json=body, timeout=timeout,
        )
    except httpx.HTTPError as exc:
        raise _BackendError(f"{b.label} request failed: {exc}") from exc
    if resp.status_code != 200:
        raise _BackendError(f"{b.label} -> {resp.status_code}: {resp.text[:160]}")
    try:
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)
    except (KeyError, IndexError, json.JSONDecodeError, TypeError) as exc:
        raise _BackendError(f"{b.label} unparseable: {exc}") from exc


def _openai_generate(
    b: _Backend, prompt: str, schema: dict, max_output_tokens: int | None, timeout: float
) -> dict:
    """OpenAI-compatible chat completion in JSON mode (OpenAI / Grok / Groq)."""
    messages = [
        {"role": "system", "content":
            "You are a precise JSON API. Reply with ONLY a single JSON object "
            "that conforms to the schema the user gives. No prose, no markdown."},
        {"role": "user", "content":
            prompt + "\n\nReturn ONLY a JSON object matching this JSON schema:\n"
            + json.dumps(schema)},
    ]
    body: dict = {
        "model": b.model,
        "messages": messages,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    if max_output_tokens is not None:
        body["max_tokens"] = max_output_tokens
    try:
        resp = httpx.post(
            f"{b.base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {b.api_key}"},
            json=body, timeout=timeout,
        )
    except httpx.HTTPError as exc:
        raise _BackendError(f"{b.label} request failed: {exc}") from exc
    if resp.status_code != 200:
        raise _BackendError(f"{b.label} -> {resp.status_code}: {resp.text[:160]}")
    try:
        content = resp.json()["choices"][0]["message"]["content"]
        return json.loads(content)
    except (KeyError, IndexError, json.JSONDecodeError, TypeError) as exc:
        raise _BackendError(f"{b.label} unparseable: {exc}") from exc


def _generate_json(
    prompt: str, schema: dict, *, max_output_tokens: int | None = None
) -> dict:
    """Try every configured backend (round-robin start, then fallback) until one
    returns valid JSON. Raises GeminiError only if they all fail."""
    settings = get_settings()
    backends = _build_backends(settings)
    if not backends:
        raise GeminiError("AI is not configured (no provider API key set).")

    timeout = settings.gemini_timeout_s + (60.0 if max_output_tokens else 0.0)
    n = len(backends)
    start = next(_rr) % n
    order = [backends[(start + i) % n] for i in range(n)]

    errors: list[str] = []
    for b in order:
        try:
            if b.kind == "gemini":
                return _gemini_generate(b, prompt, schema, max_output_tokens, timeout)
            return _openai_generate(b, prompt, schema, max_output_tokens, timeout)
        except _BackendError as exc:
            errors.append(str(exc))
            logger.info("AI backend failed, trying next: %s", exc)
            continue

    raise GeminiError("All AI backends failed: " + " | ".join(errors))


# Backward-compatible name used elsewhere (e.g. ai_suggest).
_call_gemini = _generate_json


def lookup_ingredient(query: str) -> dict:
    """Fetch structured ingredient data from Gemini. Unvalidated."""
    return _call_gemini(_INGREDIENT_PROMPT.format(query=query), _INGREDIENT_SCHEMA)


def lookup_recipe(query: str) -> dict:
    """Fetch structured recipe data (+ its ingredients) from Gemini. Unvalidated."""
    return _call_gemini(_RECIPE_PROMPT.format(query=query), _RECIPE_SCHEMA)


# ---- Batch lookups (one call for many items) --------------------------------

_INGREDIENTS_BATCH_SCHEMA = {
    "type": "object",
    "properties": {"ingredients": {"type": "array", "items": _INGREDIENT_SCHEMA}},
    "required": ["ingredients"],
}

_RECIPES_BATCH_SCHEMA = {
    "type": "object",
    "properties": {"recipes": {"type": "array", "items": _RECIPE_SCHEMA}},
    "required": ["recipes"],
}

_INGREDIENTS_BATCH_PROMPT = (
    "You are a nutrition database for an Indian vegetarian home-cooking app. "
    "Return one structured entry for EACH of these ingredients: {queries}.\n\n"
    "Follow these rules for every entry:\n"
    + _INGREDIENT_PROMPT.split("Rules:", 1)[1].strip()
).replace('"{query}"', "the ingredient")

_RECIPES_BATCH_PROMPT = (
    "You are a recipe + nutrition database for an Indian vegetarian home-cooking "
    "app. Return one structured recipe (scaled to ONE serving) for EACH of these "
    "dishes: {queries}.\n\nFollow these rules for every recipe:\n"
    + _RECIPE_PROMPT.split("Rules:", 1)[1].strip()
).replace('"{query}"', "the dish")


def lookup_ingredients(queries: list[str]) -> list[dict]:
    """Fetch many ingredients in a SINGLE Gemini call. Unvalidated."""
    if not queries:
        return []
    prompt = _INGREDIENTS_BATCH_PROMPT.replace("{queries}", ", ".join(queries))
    data = _call_gemini(prompt, _INGREDIENTS_BATCH_SCHEMA, max_output_tokens=8192)
    return list(data.get("ingredients", []))


def lookup_recipes(queries: list[str]) -> list[dict]:
    """Fetch many recipes (each with its ingredients) in a SINGLE Gemini call."""
    if not queries:
        return []
    prompt = _RECIPES_BATCH_PROMPT.replace("{queries}", ", ".join(queries))
    data = _call_gemini(prompt, _RECIPES_BATCH_SCHEMA, max_output_tokens=32768)
    return list(data.get("recipes", []))
