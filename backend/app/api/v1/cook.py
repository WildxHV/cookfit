from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.db.session import get_db
from app.models import Ingredient, Recipe
from app.models.recipe import RecipeIngredient
from app.schemas.cook import (
    CatalogMatch,
    DishSuggestion,
    SuggestRequest,
    SuggestResponse,
)
from app.services import ai_suggest, search
from app.services.ai_lookup import GeminiError

router = APIRouter(prefix="/cook", tags=["cook"])

# Catalog categories treated as everyday staples the user is assumed to have.
_PANTRY_CATEGORIES = {"spice", "fat", "sweetener", "aromatic"}
_PANTRY_SLUGS = {"onion", "salt", "sugar"}

# How confident a match must be to say "the user has this ingredient". Kept
# high so only exact / prefix / substring name matches count — a loose fuzzy
# ratio (e.g. "pasta" ~ "atta") must not register as a pantry hit.
_HAVE_THRESHOLD = 0.8


def _is_pantry(ing: Ingredient) -> bool:
    return ing.category in _PANTRY_CATEGORIES or ing.slug in _PANTRY_SLUGS


def _have_slugs(user_terms: list[str], ingredients: list[Ingredient]) -> set[str]:
    """Map the user's free-text ingredient terms to catalog ingredient slugs."""
    have: set[str] = set()
    terms = [t.strip() for t in user_terms if t.strip()]
    if not terms:
        return have
    for ing in ingredients:
        candidates = [ing.name, *ing.aliases]
        if any(search.score_query(t, candidates) >= _HAVE_THRESHOLD for t in terms):
            have.add(ing.slug)
    return have


def _catalog_matches(
    db: Session, user_terms: list[str], limit: int = 8
) -> list[CatalogMatch]:
    """Catalog recipes makeable (or nearly) from the user's ingredients + pantry."""
    ingredients = list(
        db.scalars(select(Ingredient).options(selectinload(Ingredient.units))).all()
    )
    have = _have_slugs(user_terms, ingredients)
    if not have:
        return []

    pantry = {i.slug for i in ingredients if _is_pantry(i)}
    name_by_slug = {i.slug: i.name for i in ingredients}
    id_to_slug = {i.id: i.slug for i in ingredients}

    recipes = db.scalars(
        select(Recipe).options(selectinload(Recipe.items))
    ).all()

    scored: list[tuple[int, int, CatalogMatch]] = []
    for r in recipes:
        req_slugs = {
            id_to_slug[it.ingredient_id]
            for it in r.items
            if it.ingredient_id in id_to_slug
        }
        non_pantry = req_slugs - pantry
        if not non_pantry:
            continue
        have_here = sorted(s for s in non_pantry if s in have)
        missing = sorted(s for s in non_pantry if s not in have)
        if not have_here:
            continue
        if len(missing) > 1:  # at most one missing non-pantry ingredient
            continue
        scored.append((
            len(missing),
            -len(have_here),
            CatalogMatch(
                slug=r.slug,
                name=r.name,
                meal_type=r.meal_type,
                have=[name_by_slug.get(s, s) for s in have_here],
                missing=[name_by_slug.get(s, s) for s in missing],
            ),
        ))

    scored.sort(key=lambda t: (t[0], t[1]))
    return [m for _, _, m in scored[:limit]]


@router.post("/suggest", response_model=SuggestResponse)
def suggest(
    body: SuggestRequest,
    db: Session = Depends(get_db),
) -> SuggestResponse:
    """Given the ingredients a user has, suggest dishes to make.

    Combines creative AI ideas (authentic + fusion) with catalog recipes that
    are already (nearly) makeable from those ingredients plus pantry staples.
    """
    terms = [t.strip() for t in body.ingredients if t.strip()]
    from_catalog = _catalog_matches(db, terms)

    ideas: list[DishSuggestion] = []
    ai_error: str | None = None
    if not terms:
        ai_error = "Add a few ingredients to get suggestions."
    elif not get_settings().ai_enabled:
        ai_error = "Idea generation isn't configured on the server."
    else:
        try:
            raw = ai_suggest.suggest_dishes(terms)
            ideas = [DishSuggestion(**s) for s in raw]
        except GeminiError:
            ai_error = "Couldn't generate ideas right now. Please try again."

    return SuggestResponse(ideas=ideas, from_catalog=from_catalog, ai_error=ai_error)
