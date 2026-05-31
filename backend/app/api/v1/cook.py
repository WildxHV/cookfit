import logging

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.db.session import SessionLocal, get_db
from app.models import Ingredient, Recipe
from app.schemas.cook import (
    CatalogMatch,
    DishSuggestion,
    SuggestRequest,
    SuggestResponse,
)
from app.services import ai_lookup, ai_suggest, search
from app.services.ai_lookup import GeminiError
from app.services.ai_persist import upsert_ai_ingredient, upsert_ai_recipe
from app.services.ai_validation import (
    ValidationError,
    validate_ingredient,
    validate_recipe,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cook", tags=["cook"])

# Skip an AI fetch when we already have a near-certain match for the name.
_DEDUPE_THRESHOLD = 0.85

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


def _avoided(text: str, avoid_terms: list[str]) -> bool:
    """True if `text` (an ingredient/dish name) matches anything to avoid.

    Aggressive on purpose — better to drop a borderline match than serve an
    allergen: matches on case-insensitive substring or a strong fuzzy score.
    """
    low = text.lower()
    for a in avoid_terms:
        al = a.lower().strip()
        if not al:
            continue
        if al in low or low in al or search.score_query(a, [text]) >= 0.8:
            return True
    return False


def _unmatched_terms(user_terms: list[str], ingredients: list[Ingredient]) -> list[str]:
    """User terms that don't match any catalog ingredient (candidates to fetch)."""
    unmatched: list[str] = []
    for t in (t.strip() for t in user_terms if t.strip()):
        cands_hit = any(
            search.score_query(t, [i.name, *i.aliases]) >= _HAVE_THRESHOLD
            for i in ingredients
        )
        if not cands_hit:
            unmatched.append(t)
    return unmatched


# --- Background catalog-building -------------------------------------------
# When a user mentions ingredients we don't have, or we suggest dishes, we fetch
# the full validated data from Gemini and store it — so the catalog grows from
# real usage. To keep API usage low this is just TWO calls total: one batch for
# all the unknown ingredients, one batch for all the suggested recipes. These
# run AFTER the response is sent and never raise; the same strict validators as
# the lookup endpoints gate every write.

def _not_already_stored(db: Session, names: list[str], model) -> list[str]:
    """Drop names we already have a near-certain match for (avoids re-fetching)."""
    existing = list(db.scalars(select(model)).all())
    keep: list[str] = []
    for n in names:
        hit = search.rank(
            n, existing, searchable=lambda x: [x.name, *x.aliases],
            limit=1, threshold=_DEDUPE_THRESHOLD,
        )
        if not hit:
            keep.append(n)
    return keep


def _persist_ingredients_bg(terms: list[str]) -> None:
    db = SessionLocal()
    try:
        todo = _not_already_stored(db, terms, Ingredient)
        if not todo:
            return
        for raw in ai_lookup.lookup_ingredients(todo):
            try:
                clean = validate_ingredient(raw)
                upsert_ai_ingredient(db, clean)
                logger.info("cook: stored AI ingredient %r", clean["slug"])
            except ValidationError as exc:
                logger.info("cook: skipped an ingredient: %s", exc)
        db.commit()
    except GeminiError as exc:
        db.rollback()
        logger.info("cook: ingredient batch failed: %s", exc)
    except Exception:  # never let a background task crash the worker
        db.rollback()
        logger.exception("cook: ingredient batch persist failed")
    finally:
        db.close()


def _persist_recipes_bg(names: list[str]) -> None:
    db = SessionLocal()
    try:
        todo = _not_already_stored(db, names, Recipe)
        if not todo:
            return
        for raw in ai_lookup.lookup_recipes(todo):
            try:
                validated = validate_recipe(raw)
                upsert_ai_recipe(db, validated)
                logger.info("cook: stored AI recipe %r", validated["recipe"]["slug"])
            except ValidationError as exc:
                logger.info("cook: skipped a recipe: %s", exc)
        db.commit()
    except GeminiError as exc:
        db.rollback()
        logger.info("cook: recipe batch failed: %s", exc)
    except Exception:
        db.rollback()
        logger.exception("cook: recipe batch persist failed")
    finally:
        db.close()


def _catalog_matches(
    db: Session, user_terms: list[str], avoid: list[str], limit: int = 8
) -> list[CatalogMatch]:
    """Catalog recipes makeable (or nearly) from the user's ingredients + pantry,
    excluding any recipe that contains an avoided ingredient."""
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
        # Drop recipes containing anything the user avoids.
        if avoid and any(
            _avoided(name_by_slug.get(s, s), avoid) for s in req_slugs
        ):
            continue
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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> SuggestResponse:
    """Given the ingredients a user has, suggest dishes to make.

    Combines creative AI ideas (authentic + fusion) with catalog recipes that
    are already (nearly) makeable from those ingredients plus pantry staples.
    As a side effect, the catalog grows from usage: ingredients the user
    mentioned but we don't have, and the dishes we suggest, are fetched and
    stored in the background (validated the same way as the lookup endpoints).
    """
    terms = [t.strip() for t in body.ingredients if t.strip()]
    avoid = [a.strip() for a in body.avoid if a.strip()]
    from_catalog = _catalog_matches(db, terms, avoid)

    ideas: list[DishSuggestion] = []
    ai_error: str | None = None
    if not terms:
        ai_error = "Add a few ingredients to get suggestions."
    elif not get_settings().ai_enabled:
        ai_error = "Idea generation isn't configured on the server."
    else:
        try:
            raw = ai_suggest.suggest_dishes(terms, avoid)
            ideas = [DishSuggestion(**s) for s in raw]
            # Defensive: drop any idea that slipped an avoided item into name/uses.
            if avoid:
                ideas = [
                    d for d in ideas
                    if not _avoided(d.name, avoid)
                    and not any(_avoided(u, avoid) for u in d.uses)
                ]
        except GeminiError:
            ai_error = "Couldn't generate ideas right now. Please try again."

    # Grow the catalog in the background (no effect on this response). Just two
    # batched Gemini calls: one for all unknown ingredients, one for all ideas.
    if get_settings().ai_enabled and terms:
        ingredients = list(db.scalars(select(Ingredient)).all())
        unknown = _unmatched_terms(terms, ingredients)
        if unknown:
            background_tasks.add_task(_persist_ingredients_bg, unknown)
        idea_names = [i.name for i in ideas[:6]]
        if idea_names:
            background_tasks.add_task(_persist_recipes_bg, idea_names)

    return SuggestResponse(ideas=ideas, from_catalog=from_catalog, ai_error=ai_error)
