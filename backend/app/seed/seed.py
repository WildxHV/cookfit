"""Seed the database from curated JSON files.

Idempotent: wipes existing catalog rows and reloads from
`ingredients.json` and `recipes.json`. Run from `backend/`:

    .venv/Scripts/python.exe -m app.seed.seed
"""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import (
    Ingredient,
    IngredientUnit,
    NutritionFacts,
    Recipe,
    RecipeIngredient,
)
from app.services.nutrition import grams_for_quantity

SEED_DIR = Path(__file__).resolve().parent

_VALID_FORMS = {"raw", "cooked"}


def _validate(ingredients: list[dict], recipes: list[dict]) -> None:
    """Fail loudly before touching the DB if the curated data is malformed.

    This is our own-data version of the "no false entries" guard: every recipe
    line must reference a known ingredient with a unit that actually resolves to
    grams, otherwise the recipe would 500 at request time.
    """
    errors: list[str] = []
    by_slug: dict[str, dict] = {}

    for row in ingredients:
        slug = row.get("slug")
        if not slug:
            errors.append(f"Ingredient missing slug: {row.get('name', row)!r}")
            continue
        if slug in by_slug:
            errors.append(f"Duplicate ingredient slug: {slug!r}")
        by_slug[slug] = row
        if not row.get("name") or not row.get("category"):
            errors.append(f"Ingredient '{slug}' missing name/category")
        forms = [f.get("form") for f in row.get("facts", [])]
        if not forms:
            errors.append(f"Ingredient '{slug}' has no nutrition facts")
        for form in forms:
            if form not in _VALID_FORMS:
                errors.append(f"Ingredient '{slug}' has invalid form {form!r}")

    seen_recipes: set[str] = set()
    for row in recipes:
        rslug = row.get("slug", "<no-slug>")
        if rslug in seen_recipes:
            errors.append(f"Duplicate recipe slug: {rslug!r}")
        seen_recipes.add(rslug)
        for item in row.get("items", []):
            ing_slug = item.get("ingredient")
            ing = by_slug.get(ing_slug)
            if ing is None:
                errors.append(
                    f"Recipe '{rslug}' references unknown ingredient '{ing_slug}'"
                )
                continue
            unit_weights = {u["label"]: u["grams"] for u in ing.get("units", [])}
            try:
                grams_for_quantity(
                    item.get("quantity", 0), item.get("unit_label", ""), unit_weights
                )
            except KeyError:
                errors.append(
                    f"Recipe '{rslug}' uses unit '{item.get('unit_label')}' for "
                    f"'{ing_slug}', which has units {sorted(unit_weights)} "
                    f"(plus g/kg/100g)"
                )

    if errors:
        raise ValueError(
            "Seed data validation failed:\n  - " + "\n  - ".join(errors)
        )


def _load_json(name: str) -> list[dict]:
    with open(SEED_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def _wipe(db: Session) -> None:
    # Delete children before parents to respect FK constraints.
    db.query(RecipeIngredient).delete()
    db.query(Recipe).delete()
    db.query(NutritionFacts).delete()
    db.query(IngredientUnit).delete()
    db.query(Ingredient).delete()
    db.commit()


def _load_ingredients(db: Session, data: list[dict]) -> dict[str, int]:
    slug_to_id: dict[str, int] = {}
    for row in data:
        ing = Ingredient(
            slug=row["slug"],
            name=row["name"],
            aliases=row.get("aliases", []),
            category=row["category"],
            default_unit=row.get("default_unit", "100g"),
            default_form=row.get("default_form", "raw"),
            tags=row.get("tags", []),
        )
        for f in row.get("facts", []):
            ing.facts.append(NutritionFacts(**f))
        for u in row.get("units", []):
            ing.units.append(IngredientUnit(**u))
        db.add(ing)
        db.flush()  # assign PK
        slug_to_id[ing.slug] = ing.id
    db.commit()
    return slug_to_id


def _load_recipes(db: Session, data: list[dict], slug_to_id: dict[str, int]) -> None:
    for row in data:
        recipe = Recipe(
            slug=row["slug"],
            name=row["name"],
            aliases=row.get("aliases", []),
            meal_type=row["meal_type"],
            base_servings=row.get("base_servings", 1),
            prep_time_min=row.get("prep_time_min"),
            instructions=row.get("instructions"),
            tags=row.get("tags", []),
        )
        for item in row.get("items", []):
            ing_slug = item["ingredient"]
            if ing_slug not in slug_to_id:
                raise ValueError(
                    f"Recipe '{row['slug']}' references unknown ingredient "
                    f"'{ing_slug}'"
                )
            recipe.items.append(
                RecipeIngredient(
                    ingredient_id=slug_to_id[ing_slug],
                    quantity=item["quantity"],
                    unit_label=item["unit_label"],
                    form=item.get("form", "raw"),
                    note=item.get("note"),
                )
            )
        db.add(recipe)
    db.commit()


def run() -> None:
    db = SessionLocal()
    try:
        ingredients = _load_json("ingredients.json")
        recipes = _load_json("recipes.json")
        _validate(ingredients, recipes)
        _wipe(db)
        slug_to_id = _load_ingredients(db, ingredients)
        _load_recipes(db, recipes, slug_to_id)
        print(
            f"Seeded {len(ingredients)} ingredients and {len(recipes)} recipes."
        )
    finally:
        db.close()


if __name__ == "__main__":
    run()
