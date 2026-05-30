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

### 2026-05-30 — Data expansion: large veg ingredient + recipe set

- **Goal:** store as much Indian (veg-preferred) ingredient & recipe data as possible before adding the OpenAI fallback (next phase).
- **Seed validation guard** added to `app/seed/seed.py` (`_validate()`, runs before `_wipe()`): checks unique/required fields, valid forms (raw|cooked), recipe ingredient refs exist, and — key — that every recipe item's `(ingredient, unit_label)` resolves to grams via `grams_for_quantity` (implicit g/kg/100g or a unit defined on that ingredient). Bad data now fails loudly at seed time instead of 500-ing at request time. This is the "no false entries" check applied to our own curated data.
- **Data added** via a one-off generator (`backend/_expand_seed.py`, idempotent merge by slug, then deleted — JSON remains source of truth):
  - `ingredients.json`: 35 → **116** (+81). New: more legumes/dals (sabut moong, kala chana, lobia, soybean, matki, kulthi, whole masoor, safed matar, moong sprouts); millets/grains (brown rice, bajra, jowar, ragi, makki atta, quinoa, rava, vermicelli, sabudana, idli, dosa, daliya, whole-wheat bread); many vegetables (lauki, karela, turai, kaddu, cabbage, french beans, beetroot, mooli, cucumber, mushroom, sweet potato, arbi, methi/coriander/mint leaves, broccoli, gavar, raw banana, drumstick, sweet corn); dairy (butter, buttermilk, tofu, khoya, cream, cheese); nuts/seeds/dry fruits (almonds, walnuts, pistachios, raisins, dates, til, flax, sunflower & chia seeds, makhana); oils (sunflower, groundnut, coconut, olive); sweeteners (jaggery, honey); spices (jeera, haldi, dhania, red chili, garam masala, rai, black pepper); fruits (banana, apple, mango, papaya, guava, orange, pomegranate, grapes, watermelon, lemon).
  - `recipes.json`: 10 → **49** (+39). New: dals (toor dal fry, masoor, dal palak, dal makhani, mixed/panchmel, kala chana, lobia, matki usal, soybean curry); rice/grains (jeera rice, veg pulao, lemon rice, curd rice, veg biryani, veg daliya); tiffin/breakfast (idli, masala dosa, rava upma, sevai upma, sabudana khichdi, moong cheela, aloo paratha, methi thepla); sabzis (bhindi masala, baingan bharta, lauki, mix veg, jeera aloo, matar paneer, gobi matar, cabbage); gravies (sambar, kadhi, veg raita); snacks/salads (sprouts salad, chana chaat, dhokla, roasted makhana, fruit chaat).
- **Verification:** `python -m app.seed.seed` → "Seeded 116 ingredients and 49 recipes." `pytest` → 25 passed. Runtime smoke test via TestClient hit all 49 recipes (servings=2) + all 116 ingredient defaults → **0 failures, no zero-calorie recipes**. Spot-checked values sane (banana 1 pc=107 kcal, olive oil 1 tbsp=124 kcal, matar paneer 279 kcal/person). Live server + Vite proxy verified returning new items (badam→Almonds, makhana).
- **Nutrition values:** approximate, IFCT-2017/USDA-style per 100g (raw, plus cooked where it differs). Refine later.
- **Next phase (not yet started):** OpenAI fallback — when a search misses our DB, query a (free) model, format to our schema, validate it is genuinely cooking/ingredient data with sane macros, then insert into the DB. Validation guard above is the foundation for those "no false entries" checks.

### 2026-05-30 — Phase B: Google Gemini AI fallback (live, working)

