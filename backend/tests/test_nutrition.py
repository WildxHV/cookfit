import pytest

from app.services.nutrition import (
    Macros,
    grams_for_quantity,
    macros_for_grams,
    macros_for_quantity,
    sum_macros,
)

# Per-100g facts for cooked moong dal (approx, for testing math only).
MOONG = Macros(calories=105, protein_g=7.0, fiber_g=4.0, carbs_g=19.0, fat_g=0.4)


def test_macros_for_grams_scales_linearly():
    m = macros_for_grams(MOONG, 200)
    assert m.calories == pytest.approx(210)
    assert m.protein_g == pytest.approx(14.0)
    assert m.fat_g == pytest.approx(0.8)


def test_macros_for_grams_zero():
    m = macros_for_grams(MOONG, 0)
    assert m == Macros()


def test_macros_for_grams_negative_raises():
    with pytest.raises(ValueError):
        macros_for_grams(MOONG, -10)


def test_add_and_scaled():
    a = Macros(calories=100, protein_g=5)
    b = Macros(calories=50, protein_g=2)
    assert (a + b).calories == 150
    assert a.scaled(3).protein_g == 15


def test_sum_macros_empty():
    assert sum_macros([]) == Macros()


def test_sum_macros_multiple():
    total = sum_macros([Macros(calories=10), Macros(calories=20), Macros(calories=5)])
    assert total.calories == 35


def test_grams_for_quantity_implicit_units():
    assert grams_for_quantity(2, "100g", {}) == 200
    assert grams_for_quantity(250, "g", {}) == 250
    assert grams_for_quantity(1, "kg", {}) == 1000


def test_grams_for_quantity_household_unit():
    weights = {"katori": 150.0, "tbsp": 15.0}
    assert grams_for_quantity(2, "katori", weights) == 300
    assert grams_for_quantity(3, "tbsp", weights) == 45


def test_grams_for_quantity_case_insensitive():
    assert grams_for_quantity(1, "Katori", {"katori": 150.0}) == 150


def test_grams_for_quantity_unknown_unit_raises():
    with pytest.raises(KeyError):
        grams_for_quantity(1, "scoop", {"katori": 150.0})


def test_macros_for_quantity_full_path():
    # 1 katori (150g) of moong dal.
    m = macros_for_quantity(MOONG, 1, "katori", {"katori": 150.0})
    assert m.calories == pytest.approx(157.5)
    assert m.protein_g == pytest.approx(10.5)


def test_rounded():
    m = Macros(calories=157.49, protein_g=10.456, fiber_g=4.0).rounded()
    assert m.calories == 157
    assert m.protein_g == 10.5


def test_recipe_aggregation_per_serving_and_total():
    # A 1-serving dish: 1 katori moong dal + 50g of something at 200kcal/100g.
    other = Macros(calories=200, protein_g=10)
    line1 = macros_for_quantity(MOONG, 1, "katori", {"katori": 150.0})
    line2 = macros_for_grams(other, 50)
    per_serving = sum_macros([line1, line2])
    assert per_serving.calories == pytest.approx(157.5 + 100)
    # Scale to 4 people.
    total = per_serving.scaled(4)
    assert total.calories == pytest.approx(per_serving.calories * 4)
