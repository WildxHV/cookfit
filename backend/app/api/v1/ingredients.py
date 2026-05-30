from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models import Ingredient
from app.schemas.ingredient import (
    IngredientDetail,
    IngredientSummary,
    MacrosOut,
    SelectedNutrition,
    UnitOut,
)
from app.services import search
from app.services.nutrition import Macros, grams_for_quantity, macros_for_grams

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


def _facts_to_macros(facts) -> Macros:
    return Macros(
        calories=facts.calories,
        protein_g=facts.protein_g,
        fiber_g=facts.fiber_g,
        carbs_g=facts.carbs_g,
        fat_g=facts.fat_g,
    )


def _macros_out(m: Macros) -> MacrosOut:
    r = m.rounded()
    return MacrosOut(
        calories=r.calories,
        protein_g=r.protein_g,
        fiber_g=r.fiber_g,
        carbs_g=r.carbs_g,
        fat_g=r.fat_g,
    )


def _load_all(db: Session) -> list[Ingredient]:
    stmt = select(Ingredient).options(
        selectinload(Ingredient.facts), selectinload(Ingredient.units)
    )
    return list(db.scalars(stmt).all())


def _get_one(db: Session, id_or_slug: str) -> Ingredient:
    stmt = select(Ingredient).options(
        selectinload(Ingredient.facts), selectinload(Ingredient.units)
    )
    if id_or_slug.isdigit():
        stmt = stmt.where(Ingredient.id == int(id_or_slug))
    else:
        stmt = stmt.where(Ingredient.slug == id_or_slug)
    ing = db.scalars(stmt).first()
    if ing is None:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return ing


@router.get("/search", response_model=list[IngredientSummary])
def search_ingredients(
    q: str = Query(..., min_length=1, description="Search text"),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[IngredientSummary]:
    items = _load_all(db)
    ranked = search.rank(
        q, items, searchable=lambda i: [i.name, *i.aliases], limit=limit
    )
    return [
        IngredientSummary(
            id=i.id, slug=i.slug, name=i.name, category=i.category, aliases=i.aliases
        )
        for i in ranked
    ]


@router.get("/{id_or_slug}", response_model=IngredientDetail)
def get_ingredient(
    id_or_slug: str,
    quantity: float = Query(1.0, ge=0, description="Amount in the chosen unit"),
    unit: str | None = Query(None, description="Unit label; defaults to ingredient default"),
    form: str | None = Query(None, description="raw | cooked; defaults to ingredient default"),
    db: Session = Depends(get_db),
) -> IngredientDetail:
    ing = _get_one(db, id_or_slug)

    facts_by_form = {f.form: f for f in ing.facts}
    forms = sorted(facts_by_form.keys())
    if not forms:
        raise HTTPException(status_code=500, detail="Ingredient has no nutrition data")

    chosen_form = form or ing.default_form
    if chosen_form not in facts_by_form:
        chosen_form = forms[0]

    chosen_unit = unit or ing.default_unit
    unit_weights = {u.label: u.grams for u in ing.units}

    try:
        grams = grams_for_quantity(quantity, chosen_unit, unit_weights)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    per_100g = _facts_to_macros(facts_by_form[chosen_form])
    selected_macros = macros_for_grams(per_100g, grams)

    return IngredientDetail(
        id=ing.id,
        slug=ing.slug,
        name=ing.name,
        category=ing.category,
        aliases=ing.aliases,
        default_unit=ing.default_unit,
        default_form=ing.default_form,
        forms=forms,
        units=[UnitOut(label=u.label, grams=u.grams) for u in ing.units],
        facts_per_100g={
            f: _macros_out(_facts_to_macros(facts_by_form[f])) for f in forms
        },
        selected=SelectedNutrition(
            quantity=quantity,
            unit=chosen_unit,
            form=chosen_form,
            grams=round(grams, 1),
            nutrition=_macros_out(selected_macros),
        ),
    )
