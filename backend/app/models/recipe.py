from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Recipe(Base):
    """A curated healthy Indian dish.

    Ingredient quantities in `recipe_ingredients` are stored for ONE serving
    (base_servings = 1). Scaling for N people = multiply by N.
    """

    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(140), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(140), index=True)
    aliases: Mapped[list[str]] = mapped_column(JSON, default=list)
    meal_type: Mapped[str] = mapped_column(String(40), index=True)  # breakfast/lunch/...
    base_servings: Mapped[int] = mapped_column(Integer, default=1)
    prep_time_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Tags like "high_protein", "low_cal", "vegan".
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)

    items: Mapped[list["RecipeIngredient"]] = relationship(
        back_populates="recipe",
        cascade="all, delete-orphan",
    )


class RecipeIngredient(Base):
    """One ingredient line in a recipe, quantified for a single serving."""

    __tablename__ = "recipe_ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), index=True
    )
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id", ondelete="RESTRICT"), index=True
    )
    quantity: Mapped[float] = mapped_column(Float)
    unit_label: Mapped[str] = mapped_column(String(40))  # e.g. "katori", "g", "tbsp"
    form: Mapped[str] = mapped_column(String(20), default="raw")  # raw | cooked
    # Free-text note shown to the cook, e.g. "finely chopped".
    note: Mapped[str | None] = mapped_column(String(140), nullable=True)

    recipe: Mapped["Recipe"] = relationship(back_populates="items")
    ingredient: Mapped["Ingredient"] = relationship()
