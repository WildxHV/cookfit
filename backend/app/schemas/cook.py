from pydantic import BaseModel, Field


class SuggestRequest(BaseModel):
    """Ingredients the user has on hand."""

    ingredients: list[str] = Field(default_factory=list)


class DishSuggestion(BaseModel):
    """A dish idea the user can cook from their ingredients."""

    name: str
    kind: str = "authentic"  # "authentic" | "fusion"
    description: str = ""
    uses: list[str] = []        # which of the user's ingredients it uses
    pantry: list[str] = []      # assumed pantry staples it relies on
    steps: list[str] = []
    tags: list[str] = []


class CatalogMatch(BaseModel):
    """A recipe already in our catalog that the user can (mostly) make now."""

    slug: str
    name: str
    meal_type: str
    have: list[str] = []        # required ingredients the user has
    missing: list[str] = []     # required ingredients still needed (non-pantry)


class SuggestResponse(BaseModel):
    ideas: list[DishSuggestion] = []
    from_catalog: list[CatalogMatch] = []
    ai_error: str | None = None  # set if idea generation was unavailable
