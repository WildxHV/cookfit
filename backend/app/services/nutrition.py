"""Pure nutrition engine.

No database or framework imports — just numbers in, numbers out — so the math
is trivial to unit-test and is the single source of truth for every feature.

Canonical model: an ingredient's macros are defined PER 100 GRAMS. Any quantity
in any unit is converted to grams, then scaled from the per-100g facts.
"""

from __future__ import annotations

from dataclasses import dataclass

# Rounding precision for display-facing numbers.
_CAL_DP = 0
_MACRO_DP = 1
_GRAM_DP = 1


@dataclass(frozen=True)
class Macros:
    """A bundle of nutrition values. Units: kcal and grams."""

    calories: float = 0.0
    protein_g: float = 0.0
    fiber_g: float = 0.0
    carbs_g: float = 0.0
    fat_g: float = 0.0

    def __add__(self, other: "Macros") -> "Macros":
        return Macros(
            calories=self.calories + other.calories,
            protein_g=self.protein_g + other.protein_g,
            fiber_g=self.fiber_g + other.fiber_g,
            carbs_g=self.carbs_g + other.carbs_g,
            fat_g=self.fat_g + other.fat_g,
        )

    def scaled(self, factor: float) -> "Macros":
        return Macros(
            calories=self.calories * factor,
            protein_g=self.protein_g * factor,
            fiber_g=self.fiber_g * factor,
            carbs_g=self.carbs_g * factor,
            fat_g=self.fat_g * factor,
        )

    def rounded(self) -> "Macros":
        return Macros(
            calories=round(self.calories, _CAL_DP),
            protein_g=round(self.protein_g, _MACRO_DP),
            fiber_g=round(self.fiber_g, _MACRO_DP),
            carbs_g=round(self.carbs_g, _MACRO_DP),
            fat_g=round(self.fat_g, _MACRO_DP),
        )


def sum_macros(items: list[Macros]) -> Macros:
    total = Macros()
    for m in items:
        total = total + m
    return total


def macros_for_grams(per_100g: Macros, grams: float) -> Macros:
    """Scale per-100g facts to an arbitrary gram weight."""
    if grams < 0:
        raise ValueError("grams must be non-negative")
    return per_100g.scaled(grams / 100.0)


# Units whose gram-weight is fixed regardless of ingredient.
_IMPLICIT_UNIT_GRAMS: dict[str, float] = {
    "g": 1.0,
    "gram": 1.0,
    "grams": 1.0,
    "100g": 100.0,
    "kg": 1000.0,
}


def grams_for_quantity(
    quantity: float,
    unit_label: str,
    unit_weights: dict[str, float],
) -> float:
    """Convert `quantity` of `unit_label` into grams.

    `unit_weights` maps an ingredient's household-unit label -> grams per 1 unit
    (from the ingredient_units table). Implicit mass units (g, kg, 100g) are
    always understood. Raises KeyError for an unknown unit.
    """
    if quantity < 0:
        raise ValueError("quantity must be non-negative")
    label = unit_label.strip().lower()
    if label in _IMPLICIT_UNIT_GRAMS:
        return quantity * _IMPLICIT_UNIT_GRAMS[label]
    weights_lower = {k.lower(): v for k, v in unit_weights.items()}
    if label not in weights_lower:
        raise KeyError(f"unknown unit '{unit_label}' for this ingredient")
    return quantity * weights_lower[label]


def macros_for_quantity(
    per_100g: Macros,
    quantity: float,
    unit_label: str,
    unit_weights: dict[str, float],
) -> Macros:
    """Full path: quantity + unit -> grams -> scaled macros."""
    grams = grams_for_quantity(quantity, unit_label, unit_weights)
    return macros_for_grams(per_100g, grams)
