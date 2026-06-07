# CookFit 🥗

A healthy Indian home-cooking & nutrition web app. Look up any ingredient or
dish, scale it to any amount or number of people, get clean nutrition
(calories, protein, fiber, carbs, fat) — and, when you don't know what to make,
tell CookFit **what's in your kitchen** and it suggests dishes (classic **and**
fusion) you can cook right now.

The catalog grows itself: anything you search or get suggested that isn't in the
database is fetched from an LLM, **strictly validated**, and stored — so the app
gets richer with use, with no false entries.

- **Backend:** FastAPI (Python 3.12), SQLAlchemy 2.0, Alembic, Pydantic v2
- **Frontend:** React 18 + Vite + TypeScript, Tailwind CSS v4, TanStack Query
- **Database:** SQLite for local dev, Postgres-ready for production (DB-agnostic via SQLAlchemy)
- **AI:** provider-agnostic — Groq / Gemini / OpenAI / Grok (x.ai), tried in
  priority order with automatic fallback so a single rate limit never breaks a call

---

## Features

- **Ingredient lookup** — fuzzy search, pick a household unit (katori, tbsp,
  piece…) and amount, switch raw/cooked, see nutrition recalc live. Shows tags
  (gluten-free, high protein, vitamins/minerals) and the recipes that use it.
- **Recipe view** — search a dish, set the number of people, get scaled
  ingredient quantities with per-person and total nutrition and step-by-step
  method.
- **What can I make?** — list the ingredients you have (everyday staples
  assumed) and get dish ideas: catalog recipes you can (nearly) make now, plus
  AI-generated classic & fusion ideas with steps.
- **Self-growing catalog** — foods/recipes missing from the DB are fetched from
  an LLM, validated (vegetarian-only, physically-plausible & Atwater-consistent
  macros, resolvable units), and stored automatically in the background.
- **Personalization** — save allergens / things you don't eat (kept in your
  browser). They're excluded from every suggestion and flagged on any recipe or
  ingredient that contains them.
- **Resilient AI** — multiple models/providers in a fallback pool; only fails if
  every backend is down. No accounts required.

---

## Prerequisites

- Python 3.12+
- Node.js 18+
- (Optional) at least one AI provider key to enable suggestions & catalog growth

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

**AI providers** (all optional; set at least one to enable AI features). They're
tried in priority order with fallback, so one provider's rate limit won't fail a
request:

| Provider | Key | Notes |
| -------- | --- | ----- |
| Groq | `GROQ_API_KEY` (`GROQ_MODEL`) | Fast, generous free tier — recommended primary |
| Google Gemini | `GEMINI_API_KEY` (`GEMINI_MODEL`, `GEMINI_FALLBACK_MODELS`) | Free tier; multiple models fall back among themselves |
| OpenAI | `OPENAI_API_KEY` (`OPENAI_MODEL`) | Paid (needs billing) |
| Grok (x.ai) | `XAI_API_KEY` (`XAI_MODEL`) | — |

Priority order: Groq → other OpenAI-compatible → Gemini models. With no key set,
AI features are simply disabled and the rest of the app works normally.

> `.env` is gitignored — never commit real keys.

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
- The Vite dev server proxies `/api` → `http://localhost:8000`, so start the
  backend first.

---

## API overview

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/api/v1/ingredients/search?q=&limit=` | Fuzzy-search ingredients |
| GET | `/api/v1/ingredients/{id_or_slug}?quantity=&unit=&form=` | Ingredient detail + nutrition + tags |
| GET | `/api/v1/ingredients/{id_or_slug}/recipes` | Recipes that use this ingredient |
| GET | `/api/v1/ingredients/ai?q=` | AI lookup: fetch + validate + store a missing ingredient |
| GET | `/api/v1/recipes/search?q=&limit=` | Fuzzy-search recipes |
| GET | `/api/v1/recipes/{id_or_slug}?servings=N` | Recipe scaled to N servings |
| GET | `/api/v1/recipes/ai?q=&servings=N` | AI lookup: fetch + validate + store a missing dish |
| POST | `/api/v1/cook/suggest` | `{ingredients, avoid}` → catalog matches + AI dish ideas (grows the catalog in the background) |

---

## How the AI stays trustworthy

Nothing the model returns is trusted on faith. Every AI-sourced ingredient or
recipe must pass `app/services/ai_validation.py` before it can touch the DB:
vegetarian-only, per-100g macros within physical bounds, calories consistent
with macros (Atwater), every household unit resolvable to grams, and recipe
calories sane per serving. Items that fail are rejected, not stored. Each row is
tagged `source` (`seed` | `ai`) for provenance.

---

## Deploy (free, one service on Render)

The repo ships a `Dockerfile` that builds the frontend and runs the backend,
which **also serves the built frontend** — so it's a single service, same
origin, no CORS or separate API URL to configure. A `render.yaml` blueprint is
included.

1. Push this repo to GitHub.
2. On [Render](https://render.com): **New → Blueprint**, pick the repo (it reads
   `render.yaml`). Or **New → Web Service**, choose "Docker", leave defaults.
3. Under the service's **Environment**, add your secret keys — at minimum
   `GROQ_API_KEY` (and/or `GEMINI_API_KEY`). The non-secret model names are set
   by the blueprint.
4. Deploy. The container runs migrations, seeds the catalog if empty, and starts
   serving at `https://<your-app>.onrender.com`.

Notes:
- **SQLite on the free tier is ephemeral** — the curated catalog is re-seeded on
  each boot, and AI-added rows reset when the instance restarts. For persistence,
  point `DATABASE_URL` at a free hosted Postgres (e.g. Neon) — the app is
  DB-agnostic and migrations handle the rest.
- Free Render web services **sleep after ~15 min idle**, so the first request
  after a nap takes ~30–60s to wake.

To build the image locally:

```bash
docker build -t cookfit .
docker run -p 8000:8000 -e GROQ_API_KEY=... cookfit   # → http://localhost:8000
```

---

## Project layout

```
cookfit/
  code.md            # running build log
  README.md          # this file
  backend/           # FastAPI app
    app/
      api/v1/         # ingredients, recipes, cook routes
      core/           # settings (DB, CORS, AI providers)
      db/             # engine, session, base
      models/         # SQLAlchemy models
      schemas/        # Pydantic schemas
      services/       # nutrition engine, fuzzy search, AI lookup/validate/persist/suggest
      seed/           # curated JSON (116 ingredients, 49 recipes) + loader
    alembic/          # migrations
    tests/            # pytest suite (incl. mocked-AI tests)
  frontend/           # React + Vite app
    src/
      api/            # axios client + TS types
      components/      # reusable UI (SearchBox, Layout, cards…)
      lib/            # client-side nutrition recalc + hooks (usePreferences)
      pages/          # Home, IngredientLookup, IngredientRecipes,
                      # RecipeView, CookPage, Preferences
```
