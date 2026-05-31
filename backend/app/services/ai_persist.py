"""Insert validated AI food data into the DB, tagged source='ai'.

All inputs here are assumed to have already passed `ai_validation`. These
helpers only handle de-duplication and persistence.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Ingredient,
    IngredientUnit,
    NutritionFacts,
    Recipe,
    RecipeIngredient,
)


def _unique_slug(db: Session, model, base: str) -> str:
    """Return `base`, or base-2, base-3… if the slug is already taken."""
    slug = base
    n = 1
    while db.scalars(select(model).where(model.slug == slug)).first() is not None:
        n += 1
        slug = f"{base}-{n}"
    return slug


def upsert_ai_ingredient(db: Session, clean: dict) -> Ingredient:
    """Return an existing ingredient with the same slug, else create one."""
    existing = db.scalars(
        select(Ingredient).where(Ingredient.slug == clean["slug"])
    ).first()
    if existing is not None:
        return existing

    ing = Ingredient(
        slug=clean["slug"],
        name=clean["name"],
        aliases=clean["aliases"],
        category=clean["category"],
        default_unit=clean["default_unit"],
        default_form=clean["default_form"],
        tags=clean.get("tags", []),
        source="ai",
    )
    for f in clean["facts"]:
        ing.facts.append(NutritionFacts(**f))
    for u in clean["units"]:
        ing.units.append(IngredientUnit(label=u["label"], grams=u["grams"]))
    db.add(ing)
    db.flush()
    return ing


def upsert_ai_recipe(db: Session, validated: dict) -> Recipe:
    """Ensure all referenced ingredients exist, then create the recipe.

    Returns an existing recipe with the same slug if one is already stored.
    """
    recipe_data = validated["recipe"]
    existing = db.scalars(
        select(Recipe).where(Recipe.slug == recipe_data["slug"])
    ).first()
    if existing is not None:
        return existing

    # Insert/lookup every ingredient first, mapping by the validated name.
    name_to_id: dict[str, int] = {}
    for clean in validated["ingredients"]:
        ing = upsert_ai_ingredient(db, clean)
        name_to_id[clean["name"].lower()] = ing.id

    recipe = Recipe(
        slug=recipe_data["slug"],
        name=recipe_data["name"],
        aliases=recipe_data["aliases"],
        meal_type=recipe_data["meal_type"],
        base_servings=1,
        prep_time_min=recipe_data["prep_time_min"],
        instructions=recipe_data["instructions"],
        tags=recipe_data["tags"],
        source="ai",
    )
    for item in recipe_data["items"]:
        recipe.items.append(
            RecipeIngredient(
                ingredient_id=name_to_id[item["ingredient_name"].lower()],
                quantity=item["quantity"],
                unit_label=item["unit_label"],
                form=item["form"],
                note=item["note"],
            )
        )
    db.add(recipe)
    db.flush()
    return recipe
