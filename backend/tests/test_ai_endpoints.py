"""Tests for the AI fallback endpoints with the Gemini call mocked out.

No network is hit. Any rows inserted into the dev DB are cleaned up afterward.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.main import app
from app.models import Ingredient, Recipe
from app.services import ai_lookup

client = TestClient(app)


@pytest.fixture(autouse=True)
def _enable_ai(monkeypatch):
    # Ensure the AI path is enabled regardless of the local .env.
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _delete_ingredient(slug: str):
    db = SessionLocal()
    try:
        ing = db.scalars(select(Ingredient).where(Ingredient.slug == slug)).first()
        if ing:
            db.delete(ing)
            db.commit()
    finally:
        db.close()


def _delete_recipe(slug: str, ingredient_slugs: list[str]):
    db = SessionLocal()
    try:
        rec = db.scalars(select(Recipe).where(Recipe.slug == slug)).first()
        if rec:
            db.delete(rec)
            db.commit()
        for s in ingredient_slugs:
            ing = db.scalars(select(Ingredient).where(Ingredient.slug == s)).first()
            if ing and ing.source == "ai":
                db.delete(ing)
        db.commit()
    finally:
        db.close()


FAKE_INGREDIENT = {
    "is_food": True, "is_vegetarian": True, "name": "Zztest Berry",
    "category": "fruit", "aliases": [], "default_unit": "cup", "default_form": "raw",
    "units": [{"label": "cup", "grams": 150}],
    "facts": [{"form": "raw", "calories": 57, "protein_g": 0.7, "fiber_g": 2.4,
               "carbs_g": 14.0, "fat_g": 0.3}],
}


def test_ai_ingredient_inserts_and_tags_source():
    monkey_called = {"n": 0}

    def fake(q):
        monkey_called["n"] += 1
        return FAKE_INGREDIENT

    import app.api.v1.ingredients as mod
    mod.ai_lookup.lookup_ingredient = fake  # type: ignore
    try:
        r = client.get("/api/v1/ingredients/ai", params={"q": "zzqqxx novel fruit"})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["source"] == "ai"
        assert body["name"] == "Zztest Berry"
        assert monkey_called["n"] == 1
        # Now stored: a normal lookup should find it.
        r2 = client.get("/api/v1/ingredients/zztest-berry")
        assert r2.status_code == 200
        assert r2.json()["source"] == "ai"
    finally:
        mod.ai_lookup.lookup_ingredient = ai_lookup.lookup_ingredient  # type: ignore
        _delete_ingredient("zztest-berry")


def test_ai_ingredient_rejects_non_vegetarian():
    def fake(q):
        p = dict(FAKE_INGREDIENT)
        p["is_vegetarian"] = False
        return p

    import app.api.v1.ingredients as mod
    mod.ai_lookup.lookup_ingredient = fake  # type: ignore
    try:
        r = client.get("/api/v1/ingredients/ai", params={"q": "zzqqxx chicken thing"})
        assert r.status_code == 422
    finally:
        mod.ai_lookup.lookup_ingredient = ai_lookup.lookup_ingredient  # type: ignore


FAKE_RECIPE = {
    "is_recipe": True, "is_vegetarian": True, "name": "Zztest Pulao",
    "aliases": [], "meal_type": "lunch", "prep_time_min": 30,
    "instructions": "Cook it.", "tags": ["vegetarian"],
    "items": [
        {"ingredient_name": "Zztest Rice", "quantity": 60, "unit_label": "g", "form": "raw"},
    ],
    "ingredients": [
        {"is_food": True, "is_vegetarian": True, "name": "Zztest Rice", "category": "grain",
         "aliases": [], "default_unit": "g", "default_form": "raw", "units": [],
         "facts": [{"form": "raw", "calories": 360, "protein_g": 7.0, "fiber_g": 1.0,
                    "carbs_g": 79.0, "fat_g": 0.6}]},
    ],
}


def test_ai_recipe_inserts_recipe_and_missing_ingredients():
    def fake(q):
        return FAKE_RECIPE

    import app.api.v1.recipes as mod
    mod.ai_lookup.lookup_recipe = fake  # type: ignore
    try:
        r = client.get("/api/v1/recipes/ai", params={"q": "zzqqxx novel pulao"})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["source"] == "ai"
        assert body["per_person"]["calories"] > 0
        assert len(body["items"]) == 1
    finally:
        mod.ai_lookup.lookup_recipe = ai_lookup.lookup_recipe  # type: ignore
        _delete_recipe("zztest-pulao", ["zztest-rice"])
