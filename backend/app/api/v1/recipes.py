from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.models import Ingredient, Recipe
from app.models.recipe import RecipeIngredient
from app.db.session import get_db
from app.schemas.ingredient import MacrosOut
from app.schemas.recipe import RecipeDetail, RecipeSummary, ScaledIngredient
from app.services import ai_lookup, search
from app.services.ai_lookup import GeminiError
from app.services.ai_persist import upsert_ai_recipe
from app.services.ai_validation import ValidationError, validate_recipe
from app.services.nutrition import (
    Macros,
    grams_for_quantity,
    macros_for_grams,
    sum_macros,
)

router = APIRouter(prefix="/recipes", tags=["recipes"])


def _macros_out(m: Macros) -> MacrosOut:
    r = m.rounded()
    return MacrosOut(
        calories=r.calories,
        protein_g=r.protein_g,
        fiber_g=r.fiber_g,
        carbs_g=r.carbs_g,
        fat_g=r.fat_g,
    )


def _per_100g_for(item: RecipeIngredient) -> Macros:
    """Pick the nutrition facts matching the line's form, falling back to any
    available form if the exact one is missing."""
    facts_by_form = {f.form: f for f in item.ingredient.facts}
    facts = facts_by_form.get(item.form) or next(iter(facts_by_form.values()), None)
    if facts is None:
        raise HTTPException(
            status_code=500,
            detail=f"Ingredient '{item.ingredient.slug}' has no nutrition data",
        )
    return Macros(
        calories=facts.calories,
        protein_g=facts.protein_g,
        fiber_g=facts.fiber_g,
        carbs_g=facts.carbs_g,
        fat_g=facts.fat_g,
    )


def _load_all(db: Session) -> list[Recipe]:
    stmt = select(Recipe).options(selectinload(Recipe.items))
    return list(db.scalars(stmt).all())


def _get_one(db: Session, id_or_slug: str) -> Recipe:
    stmt = select(Recipe).options(
        selectinload(Recipe.items)
        .selectinload(RecipeIngredient.ingredient)
        .selectinload(Ingredient.facts),
        selectinload(Recipe.items)
        .selectinload(RecipeIngredient.ingredient)
        .selectinload(Ingredient.units),
    )
    if id_or_slug.isdigit():
        stmt = stmt.where(Recipe.id == int(id_or_slug))
    else:
        stmt = stmt.where(Recipe.slug == id_or_slug)
    recipe = db.scalars(stmt).first()
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@router.get("/search", response_model=list[RecipeSummary])
def search_recipes(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[RecipeSummary]:
    items = _load_all(db)
    ranked = search.rank(
        q, items, searchable=lambda r: [r.name, *r.aliases], limit=limit
    )
    return [
        RecipeSummary(
            id=r.id,
            slug=r.slug,
            name=r.name,
            meal_type=r.meal_type,
            prep_time_min=r.prep_time_min,
            tags=r.tags,
            aliases=r.aliases,
        )
        for r in ranked
    ]


def _detail_for(recipe: Recipe, servings: int) -> RecipeDetail:
    scaled_items: list[ScaledIngredient] = []
    per_serving_macros: list[Macros] = []

    for item in recipe.items:
        ing = item.ingredient
        unit_weights = {u.label: u.grams for u in ing.units}
        try:
            grams_one = grams_for_quantity(item.quantity, item.unit_label, unit_weights)
        except KeyError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        per_100g = _per_100g_for(item)
        macros_one = macros_for_grams(per_100g, grams_one)
        per_serving_macros.append(macros_one)

        scaled_items.append(
            ScaledIngredient(
                ingredient_id=ing.id,
                slug=ing.slug,
                name=ing.name,
                quantity=round(item.quantity * servings, 2),
                unit_label=item.unit_label,
                form=item.form,
                grams=round(grams_one * servings, 1),
                note=item.note,
                nutrition=_macros_out(macros_one.scaled(servings)),
            )
        )

    per_person = sum_macros(per_serving_macros)
    total = per_person.scaled(servings)

    return RecipeDetail(
        id=recipe.id,
        slug=recipe.slug,
        name=recipe.name,
        meal_type=recipe.meal_type,
        prep_time_min=recipe.prep_time_min,
        instructions=recipe.instructions,
        tags=recipe.tags,
        aliases=recipe.aliases,
        servings=servings,
        items=scaled_items,
        per_person=_macros_out(per_person),
        total=_macros_out(total),
        source=recipe.source,
    )


@router.get("/ai", response_model=RecipeDetail)
def ai_lookup_recipe(
    q: str = Query(..., min_length=1, description="Dish name not found in the DB"),
    servings: int = Query(1, ge=1, le=100),
    db: Session = Depends(get_db),
) -> RecipeDetail:
    """Fallback: ask Gemini for a dish we don't have, validate it (and every
    ingredient it uses), store it (source='ai'), and return it scaled."""
    existing = search.rank(
        q, _load_all(db), searchable=lambda r: [r.name, *r.aliases],
        limit=1, threshold=0.6,
    )
    if existing:
        return _detail_for(_get_one(db, existing[0].slug), servings)

    if not get_settings().ai_enabled:
        raise HTTPException(status_code=503, detail="AI lookup is not configured.")

    try:
        raw = ai_lookup.lookup_recipe(q)
    except GeminiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    try:
        validated = validate_recipe(raw)
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Couldn't find reliable data for '{q}': {exc}",
        ) from exc

    recipe = upsert_ai_recipe(db, validated)
    db.commit()
    return _detail_for(_get_one(db, recipe.slug), servings)


@router.get("/{id_or_slug}", response_model=RecipeDetail)
def get_recipe(
    id_or_slug: str,
    servings: int = Query(1, ge=1, le=100, description="Number of people"),
    db: Session = Depends(get_db),
) -> RecipeDetail:
    return _detail_for(_get_one(db, id_or_slug), servings)
