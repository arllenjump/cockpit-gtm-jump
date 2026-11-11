from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware

from app import auth
from app.config import env
from app.db import engine

app = FastAPI(title="Cockpit GTM Jump")
app.add_middleware(
    SessionMiddleware,
    secret_key=env("SESSION_SECRET", "dev-apenas-local"),
    same_site="lax",
    https_only=env("APP_URL", "").startswith("https://"),
)
app.include_router(auth.router)


@app.get("/api/health")
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("select 1"))
    except Exception:
        return JSONResponse({"status": "erro", "db": "indisponivel"}, status_code=503)
    return {"status": "ok", "db": "ok"}
