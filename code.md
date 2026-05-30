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
- [x] 4. Ingredient API + fuzzy search — DONE
- [x] 5. Recipe API (scaled endpoint) — DONE  ← BACKEND MVP COMPLETE
- [x] 6. Frontend scaffold + theme (Vite, Tailwind, routing, API client) — DONE
- [x] 7. Ingredient Lookup screen — DONE (verified live in browser)
- [x] 8. Recipe View screen — DONE (verified live in browser)  ← FULL MVP FLOW WORKS
- [x] 9. Polish pass (responsive, loading/error states) — DONE
- [x] 10. README with run instructions — DONE  ← PHASE 1 MVP COMPLETE

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

### 2026-05-30 — Component 4: Ingredient API + fuzzy search

- `backend/app/services/search.py` — portable fuzzy search (no pg_trgm): `score_query()` (exact > startswith > substring > difflib ratio) and `rank()` over name+aliases, threshold 0.35. Reused by recipes later.
- `backend/app/schemas/ingredient.py` — Pydantic: `MacrosOut`, `UnitOut`, `IngredientSummary`, `SelectedNutrition`, `IngredientDetail` (returns per-100g facts + unit weights so the client can recalc live without round-trips).
- `backend/app/api/v1/ingredients.py`:
  - `GET /api/v1/ingredients/search?q=&limit=` → ranked summaries.
  - `GET /api/v1/ingredients/{id_or_slug}?quantity=&unit=&form=` → full detail + nutrition for the selected quantity/unit/form. Resolves by numeric id or slug. 404 unknown ingredient, 400 unknown unit.
- `backend/app/main.py` — mounted routers under `/api/v1`.
- Tests `backend/tests/test_ingredients_api.py` (7): alias search, fuzzy typo ("paner"→paneer), default unit calc, quantity+unit calc, forms available, 400/404. **Full suite: 20 passed.**
- API docs at http://localhost:8000/docs once running.

### 2026-05-30 — Component 5: Recipe API (scaled) — backend MVP done

- `backend/app/schemas/recipe.py` — `RecipeSummary`, `ScaledIngredient`, `RecipeDetail` (items scaled to servings + `per_person` + `total`).
- `backend/app/api/v1/recipes.py`:
  - `GET /api/v1/recipes/search?q=&limit=` → ranked summaries.
  - `GET /api/v1/recipes/{id_or_slug}?servings=N` → scaled ingredient list + per-person + total nutrition. Per-ingredient nutrition computed from its per-100g facts (form-matched, with fallback) via the engine; quantities and grams scale by N.
- Mounted recipes router under `/api/v1` in `main.py`.
- Tests `backend/tests/test_recipes_api.py` (5): alias search, default 1 serving, linear scaling (per_person invariant, total = per_person×N), total == sum of item nutrition, 404. **Full suite: 25 passed.**
- Sanity: Moong Dal Tadka ≈ 235 kcal / 12g protein per serving; ×4 = 940 kcal total.
- **Backend MVP endpoints:** `/health`, `/api/v1/ingredients/search`, `/api/v1/ingredients/{id|slug}`, `/api/v1/recipes/search`, `/api/v1/recipes/{id|slug}`.

### 2026-05-30 — Component 6: Frontend scaffold + theme

- Scaffolded with `npm create vite@latest frontend -- --template react-ts` (in `cookfit/`).
- Installed: `react-router-dom`, `@tanstack/react-query`, `axios`; dev: `tailwindcss`, `@tailwindcss/vite` (Tailwind v4 Vite-plugin setup).
- `frontend/vite.config.ts` — added `@tailwindcss/vite` plugin + dev **proxy `/api` → http://localhost:8000** (so frontend calls the backend without CORS pain).
- `frontend/src/index.css` — replaced boilerplate; `@import "tailwindcss"` + `@theme` tokens: single **accent = emerald/green** palette (accent-50..900), ink/muted/surface/canvas colors, Inter font.
- API layer:
  - `src/api/types.ts` — TS mirrors of backend schemas.
  - `src/api/client.ts` — axios (`baseURL: /api/v1`): `searchIngredients`, `getIngredient`, `searchRecipes`, `getRecipe`.
  - `src/lib/nutrition.ts` — client-side recalc mirroring backend engine (live updates, no round-trip).
  - `src/lib/useDebounce.ts` — debounce hook.
