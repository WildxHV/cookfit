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

SEED_DIR = Path(__file__).resolve().parent


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
        _wipe(db)
        ingredients = _load_json("ingredients.json")
        recipes = _load_json("recipes.json")
        slug_to_id = _load_ingredients(db, ingredients)
        _load_recipes(db, recipes, slug_to_id)
        print(
            f"Seeded {len(ingredients)} ingredients and {len(recipes)} recipes."
        )
    finally:
        db.close()


if __name__ == "__main__":
    run()
