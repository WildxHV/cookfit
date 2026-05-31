"""Strict validation for AI-sourced food data.

The AI fallback may only write data into our DB if it passes every check here.
We trust nothing the model says: we re-verify it is vegetarian food, that the
per-100g macros are physically plausible and internally consistent, and that
every household unit resolves to grams the same way our seed data must.
"""

from __future__ import annotations

import re

from app.services.nutrition import (
    Macros,
    grams_for_quantity,
    macros_for_grams,
    sum_macros,
)

# Per-100g sanity bounds.
CAL_MAX = 900.0          # pure fat/oil tops out ~900
MACRO_MAX = 100.0        # can't have >100 g of a macro in 100 g
GRAMS_PER_UNIT_MAX = 3000.0
RECIPE_CAL_PER_SERVING_MAX = 3000.0
_VALID_FORMS = {"raw", "cooked"}
_IMPLICIT_UNITS = {"g", "gram", "grams", "100g", "kg"}

# Household units the app understands. The AI often returns verbose labels like
# "cup, sliced" or "piece (medium)"; we normalize those down to one of these.
_KNOWN_UNITS = {
    "katori", "cup", "tbsp", "tsp", "piece", "clove", "glass", "cube",
    "bunch", "slice", "bowl", "handful", "scoop", "ball", "pinch", "stick",
}
_UNIT_ALIASES = {
    "tablespoon": "tbsp", "tablespoons": "tbsp", "tbs": "tbsp",
    "teaspoon": "tsp", "teaspoons": "tsp",
    "pieces": "piece", "pc": "piece", "pcs": "piece", "medium": "piece",
    "small": "piece", "large": "piece", "whole": "piece",
    "cloves": "clove", "cups": "cup", "slices": "slice", "bowls": "bowl",
    "katoris": "katori", "glasses": "glass", "cubes": "cube",
}


class ValidationError(ValueError):
    """Raised when AI data is not safe to store."""


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return s or "item"


def _canonical_unit(label: str) -> str:
    """Reduce a free-form unit label to a canonical household unit.

    "cup, sliced" -> "cup", "piece (medium)" -> "piece", "Tablespoon" -> "tbsp".
    Returns "" if the label is blank; returns the cleaned first token otherwise.
    """
    low = label.strip().lower()
    if not low:
        return ""
    # Drop parentheticals and anything after a comma/slash.
    low = re.sub(r"\([^)]*\)", " ", low)
    low = re.split(r"[,/]", low)[0]
    words = re.findall(r"[a-z]+", low)
    if not words:
        return ""
    # Prefer a recognized unit word anywhere in the label.
    for w in words:
        if w in _KNOWN_UNITS:
            return w
        if w in _UNIT_ALIASES:
            return _UNIT_ALIASES[w]
    # Fall back to the last word (e.g. "medium tomato" -> "tomato").
    return words[-1]


def _macro_of(fact: dict) -> Macros:
    return Macros(
        calories=fact["calories"],
        protein_g=fact["protein_g"],
        fiber_g=fact["fiber_g"],
        carbs_g=fact["carbs_g"],
        fat_g=fact["fat_g"],
    )


def _check_fact(fact: dict, where: str) -> None:
    form = fact.get("form")
    if form not in _VALID_FORMS:
        raise ValidationError(f"{where}: invalid form {form!r}")
    for key in ("calories", "protein_g", "fiber_g", "carbs_g", "fat_g"):
        val = fact.get(key)
        if not isinstance(val, (int, float)) or val < 0:
            raise ValidationError(f"{where}: {key} must be a non-negative number")
    if fact["calories"] > CAL_MAX:
        raise ValidationError(f"{where}: calories {fact['calories']} exceed {CAL_MAX}")
    for key in ("protein_g", "fiber_g", "carbs_g", "fat_g"):
        if fact[key] > MACRO_MAX:
            raise ValidationError(f"{where}: {key} {fact[key]} exceeds {MACRO_MAX} g/100g")
    if fact["fiber_g"] > fact["carbs_g"] + 1.0:
        raise ValidationError(f"{where}: fiber cannot exceed carbs")
    # Atwater consistency: calories ~= 4P + 4C + 9F. Generous tolerance for
    # rounding, fiber, alcohol-free foods.
    expected = 4 * fact["protein_g"] + 4 * fact["carbs_g"] + 9 * fact["fat_g"]
    tol = max(45.0, 0.30 * expected)
    if abs(fact["calories"] - expected) > tol:
        raise ValidationError(
            f"{where}: calories {fact['calories']} inconsistent with macros "
            f"(expected ~{expected:.0f})"
        )


