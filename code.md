# CookFit — Build Log (`code.md`)

> **Purpose:** A running record of every command run and every change made while building CookFit.
> If context is ever lost, read this file top-to-bottom to reconstruct the full state of the project.
> **Rule:** Every command and every file change gets appended here, in order, with date.

---

## Project at a glance

- **Product:** CookFit — healthy Indian home-cooking & nutrition web app.
- **Stack:** FastAPI (Python 3.12) · React 18 + Vite + TypeScript · PostgreSQL 16 · SQLAlchemy 2.0 + Alembic · Tailwind CSS · TanStack Query.
- **Scope now:** Phase 1 MVP — nutrition engine + single-ingredient lookup + dish search + serving scaler + per-person/total nutrition. No auth.
- **Project root:** `C:\Users\Harshvardhan\cookfit`

### Planned layout
```
cookfit/
  code.md            # this build log
  backend/           # FastAPI app
  frontend/          # React + Vite app
  docker-compose.yml # Postgres for local dev
```

---

## Decisions log

- **Database runtime:** Docker not installed locally. Decision: **SQLite for dev** (`sqlite:///./cookfit.db`), **Postgres-ready** for production via `DATABASE_URL` env. All code DB-agnostic through SQLAlchemy. Fuzzy search done portably in Python (not pg_trgm) so it works on both.
- **Git:** repo initialized on `main`. Commit after each big change.

## Build sequence (checklist)

- [x] 1. Repo scaffold (backend/ folders, SQLite dev / Postgres-ready config, env) — DONE
- [x] 2. Nutrition engine + schema (models, Alembic migration, nutrition service + unit tests) — DONE
- [x] 3. Seed data v1 (curated ingredients + recipes JSON, load script) — DONE
- [ ] 4. Ingredient API + fuzzy search
- [ ] 5. Recipe API (scaled endpoint)
- [ ] 6. Frontend scaffold + theme (Vite, Tailwind, routing, API client)
- [ ] 7. Ingredient Lookup screen
- [ ] 8. Recipe View screen
- [ ] 9. Polish pass (responsive, loading/error states)
- [ ] 10. README with run instructions

---

## Change log

### 2026-05-30 — Session start

- Created project root: `C:\Users\Harshvardhan\cookfit`
  - Command: `mkdir -p /c/Users/Harshvardhan/cookfit`
- Created this build log: `cookfit/code.md`

### 2026-05-30 — Component 1: Backend scaffold + config

- Initialized git repo on `main` branch: `git init` + `git branch -m main`.
- Created `.gitignore` (Python, venv, node, env, editor/OS junk).
- Created backend dir tree: `backend/app/{core,db,models,schemas,services,api/v1,seed}` + `backend/tests`, with `__init__.py` in each package.
- Files:
  - `backend/requirements.txt` — FastAPI, uvicorn, SQLAlchemy 2.0, Alembic, Pydantic v2, pydantic-settings, psycopg (Postgres), pytest, httpx.
  - `backend/.env.example` — `DATABASE_URL` (SQLite dev default + Postgres example), `CORS_ORIGINS`.
  - `backend/app/core/config.py` — `Settings` via pydantic-settings, `get_settings()` cached, `cors_origins_list` helper.
  - `backend/app/db/base.py` — SQLAlchemy `Base` (DeclarativeBase).
  - `backend/app/db/session.py` — engine (SQLite `check_same_thread=False`), `SessionLocal`, `get_db()` dependency.
  - `backend/app/main.py` — FastAPI app, CORS middleware, `GET /health`.
- Commands:
  - `python -m venv .venv` (in `backend/`)
  - `.venv/Scripts/python.exe -m pip install -r requirements.txt`
  - Verified: `TestClient(app).get('/health')` -> `200 {'status':'ok'}`.
- **To run backend:** from `backend/`: `.venv/Scripts/python.exe -m uvicorn app.main:app --reload` (docs at http://localhost:8000/docs).

### 2026-05-30 — Component 2: Nutrition engine + DB schema

- **Schema design (single source of truth):** nutrition stored canonically **per 100g**; household units stored separately as gram-weights. Any quantity → grams → scale per-100g facts.
- Models (`backend/app/models/`):
  - `ingredient.py`:
    - `Ingredient` (id, slug[unique], name, aliases[JSON], category, default_unit, default_form)
    - `NutritionFacts` (ingredient_id, form raw|cooked, calories/protein_g/fiber_g/carbs_g/fat_g — all **per 100g**; unique(ingredient_id, form))
    - `IngredientUnit` (ingredient_id, label, grams; unique(ingredient_id, label))
  - `recipe.py`:
    - `Recipe` (id, slug, name, aliases[JSON], meal_type, base_servings=1, prep_time_min, instructions, tags[JSON])
    - `RecipeIngredient` (recipe_id, ingredient_id, quantity, unit_label, form, note) — quantities are **per 1 serving**
  - `__init__.py` re-exports all models.
- **Nutrition engine** `backend/app/services/nutrition.py` — pure, no DB/framework:
  - `Macros` dataclass (calories, protein_g, fiber_g, carbs_g, fat_g) with `__add__`, `scaled()`, `rounded()`.
  - `sum_macros()`, `macros_for_grams()`, `grams_for_quantity()` (implicit units g/kg/100g + per-ingredient household units, case-insensitive), `macros_for_quantity()`.
- **Tests** `backend/tests/test_nutrition.py` — 13 tests, all passing (`pytest -q`).
- **Alembic** set up (`backend/alembic/`, `backend/alembic.ini`):
  - `env.py` edited: pulls `DATABASE_URL` from app settings, `target_metadata = Base.metadata`, imports `app.models`, `render_as_batch=True` (SQLite-safe ALTERs).
  - Generated initial migration `alembic/versions/0573499e6866_initial_schema.py`.
  - Commands: `alembic revision --autogenerate -m "initial schema"` then `alembic upgrade head`.
  - Result: tables `ingredients, nutrition_facts, ingredient_units, recipes, recipe_ingredients` (+ `alembic_version`) created in dev SQLite `cookfit.db`.
- **Migration commands (remember):** from `backend/`: `.venv/Scripts/python.exe -m alembic upgrade head` to apply; `... revision --autogenerate -m "msg"` to create new after model changes.

### 2026-05-30 — Component 3: Seed data v1

- `backend/app/seed/ingredients.json` — 35 curated Indian ingredients (dals, legumes, grains/flours, vegetables, dairy, fats, nuts, aromatics, sweetener). Each has: slug, name, aliases, category, default_unit/form, household `units` (gram weights), and `facts` per-100g (raw and, where it differs, cooked). Values approximate IFCT/USDA — refine later.
- `backend/app/seed/recipes.json` — 10 healthy recipes (moong dal tadka, rajma, chole, palak paneer, aloo gobi, veg poha, paneer bhurji, masala oats, besan chilla, dal khichdi). Quantities are **per single serving** and reference ingredients by slug, using **raw** inputs (calories conserved from raw → cooked).
- `backend/app/seed/seed.py` — idempotent loader: wipes catalog tables (FK-safe order) then reloads; builds slug→id map; validates recipe ingredient refs.
- **Run seed:** from `backend/`: `.venv/Scripts/python.exe -m app.seed.seed`
- Verified counts: 35 ingredients / 43 facts / 69 units / 10 recipes / 55 recipe items.

<!--
APPEND NEW ENTRIES BELOW THIS LINE.
Format for each entry:
### <date> — <short title>
- What changed / why
- Commands run (exact)
- Files created/edited (paths)
-->
