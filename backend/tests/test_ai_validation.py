"""Unit tests for the AI data validators (pure, no network or DB)."""

import copy

import pytest

from app.services.ai_validation import (
    ValidationError,
    validate_ingredient,
    validate_recipe,
)


def good_ingredient():
    return {
        "is_food": True,
        "is_vegetarian": True,
        "name": "Dragon Fruit",
        "category": "fruit",
        "aliases": ["pitaya"],
        "default_unit": "piece",
        "default_form": "raw",
        "units": [{"label": "piece", "grams": 300}, {"label": "cup", "grams": 200}],
        # 4*1.1 + 4*13 + 9*0.4 = 60.0 ~ 60 cal: consistent
        "facts": [
            {"form": "raw", "calories": 60, "protein_g": 1.1, "fiber_g": 3.0,
             "carbs_g": 13.0, "fat_g": 0.4}
        ],
    }


def test_valid_ingredient_passes():
    clean = validate_ingredient(good_ingredient())
    assert clean["slug"] == "dragon-fruit"
    assert clean["default_form"] == "raw"
    assert {u["label"] for u in clean["units"]} == {"piece", "cup"}


def test_non_food_rejected():
    p = good_ingredient()
    p["is_food"] = False
    with pytest.raises(ValidationError):
        validate_ingredient(p)


def test_non_vegetarian_rejected():
    p = good_ingredient()
    p["is_vegetarian"] = False
    with pytest.raises(ValidationError):
        validate_ingredient(p)


def test_calorie_macro_inconsistency_rejected():
    p = good_ingredient()
    p["facts"][0]["calories"] = 500  # macros imply ~60
    with pytest.raises(ValidationError):
        validate_ingredient(p)


def test_impossible_macro_rejected():
    p = good_ingredient()
    p["facts"][0]["protein_g"] = 250  # > 100 g per 100 g
    with pytest.raises(ValidationError):
        validate_ingredient(p)


def test_implausible_unit_grams_rejected():
    p = good_ingredient()
    p["units"] = [{"label": "piece", "grams": -5}]
    p["default_unit"] = "g"
    with pytest.raises(ValidationError):
        validate_ingredient(p)


def test_implicit_units_are_dropped():
    p = good_ingredient()
    p["units"] = [{"label": "g", "grams": 1}, {"label": "piece", "grams": 300}]
    clean = validate_ingredient(p)
    assert {u["label"] for u in clean["units"]} == {"piece"}


def good_recipe():
    return {
        "is_recipe": True,
        "is_vegetarian": True,
        "name": "Test Khichdi",
        "aliases": [],
        "meal_type": "lunch",
        "prep_time_min": 25,
        "instructions": "Cook rice and dal together.",
        "tags": ["high_protein"],
        "items": [
            {"ingredient_name": "Rice", "quantity": 50, "unit_label": "g", "form": "raw"},
            {"ingredient_name": "Moong Dal", "quantity": 30, "unit_label": "g", "form": "raw"},
        ],
        "ingredients": [
            {"is_food": True, "is_vegetarian": True, "name": "Rice", "category": "grain",
             "aliases": [], "default_unit": "g", "default_form": "raw", "units": [],
             "facts": [{"form": "raw", "calories": 360, "protein_g": 7.0, "fiber_g": 1.0,
                        "carbs_g": 79.0, "fat_g": 0.6}]},
            {"is_food": True, "is_vegetarian": True, "name": "Moong Dal", "category": "dal",
             "aliases": [], "default_unit": "g", "default_form": "raw", "units": [],
             "facts": [{"form": "raw", "calories": 348, "protein_g": 24.0, "fiber_g": 16.0,
                        "carbs_g": 59.0, "fat_g": 1.2}]},
        ],
    }


def test_valid_recipe_passes():
    out = validate_recipe(good_recipe())
    assert out["recipe"]["slug"] == "test-khichdi"
    assert len(out["recipe"]["items"]) == 2
    assert "vegetarian" in [t.lower() for t in out["recipe"]["tags"]]


def test_recipe_with_unresolvable_unit_rejected():
    p = good_recipe()
    # 'katori' is not in Rice's units (which are empty) and isn't implicit.
    p["items"][0]["unit_label"] = "katori"
    with pytest.raises(ValidationError):
        validate_recipe(p)


def test_recipe_item_without_ingredient_entry_rejected():
    p = good_recipe()
    p["items"].append(
        {"ingredient_name": "Ghee", "quantity": 1, "unit_label": "g", "form": "raw"}
    )
    with pytest.raises(ValidationError):
        validate_recipe(p)


def test_non_veg_recipe_rejected():
    p = good_recipe()
    p["is_vegetarian"] = False
    with pytest.raises(ValidationError):
        validate_recipe(p)
