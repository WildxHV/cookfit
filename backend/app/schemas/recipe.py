from pydantic import BaseModel

from app.schemas.ingredient import MacrosOut


class RecipeSummary(BaseModel):
    id: int
    slug: str
    name: str
    meal_type: str
    prep_time_min: int | None
    tags: list[str]
    aliases: list[str]


class ScaledIngredient(BaseModel):
    """A recipe line scaled to the requested number of servings."""

    ingredient_id: int
    slug: str
    name: str
    quantity: float
    unit_label: str
    form: str
    grams: float
    note: str | None
    nutrition: MacrosOut


class RecipeDetail(BaseModel):
    id: int
    slug: str
    name: str
    meal_type: str
    prep_time_min: int | None
    instructions: str | None
    tags: list[str]
    aliases: list[str]
    servings: int
    items: list[ScaledIngredient]
    per_person: MacrosOut
    total: MacrosOut