- App shell:
  - `src/main.tsx` — QueryClientProvider + BrowserRouter.
  - `src/App.tsx` — routes: `/` Home, `/ingredient`, `/recipe`.
  - `src/components/Layout.tsx` — sticky header, logo, nav pills (accent active state).
  - `src/components/NutritionCards.tsx` — 5 macro cards (calories highlighted in accent).
  - `src/components/SearchBox.tsx` — generic debounced search dropdown (React Query).
  - `src/pages/Home.tsx` — two mode cards (Ingredient / Recipe). IngredientLookup & RecipeView are stubs (filled in components 7–8).
- Removed Vite boilerplate (App.css, demo assets); set `index.html` title to CookFit.
- **Run frontend:** from `frontend/`: `npm run dev` (http://localhost:5173). Build verified: `npm run build` (tsc + vite) OK.

### 2026-05-30 — Component 7: Ingredient Lookup screen

- `src/components/QuantityControl.tsx` — stepper (−/+ by 0.5) + number input + unit `<select>`.
- `src/components/Segmented.tsx` — pill toggle (used for raw/cooked).
- `src/pages/IngredientLookup.tsx` — search → select → card. Fetches detail via React Query; recalcs **client-side** (lib/nutrition) on quantity/unit/form change. Raw/cooked toggle only shows when >1 form. Shows grams equivalent + NutritionCards.
- **Servers for verifying:** backend `uvicorn app.main:app --port 8000` (from backend/, venv); frontend `npm run dev` (5173). Vite proxies `/api`→8000.
- Browser-verified: "paner"→Paneer (fuzzy), 1 katori=100g→296 kcal; +0.5 → 1.5 katori=150g→444 kcal, 27.5 g protein (live recalc correct).
- Added `C:\Users\Harshvardhan\.claude\launch.json` (preview tool config; cwd `cookfit/frontend`, port 5173) — note: lives in user home, not repo.

### 2026-05-30 — Component 8: Recipe View screen (heart of product)

- `src/components/ServingScaler.tsx` — "Number of people" stepper (1–100), accent-styled.
- `src/pages/RecipeView.tsx` — search → select → result card. Refetches `getRecipe(slug, servings)` via React Query (key includes servings; `placeholderData` keeps old data during refetch to avoid flicker). Serving scaler + Per-person/Total toggle pinned (sticky) at top of result. Shows NutritionCards for the chosen view, scaled ingredient list (qty + unit + per-item kcal + notes), tags, and method.
- Browser-verified: Moong Dal Tadka 235 kcal/person (1 person); set to 4 + Total → 940 kcal, 48.2 g protein; ingredients scaled (dal 45→180 g). Matches backend exactly.
- **Full MVP user flow works end-to-end** (both input modes).

<!--
APPEND NEW ENTRIES BELOW THIS LINE.
Format for each entry:
### <date> — <short title>
- What changed / why
- Commands run (exact)
- Files created/edited (paths)
-->

### 2026-05-30 — Component 9: Polish pass + README (Phase 1 MVP complete)

- Polish: error states wired into both screens.
  - `src/components/ErrorBanner.tsx` — new; red banner, optional `message` prop, default "Something went wrong. Is the backend running on port 8000?".
  - `src/pages/IngredientLookup.tsx` — added `isError` from useQuery + `{slug && isError && <ErrorBanner />}` + import.
  - `src/pages/RecipeView.tsx` — same `isError` + `<ErrorBanner />` wiring + import.
  - `src/App.tsx` — added catch-all route `<Route path="*" element={<Navigate to="/" replace />} />` so unknown URLs redirect home.
- Responsive: verified mobile preset (375x812) layout renders cleanly; no console warnings/errors (preview console clean).
- `README.md` — new; full run instructions (backend venv + alembic upgrade + seed + uvicorn; frontend npm install + dev), config (.env, DATABASE_URL/CORS), API table, project layout.
- Build sequence checklist items 9 & 10 marked DONE. Phase 1 MVP is complete.
