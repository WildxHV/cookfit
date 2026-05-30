# CookFit

A healthy Indian home-cooking & nutrition web app. Search any ingredient or dish,
set the amount or number of people, and get clean per-person and total nutrition —
calories, protein, fiber, carbs, and fat.

- **Backend:** FastAPI (Python 3.12), SQLAlchemy 2.0, Alembic, Pydantic v2
- **Frontend:** React 18 + Vite + TypeScript, Tailwind CSS, TanStack Query
- **Database:** SQLite for local dev, Postgres-ready for production (DB-agnostic via SQLAlchemy)

---

## Features (Phase 1 MVP)

- **Ingredient lookup** — fuzzy search any ingredient, pick a household unit
  (katori, tbsp, piece…) and amount, switch raw/cooked, see nutrition update live.
- **Recipe view** — search a dish, set the number of people, and get scaled
  ingredient quantities with per-person and total nutrition.
- **Nutrition engine** — facts stored canonically per 100g; quantities resolve to
  grams, then scale. Recipes are defined per single serving and multiplied by N.
- No accounts, no setup beyond running two dev servers.

---

## Prerequisites

- Python 3.12+
- Node.js 18+

---

## Backend — run it

From the `backend/` folder:

```bash
# 1. Create + activate a virtual environment (first time only)
python -m venv .venv

# 2. Install dependencies (first time only)
.venv/Scripts/python.exe -m pip install -r requirements.txt

# 3. Create the database schema (first time only)
.venv/Scripts/python.exe -m alembic upgrade head

# 4. Load the curated seed data (ingredients + recipes)
.venv/Scripts/python.exe -m app.seed.seed

# 5. Start the API
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
```

- API runs at **http://localhost:8000**
- Interactive docs at **http://localhost:8000/docs**
- Health check: **http://localhost:8000/health**

> On macOS/Linux use `.venv/bin/python` instead of `.venv/Scripts/python.exe`.

### Configuration

Copy `backend/.env.example` to `backend/.env` to override defaults:

- `DATABASE_URL` — defaults to `sqlite:///./cookfit.db`. For Postgres:
  `postgresql+psycopg://user:pass@localhost:5432/cookfit`
- `CORS_ORIGINS` — comma-separated allowed origins (defaults include the Vite dev server).

### Tests

```bash
.venv/Scripts/python.exe -m pytest
```

---

## Frontend — run it

From the `frontend/` folder:

```bash
# 1. Install dependencies (first time only)
npm install

# 2. Start the dev server
npm run dev
```

- App runs at **http://localhost:5173**
- The Vite dev server proxies `/api` → `http://localhost:8000`, so make sure the
  backend is running first.

---

## API overview

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/api/v1/ingredients/search?q=&limit=` | Fuzzy-search ingredients |
| GET | `/api/v1/ingredients/{id_or_slug}?quantity=&unit=&form=` | Ingredient detail + nutrition |
| GET | `/api/v1/recipes/search?q=&limit=` | Fuzzy-search recipes |
| GET | `/api/v1/recipes/{id_or_slug}?servings=N` | Recipe scaled to N servings |

---

## Project layout

```
cookfit/
  code.md            # running build log
  README.md          # this file
  backend/           # FastAPI app
    app/
      api/v1/         # ingredient + recipe routes
      core/           # settings
      db/             # engine, session, base
      models/         # SQLAlchemy models
      schemas/        # Pydantic schemas
      services/       # nutrition engine + fuzzy search
      seed/           # curated JSON + loader
    alembic/          # migrations
    tests/            # pytest suite
  frontend/           # React + Vite app
    src/
      api/            # axios client + TS types
      components/      # reusable UI
      lib/            # client-side nutrition recalc + hooks
      pages/          # Home, IngredientLookup, RecipeView
```
