import msal
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.config import env

router = APIRouter(prefix="/api")

SCOPES = ["User.Read"]


def email_permitido(email: str, dominio: str) -> bool:
    email = (email or "").strip().lower()
    dominio = (dominio or "").strip().lower().lstrip("@")
    return bool(dominio) and email.endswith("@" + dominio)


def redirect_uri() -> str:
    return env("APP_URL", "http://localhost:5173").rstrip("/") + "/api/auth/callback"


def msal_app() -> msal.ConfidentialClientApplication:
    return msal.ConfidentialClientApplication(
        env("MICROSOFT_CLIENT_ID"),
        client_credential=env("MICROSOFT_CLIENT_SECRET"),
        authority=f"https://login.microsoftonline.com/{env('MICROSOFT_TENANT_ID', 'common')}",
    )


@router.get("/auth/login")
def login(request: Request):
    flow = msal_app().initiate_auth_code_flow(SCOPES, redirect_uri=redirect_uri())
    request.session["flow"] = flow
    return RedirectResponse(flow["auth_uri"])


@router.get("/auth/callback")
def callback(request: Request):
    flow = request.session.pop("flow", None)
    if not flow:
        return RedirectResponse("/login?erro=sessao")
    result = msal_app().acquire_token_by_auth_code_flow(flow, dict(request.query_params))
    claims = result.get("id_token_claims") or {}
    email = claims.get("preferred_username") or claims.get("email") or ""
    if "error" in result or not email_permitido(email, env("ALLOWED_EMAIL_DOMAIN")):
        request.session.clear()
        return RedirectResponse("/login?erro=dominio")
    request.session["user"] = {"email": email.lower(), "name": claims.get("name", "")}
    return RedirectResponse("/")


@router.get("/auth/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login")


@router.get("/me")
def me(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return user