def _clean_units(units: list[dict], default_unit: str, where: str) -> tuple[list[dict], str]:
    """Normalize AI unit labels and reconcile the default unit.

    Returns (cleaned_units, default_unit). Verbose labels are canonicalized
    ("cup, sliced" -> "cup"). If the default unit can't be resolved against the
    cleaned units, it falls back to "g" (always available) rather than rejecting
    an otherwise-good ingredient.
    """
    cleaned: list[dict] = []
    seen: set[str] = set()
    for u in units or []:
        label = _canonical_unit(str(u.get("label", "")))
        grams = u.get("grams")
        if not label or label in _IMPLICIT_UNITS:
            continue  # skip blanks and implicit mass units (always available)
        if not isinstance(grams, (int, float)) or grams <= 0 or grams > GRAMS_PER_UNIT_MAX:
            raise ValidationError(f"{where}: unit '{label}' has implausible grams {grams}")
        if label in seen:
            continue
        seen.add(label)
        cleaned.append({"label": label, "grams": float(grams)})
    du = _canonical_unit(default_unit or "")
    if du and du not in _IMPLICIT_UNITS and du not in seen:
        du = "g"  # don't reject a good ingredient over a stray default unit
    return cleaned, (du or "g")


def _clean_tags(tags: list) -> list[str]:
    """Keep up to 8 short, deduped label tags. Drops blanks and anything that
    looks like a sentence rather than a label."""
    cleaned: list[str] = []
    seen: set[str] = set()
    for t in tags or []:
        label = str(t).strip().strip(".")
        if not label or len(label) > 30 or len(label.split()) > 4:
            continue
        key = label.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(label)
        if len(cleaned) >= 8:
            break
    return cleaned


def validate_ingredient(payload: dict, *, where: str = "ingredient") -> dict:
    """Validate one AI ingredient payload; return a normalized, insertable dict.

    Raises ValidationError on anything suspicious.
    """
    if not payload.get("is_food", False):
        raise ValidationError(f"{where}: not a recognized food item")
    if not payload.get("is_vegetarian", True):
        raise ValidationError(f"{where}: only vegetarian items are supported")

    name = str(payload.get("name", "")).strip()
    if not name:
        raise ValidationError(f"{where}: missing name")
    category = str(payload.get("category", "")).strip() or "other"

    facts = payload.get("facts") or []
    if not facts:
        raise ValidationError(f"{where}: no nutrition facts")
    forms_seen: set[str] = set()
    clean_facts: list[dict] = []
    for f in facts:
        _check_fact(f, where=f"{where} facts")
        if f["form"] in forms_seen:
            continue
        forms_seen.add(f["form"])
        clean_facts.append({
            "form": f["form"],
            "calories": float(f["calories"]),
            "protein_g": float(f["protein_g"]),
            "fiber_g": float(f["fiber_g"]),
            "carbs_g": float(f["carbs_g"]),
            "fat_g": float(f["fat_g"]),
        })

    default_form = payload.get("default_form", clean_facts[0]["form"])
    if default_form not in forms_seen:
        default_form = clean_facts[0]["form"]

    default_unit = str(payload.get("default_unit", "")).strip() or "g"
    units, default_unit = _clean_units(payload.get("units", []), default_unit, where)

    aliases = [str(a).strip() for a in payload.get("aliases", []) if str(a).strip()]
    tags = _clean_tags(payload.get("tags", []))

    return {
        "slug": slugify(name),
        "name": name,
        "aliases": aliases,
        "category": category,
        "default_unit": default_unit,
        "default_form": default_form,
        "units": units,
        "facts": clean_facts,
        "tags": tags,
    }


