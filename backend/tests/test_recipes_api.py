"""Integration tests for the recipe API against the seeded dev DB."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_search_recipe_by_alias():
    r = client.get("/api/v1/recipes/search", params={"q": "dal fry"})
    assert r.status_code == 200
    slugs = [x["slug"] for x in r.json()]
    assert "moong-dal-tadka" in slugs


def test_recipe_default_one_serving():
    r = client.get("/api/v1/recipes/moong-dal-tadka")
    assert r.status_code == 200
    body = r.json()
    assert body["servings"] == 1
    # per_person == total when servings == 1
    assert body["per_person"]["calories"] == body["total"]["calories"]
    assert len(body["items"]) == 7


def test_recipe_scales_linearly():
    one = client.get("/api/v1/recipes/rajma-masala").json()
    four = client.get(
        "/api/v1/recipes/rajma-masala", params={"servings": 4}
    ).json()
    # Per-person nutrition is invariant to servings.
    assert one["per_person"]["calories"] == four["per_person"]["calories"]
    # Total scales by 4 (allow rounding slack).
    assert abs(four["total"]["calories"] - one["per_person"]["calories"] * 4) <= 4
    # Ingredient quantities scale by 4.
    one_item = next(i for i in one["items"] if i["slug"] == "rajma")
    four_item = next(i for i in four["items"] if i["slug"] == "rajma")
    assert abs(four_item["quantity"] - one_item["quantity"] * 4) < 0.01


def test_total_equals_sum_of_item_nutrition():
    body = client.get(
        "/api/v1/recipes/palak-paneer", params={"servings": 3}
    ).json()
    cal_sum = sum(i["nutrition"]["calories"] for i in body["items"])
    # Item nutrition is already scaled to servings; should match total (rounding).
    assert abs(cal_sum - body["total"]["calories"]) <= len(body["items"])


def test_unknown_recipe_404():
    r = client.get("/api/v1/recipes/no-such-dish")
    assert r.status_code == 404
