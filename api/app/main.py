import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware

from app import aprovacoes, auth, contas, lancamentos, martech
from app.config import env
from app.db import engine


class OcultarRetornoDoLogin(logging.Filter):
    """Tira do log de acesso a query do retorno da Microsoft (código de autorização)."""

    def filter(self, record: logging.LogRecord) -> bool:
        args = record.args
        if isinstance(args, tuple) and len(args) >= 3 and str(args[2]).startswith("/api/auth/callback?"):
            record.args = (*args[:2], "/api/auth/callback?[oculto]", *args[3:])
        return True


logging.getLogger("uvicorn.access").addFilter(OcultarRetornoDoLogin())

app = FastAPI(title="Cockpit GTM Jump")
app.add_middleware(
    SessionMiddleware,
    secret_key=env("SESSION_SECRET", "dev-apenas-local"),
    same_site="lax",
    https_only=env("APP_URL", "").startswith("https://"),
)
app.include_router(auth.router)
app.include_router(contas.router)
app.include_router(martech.router)
app.include_router(lancamentos.router)
app.include_router(aprovacoes.router)


@app.get("/api/health")
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("select 1"))
    except Exception:
        return JSONResponse({"status": "erro", "db": "indisponivel"}, status_code=503)
    return {"status": "ok", "db": "ok"}
