from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1 import cook, ingredients, recipes
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}


api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(ingredients.router)
api_v1.include_router(recipes.router)
api_v1.include_router(cook.router)
app.include_router(api_v1)


# In a production single-service deploy we also serve the built frontend
# (Vite `dist/` copied to backend/static). Registered AFTER the API + docs so
# those win; the catch-all returns index.html so SPA deep links work on refresh.
# In local dev this directory doesn't exist and the frontend runs on Vite.
_STATIC = Path(__file__).resolve().parent.parent / "static"
if _STATIC.is_dir():
    _assets = _STATIC / "assets"
    if _assets.is_dir():
        app.mount("/assets", StaticFiles(directory=_assets), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str) -> FileResponse:
        candidate = _STATIC / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_STATIC / "index.html")
