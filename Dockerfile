# CookFit — single-image deploy: build the React frontend, then run the FastAPI
# backend which also serves the built frontend (same origin, one service).

# ---- Stage 1: build the frontend ----
FROM node:20-alpine AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: backend + static frontend ----
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

COPY backend/requirements.txt ./
RUN pip install -r requirements.txt

COPY backend/ ./
# Built frontend goes where app.main looks for it (backend/static).
COPY --from=frontend /fe/dist ./static

EXPOSE 8000
# Apply migrations, seed only if the DB is empty, then serve.
CMD ["sh", "-c", "alembic upgrade head && python -m app.seed.seed --if-empty && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
