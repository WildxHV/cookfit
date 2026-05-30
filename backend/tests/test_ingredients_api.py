"""Integration tests for the ingredient API against the seeded dev DB.

These assume the dev database has been seeded (`python -m app.seed.seed`).
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_search_finds_by_alias():
    # "chana"/"chickpea" are aliases of chole.
    r = client.get("/api/v1/ingredients/search", params={"q": "chana"})
    assert r.status_code == 200
    slugs = [i["slug"] for i in r.json()]
    assert "chole" in slugs


def test_search_fuzzy_typo():
    r = client.get("/api/v1/ingredients/search", params={"q": "paner"})
    assert r.status_code == 200
    slugs = [i["slug"] for i in r.json()]
    assert "paneer" in slugs


def test_get_by_slug_default():
    r = client.get("/api/v1/ingredients/paneer")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Paneer"
    assert body["selected"]["unit"] == "katori"
    # 1 katori = 100g of paneer -> ~296 kcal.
    assert abs(body["selected"]["nutrition"]["calories"] - 296) < 1


def test_get_with_quantity_and_unit():
    # 2 katori of moong dal cooked = 300g; cooked 105 kcal/100g -> 315.
    r = client.get(
        "/api/v1/ingredients/moong-dal",
        params={"quantity": 2, "unit": "katori", "form": "cooked"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["selected"]["grams"] == 300
    assert abs(body["selected"]["nutrition"]["calories"] - 315) < 1


def test_raw_cooked_forms_available():
    r = client.get("/api/v1/ingredients/moong-dal")
    forms = r.json()["forms"]
    assert "raw" in forms and "cooked" in forms


def test_unknown_unit_is_400():
    r = client.get("/api/v1/ingredients/paneer", params={"unit": "scoop"})
    assert r.status_code == 400


def test_unknown_ingredient_is_404():
    r = client.get("/api/v1/ingredients/does-not-exist")
    assert r.status_code == 404
