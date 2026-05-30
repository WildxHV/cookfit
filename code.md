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
- [ ] 2. Nutrition engine + schema (models, Alembic migration, nutrition service + unit tests)
- [ ] 3. Seed data v1 (curated ingredients + recipes JSON, load script)
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

<!--
APPEND NEW ENTRIES BELOW THIS LINE.
Format for each entry:
### <date> — <short title>
- What changed / why
- Commands run (exact)
- Files created/edited (paths)
-->