- **Goal:** when a search misses our DB, ask Gemini (free tier) for the food, validate it hard ("no false entries", veg-only, plausible macros), store it (`source='ai'`), and return it like any seed item. Auto-trigger on no DB match. Covers ingredients AND recipes.
- **Provenance column:** added `source: Mapped[str]` (`String(20)`, default `"seed"`, indexed) to `app/models/ingredient.py` and `app/models/recipe.py`. Migration `alembic/versions/4e8f033ff937_..._add_source_column_...py` (down_revision `0573499e6866`) adds the column to both tables with `server_default='seed'` so existing rows backfill. Applied via `alembic upgrade head`. Exposed as `source` in `schemas/ingredient.py` `IngredientDetail` and `schemas/recipe.py` `RecipeDetail`.
- **Config** (`app/core/config.py`): added `gemini_api_key=""`, `gemini_model="gemini-2.5-flash-lite"`, `gemini_timeout_s=30.0`, and `@property ai_enabled` (true when key is set). `.env.example` documents `GEMINI_API_KEY=` / `GEMINI_MODEL=gemini-2.5-flash-lite`. Real key lives ONLY in `backend/.env` (gitignored).
- **Gemini client** (`app/services/ai_lookup.py`, new): REST `:generateContent` with structured output (`responseMimeType=application/json` + `responseSchema`). `lookup_ingredient(q)` / `lookup_recipe(q)`. Recipe schema returns the recipe `items` PLUS a full `ingredients[]` array (per-100g nutrition + units) for every ingredient used, so we can insert any we don't already have. Prompts force: Indian veg context, per-100g, Atwater-consistent calories, single-word unit labels. `GeminiError` on any non-200/parse failure.
- **Validation** (`app/services/ai_validation.py`, new) — the "no false entries" gate; nothing is trusted:
  - `validate_ingredient`: rejects non-food / non-veg; bounds (cal ≤ 900, each macro ≤ 100 g/100g, fiber ≤ carbs); Atwater check `cal ≈ 4P+4C+9F` (tol `max(45, 30%)`); unit grams `0 < g ≤ 3000`.
  - `validate_recipe`: validates every sub-ingredient, maps items→ingredient by name, resolves every `(ingredient, unit)` to grams (rejects unresolved), computes per-serving macros, rejects 0 or > 3000 kcal/serving, auto-tags `vegetarian`.
  - **Unit normalization** (`_canonical_unit`): Gemini often returns verbose labels ("cup, sliced", "piece (medium)", "Tablespoon"); these are reduced to a known single-word vocabulary (katori/cup/tbsp/tsp/piece/clove/glass/cube/bunch/slice/bowl/...). If `default_unit` still won't resolve, it falls back to `"g"` (always available) instead of rejecting an otherwise-good ingredient. Item `unit_label`s are canonicalized the same way.