def _facts_by_form(clean_ingredient: dict) -> dict[str, Macros]:
    return {f["form"]: _macro_of(f) for f in clean_ingredient["facts"]}


def validate_recipe(payload: dict, *, where: str = "recipe") -> dict:
    """Validate an AI recipe payload (recipe + its ingredients).

    Returns a normalized dict with `recipe` and `ingredients` (both insertable),
    after confirming every item resolves to grams and macros are sane.
    """
    if not payload.get("is_recipe", False):
        raise ValidationError(f"{where}: not a recognized recipe")
    if not payload.get("is_vegetarian", True):
        raise ValidationError(f"{where}: only vegetarian recipes are supported")

    name = str(payload.get("name", "")).strip()
    if not name:
        raise ValidationError(f"{where}: missing name")

    raw_ings = payload.get("ingredients") or []
    if not raw_ings:
        raise ValidationError(f"{where}: no ingredient nutrition provided")

    by_name: dict[str, dict] = {}
    clean_ings: list[dict] = []
    for ing in raw_ings:
        clean = validate_ingredient(ing, where=f"{where} ingredient '{ing.get('name')}'")
        by_name[clean["name"].lower()] = clean
        clean_ings.append(clean)

    items = payload.get("items") or []
    if not items:
        raise ValidationError(f"{where}: no ingredient lines")

    clean_items: list[dict] = []
    per_serving: list[Macros] = []
    for item in items:
        iname = str(item.get("ingredient_name", "")).strip()
        ing = by_name.get(iname.lower())
        if ing is None:
            raise ValidationError(
                f"{where}: item '{iname}' has no matching ingredient entry"
            )
        qty = item.get("quantity")
        if not isinstance(qty, (int, float)) or qty <= 0:
            raise ValidationError(f"{where}: item '{iname}' has invalid quantity {qty}")
        unit_label = _canonical_unit(str(item.get("unit_label", "g"))) or "g"
        unit_weights = {u["label"]: u["grams"] for u in ing["units"]}
        try:
            grams = grams_for_quantity(qty, unit_label, unit_weights)
        except KeyError as exc:
            raise ValidationError(
                f"{where}: item '{iname}' uses unit '{unit_label}' which does not "
                f"resolve (units: {sorted(unit_weights)} + g/kg/100g)"
            ) from exc

        form = item.get("form", "raw")
        facts_by_form = _facts_by_form(ing)
        per_100g = facts_by_form.get(form) or next(iter(facts_by_form.values()))
        per_serving.append(macros_for_grams(per_100g, grams))

        clean_items.append({
            "ingredient_name": ing["name"],
            "ingredient_slug": ing["slug"],
            "quantity": float(qty),
            "unit_label": unit_label,
            "form": form if form in _VALID_FORMS else "raw",
            "note": (str(item.get("note")).strip() or None) if item.get("note") else None,
        })

    total = sum_macros(per_serving)
    if total.calories <= 0:
        raise ValidationError(f"{where}: computed 0 calories per serving")
    if total.calories > RECIPE_CAL_PER_SERVING_MAX:
        raise ValidationError(
            f"{where}: {total.calories:.0f} kcal/serving is implausibly high"
        )

    meal_type = str(payload.get("meal_type", "lunch")).strip() or "lunch"
    prep = payload.get("prep_time_min")
    prep = int(prep) if isinstance(prep, (int, float)) and prep > 0 else None
    tags = [str(t).strip() for t in payload.get("tags", []) if str(t).strip()]
    if "vegetarian" not in [t.lower() for t in tags]:
        tags.append("vegetarian")
    aliases = [str(a).strip() for a in payload.get("aliases", []) if str(a).strip()]

    recipe = {
        "slug": slugify(name),
        "name": name,
        "aliases": aliases,
        "meal_type": meal_type,
        "prep_time_min": prep,
        "instructions": str(payload.get("instructions", "")).strip() or None,
        "tags": tags,
        "items": clean_items,
    }
    return {"recipe": recipe, "ingredients": clean_ings}
