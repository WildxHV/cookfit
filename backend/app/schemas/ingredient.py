from pydantic import BaseModel


class MacrosOut(BaseModel):
    calories: float
    protein_g: float
    fiber_g: float
    carbs_g: float
    fat_g: float


class UnitOut(BaseModel):
    label: str
    grams: float


class IngredientSummary(BaseModel):
    """Lightweight result for search lists."""

    id: int
    slug: str
    name: str
    category: str
    aliases: list[str]


class SelectedNutrition(BaseModel):
    """The nutrition for the specifically requested quantity/unit/form."""

    quantity: float
    unit: str
    form: str
    grams: float
    nutrition: MacrosOut


class IngredientDetail(BaseModel):
    """Everything the lookup screen needs, including per-100g facts and unit
    weights so the client can recalculate live without a round-trip."""

    id: int
    slug: str
    name: str
    category: str
    aliases: list[str]
    default_unit: str
    default_form: str
    forms: list[str]
    units: list[UnitOut]
    facts_per_100g: dict[str, MacrosOut]  # keyed by form: "raw" / "cooked"
    selected: SelectedNutrition
