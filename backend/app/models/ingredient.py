from sqlalchemy import JSON, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Ingredient(Base):
    """A conceptual food item (e.g. "Moong dal", "Paneer", "Roti").

    Nutrition is stored canonically per 100g in `nutrition_facts` (one row per
    form: raw / cooked). `units` holds the gram-weight of common household
    measures so any quantity can be converted to grams and scaled.
    """

    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    # List of alternate names ("chole", "chana", "chickpea"). JSON => portable
    # across SQLite (dev) and Postgres (prod).
    aliases: Mapped[list[str]] = mapped_column(JSON, default=list)
    category: Mapped[str] = mapped_column(String(60), index=True)
    # Sensible defaults for the UI.
    default_unit: Mapped[str] = mapped_column(String(40), default="100g")
    default_form: Mapped[str] = mapped_column(String(20), default="raw")
    # Provenance: "seed" (curated) or "ai" (Gemini lookup, validated).
    source: Mapped[str] = mapped_column(String(20), default="seed", index=True)

    facts: Mapped[list["NutritionFacts"]] = relationship(
        back_populates="ingredient",
        cascade="all, delete-orphan",
    )
    units: Mapped[list["IngredientUnit"]] = relationship(
        back_populates="ingredient",
        cascade="all, delete-orphan",
    )


class NutritionFacts(Base):
    """Canonical nutrition for an ingredient, per 100g, for a given form."""

    __tablename__ = "nutrition_facts"
    __table_args__ = (
        UniqueConstraint("ingredient_id", "form", name="uq_facts_ingredient_form"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id", ondelete="CASCADE"), index=True
    )
    form: Mapped[str] = mapped_column(String(20), default="raw")  # raw | cooked

    # All values are per 100 grams.
    calories: Mapped[float] = mapped_column(Float)
    protein_g: Mapped[float] = mapped_column(Float)
    fiber_g: Mapped[float] = mapped_column(Float)
    carbs_g: Mapped[float] = mapped_column(Float)
    fat_g: Mapped[float] = mapped_column(Float)

    ingredient: Mapped["Ingredient"] = relationship(back_populates="facts")


class IngredientUnit(Base):
    """A household measure for an ingredient and how many grams it weighs.

    A 1g unit and a 100g unit are always available implicitly (handled in the
    nutrition service); this table holds the non-trivial ones like "katori",
    "cup", "piece", "tbsp".
    """

    __tablename__ = "ingredient_units"
    __table_args__ = (
        UniqueConstraint("ingredient_id", "label", name="uq_unit_ingredient_label"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id", ondelete="CASCADE"), index=True
    )
    label: Mapped[str] = mapped_column(String(40))
    grams: Mapped[float] = mapped_column(Float)

    ingredient: Mapped["Ingredient"] = relationship(back_populates="units")