- **Persistence** (`app/services/ai_persist.py`, new): `upsert_ai_ingredient` (dedupe by slug, else insert with `source="ai"` + facts + units), `upsert_ai_recipe` (upsert all sub-ingredients first via name→id map, then create recipe + items), `_unique_slug` helper.
- **Endpoints**: `GET /api/v1/ingredients/ai?q=` and `GET /api/v1/recipes/ai?q=` (declared BEFORE `/{id_or_slug}`). Flow: strong DB match (threshold 0.6) short-circuits without a call → else 503 if not `ai_enabled` → `lookup_*` (502 on GeminiError) → `validate_*` (422 on ValidationError) → upsert + commit → return scaled detail. `_detail_for` extracted in both routers and now carries `source`.
- **Tests** (39 pass): `tests/test_ai_validation.py` (pure: valid pass, non-food/non-veg/cal-inconsistency/impossible-macro/implausible-unit rejected, implicit units dropped, recipe valid/unresolvable-unit/missing-ingredient/non-veg) + `tests/test_ai_endpoints.py` (Gemini monkeypatched: ingredient inserts + `source='ai'`, non-veg→422, recipe inserts recipe + missing ingredients; inserted rows cleaned up).
- **Live model fix:** `gemini-2.0-flash` free quota was exhausted (HTTP 429). Listed models for the key (`GET /v1beta/models`), found `gemini-2.5-flash-lite` has free quota → set as default in `.env`, `.env.example`, and `config.py`.
- **Port/zombie gotcha:** an orphaned `python.exe` kept the listener on 8000 (netstat showed a PID `taskkill` couldn't find, since the socket fd was inherited by a sibling process). Fixed with `Stop-Process -Name python -Force`, then restarted uvicorn cleanly.
- **Commands run (exact):**
  - `curl "https://generativelanguage.googleapis.com/v1beta/models?key=$KEY"` — enumerate usable models.
  - `.venv/Scripts/python.exe -m pytest tests/test_ai_validation.py -q` → 11 passed.
  - `powershell Stop-Process -Name python -Force` then `.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000` (background).
  - Live verified: `GET /api/v1/ingredients/ai?q=avocado` → stored id 117, `source=ai`, units normalized to piece/cup/tbsp. `GET /api/v1/recipes/ai?q=hara bhara kabab` → stored recipe + 14 auto-inserted ingredients, per-person 240 kcal. `GET /api/v1/recipes/ai?q=palak paneer` → short-circuited to existing seed recipe (no call).
- **Next:** frontend auto-fallback (call `/ai` when a DB search returns 0 results, "Searching with AI…" state) + an "AI" source badge on AI-sourced items.

### 2026-05-30 — Phase B (frontend): AI auto-fallback in search + AI badge

- **Goal:** when a user searches a food we don't have, let them fetch it via the Gemini `/ai` endpoints from the UI, then render it like any other result with a visible "AI" provenance badge.
- **Types** (`frontend/src/api/types.ts`): added `source: string` to `IngredientDetail` and `RecipeDetail` (mirrors the backend schema field).
- **API client** (`frontend/src/api/client.ts`): added `aiLookupIngredient(q)` → `GET /ingredients/ai?q=` and `aiLookupRecipe(q)` → `GET /recipes/ai?q=`, each returning the full detail object.
- **SearchBox** (`frontend/src/components/SearchBox.tsx`): added optional `aiSearch(q) => Promise<{slug}>`, `onAiResult(slug)`, and `aiNoun` props. The fuzzy `/search` endpoint uses a low default threshold (0.35) and almost always returns *some* loose match, so a true "no matches" state is rare — instead of gating on emptiness, the dropdown now ALWAYS shows a trailing AI fallback row when `aiSearch` is provided: "Not it? look up '<q>' with AI" (or "Not in our list — …" when there are zero matches, where it's the only row). Clicking it shows an inline spinner "Searching with AI for '<q>'…"; `onMouseDown`+`preventDefault` keeps input focus so the dropdown stays open during the in-flight call. On success it calls `onAiResult(slug)` and clears; on failure it shows a friendly inline message mapped from the HTTP status (422 = no reliable data, 503 = not configured, 502 = AI unavailable).
- **AiBadge** (`frontend/src/components/AiBadge.tsx`, new): small violet "✨ AI" pill with tooltip "Fetched with AI and added to our database".
- **Pages**: `IngredientLookup.tsx` and `RecipeView.tsx` wire `aiSearch`/`onAiResult` (→ `setSlug`, recipe also resets servings to 1) into their SearchBox, and render `<AiBadge />` next to the result name when `detail.source === "ai"`. After the AI call stores the item, the existing `useQuery(getIngredient/getRecipe, slug)` refetches it normally.
- **Verification:** in progress via the running Vite preview (port 5173, proxying to backend on 8000).

### 2026-05-30 — Phase B: AI fallback verified end-to-end + short-circuit threshold fix

- **Bug found during browser verification:** the `/ai` endpoints' "do we already have it?" pre-check used `search.rank(..., threshold=0.6)`, which produced false positives — e.g. searching "starfruit" fuzzily matched the avocado alias "butter fruit" (SequenceMatcher ratio 0.667, both share "fruit"), so the endpoint returned **Avocado** instead of calling Gemini for starfruit.
- **Fix:** raised the short-circuit threshold from `0.6` → `0.85` in both `app/api/v1/ingredients.py` and `app/api/v1/recipes.py`. At 0.85 only near-exact/prefix/substring name matches skip the AI call (which is the point — avoid redundant calls/duplicates for foods we truly have), while genuinely new queries fall through to Gemini. Confirmed: `/ingredients/ai?q=starfruit` now returns **Starfruit** (source ai).
- **Live browser verification (Vite preview :5173 → backend :8000):**
  - Ingredient: searched "rambutan" → trailing "Not it? look up 'rambutan' with AI" row → click → spinner → renders **Rambutan** (Fruit, piece=15g, 9 kcal) with the **✨ AI** badge.
  - Recipe: searched "veg manchurian" → AI row → "Searching with AI…" spinner → renders **Veg Manchurian** with **✨ AI** badge, 328 kcal/person, 14 ingredients all resolved (cabbage, carrots, green beans, onion, ginger-garlic paste, green chili, soy sauce, vinegar, salt, black pepper, cornflour, all-purpose flour, vegetable oil).
  - No browser console errors. `npx tsc --noEmit` clean. Backend `pytest` → 39 passed.
- Phase B (Gemini AI fallback, backend + frontend) is complete and working end-to-end.

### 2026-05-30 — Recipe Method: render step-by-step instead of one paragraph

- **Why:** recipe instructions arrive as a single string with inline numbering ("1. … 2. … 3. …") and were dumped into one cramped `<p>`. Hard to follow while cooking.
- **`frontend/src/pages/RecipeView.tsx`:** added `parseSteps(text)` — splits on `\d+\.\s+` numbering (inline or per-line), falls back to newline-split, else a single block. The Method section now renders an `<ol>` where each step has a small circular accent number badge + the step text; a one-step instruction still renders as a plain paragraph.
- **Verified:** Veg Manchurian (12 steps) now shows a clean numbered list with green number chips; `npx tsc --noEmit` clean; no console errors.

### 2026-05-30 — Ingredient names carry the common Indian name in brackets

- **Goal (user):** names like "Asafoetida" should display the common Indian name in brackets → "Asafoetida (hing)".
- **AI prompt** (`backend/app/services/ai_lookup.py`): both the ingredient and recipe-ingredient prompts now instruct Gemini to format `name` as "English Name (common Indian name)" when a well-known Hindi name differs (e.g. "Asafoetida (hing)", "Fenugreek Seeds (methi dana)"), use the plain name when the English name already is the common one (Paneer, Quinoa, Oats), and also list the common name in `aliases`. Verified live: an AI lookup for "jackfruit" returns **"Jackfruit (kathal)"** with alias `kathal`.
- **Seed data** (`backend/app/seed/ingredients.json`): added the bracketed common name to 26 entries that previously had only the plain English name (Banana (kela), Apple (seb), Mango (aam), Almonds (badam), Walnuts (akhrot), Pistachios (pista), Butter (makkhan), Honey (shahad), Coconut Oil (nariyal tel), Mustard Oil (sarson ka tel), Red Chili Powder (lal mirch), Cabbage (patta gobi), Beetroot (chukandar), Cucumber (kheera), Sweet Potato (shakarkandi), Coriander Leaves (hara dhania), Sweet Corn (makka), Orange (santra), Pomegranate (anar), Grapes (angoor), Watermelon (tarbooz), Lemon (nimbu), Papaya (papita), Guava (amrood), Groundnut Oil (moongphali tel), French Beans (fansi)). Common name also ensured present in `aliases` for search. Slugs unchanged, so recipe references stay valid.
- **Commands:** one-off Python script over `ingredients.json` (name+alias merge) → `python -m app.seed.seed` (re-validated + reseeded: "Seeded 116 ingredients and 49 recipes.") → restarted uvicorn to pick up the new prompt.
- **Verification:** `pytest` → 39 passed; live search shows "Banana (kela)", "Almonds (badam)", "Jackfruit (kathal)", etc.
- **Note:** the AI lookup for "asafoetida" itself was *declined* this run because Gemini's macros failed the Atwater consistency guard (320 vs ~225 kcal) — asafoetida powder is often cut with starch, so values vary. This is the "no false entries" validator working as intended; the naming convention applies whenever the data passes.

### 2026-05-30 — Make AI fallback seamless: transient badge, top-of-list, neutral wording

User asks: (1) the AI tag must NOT persist — once data is in our DB, a later search/user should see it as normal data; the tag should appear only on the search that fetched it; (2) put the lookup option at the TOP of the dropdown so it isn't buried under loose fuzzy matches; (3) make the lookup feel seamless — like it came from our own DB, not "fetched from somewhere".

- **Transient badge (was persistent).** Previously the badge rendered from `detail.source === "ai"`, which is permanent, so every future view showed it. Now each page tracks `aiSlug` (the slug just fetched via the lookup fallback): `onAiResult` sets it, any normal `onSelect` clears it. Badge shows only when `aiSlug === detail.slug`. Verified: looking up "dragonfruit" shows the badge; re-searching and picking it from results shows it with **no** badge.
- **Top-of-list lookup action** (`SearchBox.tsx`): the fallback row moved from the bottom to the **top** of the dropdown (with a divider below it when matches exist), so it's reachable without scrolling past non-matching fuzzy results.
- **Neutral / seamless wording:** dropdown row "🔍 Look up "<q>"" (was "✨ … look up "<q>" with AI"); spinner "Looking up "<q>"…" (was "Searching with AI…"); error messages no longer mention "AI"; the badge label changed from "AI" to **"New"** (tooltip "Just added to your catalog") so the result reads as freshly-added catalog data rather than externally sourced. `source` is still stored in the DB for provenance but no longer drives any UI.
- **Verified:** `npx tsc --noEmit` clean; no console errors; lookup row is dropdown item #1; badge is one-shot.

### 2026-05-30 — Remove the badge entirely (looked-up items look native)

- User: "no need for ai" — drop the badge altogether so a looked-up item is indistinguishable from our own catalog data.
- Removed the `<AiBadge>` from both pages, deleted `frontend/src/components/AiBadge.tsx`, and removed the now-unused `aiSlug` state (kept `onAiResult → setSlug` so the lookup still loads the result). The lookup flow is unchanged otherwise; it just shows the result with no badge.
- `source` column still recorded in the DB for provenance; nothing in the UI reflects it.
- Verified: looked up "lychee" → renders as a normal ingredient (name + category), no badge; `npx tsc --noEmit` clean.
