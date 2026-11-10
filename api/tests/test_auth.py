import pytest

from app import auth


class FakeMsal:
    def __init__(self, email):
        self.email = email

    def initiate_auth_code_flow(self, scopes, redirect_uri):
        return {"auth_uri": "https://login.microsoftonline.com/fake", "state": "s"}

    def acquire_token_by_auth_code_flow(self, flow, params):
        return {"id_token_claims": {"preferred_username": self.email, "name": "Teste"}}


def entrar(client, monkeypatch, email):
    monkeypatch.setenv("ALLOWED_EMAIL_DOMAIN", "jumplabel.com.br")
    monkeypatch.setattr(auth, "msal_app", lambda: FakeMsal(email))
    r = client.get("/api/auth/login", follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"].startswith("https://login.microsoftonline.com/")
    return client.get("/api/auth/callback?code=x&state=s", follow_redirects=False)


def test_email_da_jump_entra(client, monkeypatch):
    r = entrar(client, monkeypatch, "pessoa@jumplabel.com.br")
    assert r.headers["location"] == "/"
    me = client.get("/api/me")
    assert me.status_code == 200
    assert me.json()["email"] == "pessoa@jumplabel.com.br"


def test_email_de_fora_e_recusado(client, monkeypatch):
    r = entrar(client, monkeypatch, "pessoa@gmail.com")
    assert r.headers["location"] == "/login?erro=dominio"
    assert client.get("/api/me").status_code == 401


def test_me_sem_login(client):
    assert client.get("/api/me").status_code == 401


@pytest.mark.parametrize(
    "email,ok",
    [
        ("a@jumplabel.com.br", True),
        ("A@JumpLabel.com.br", True),
        ("a@jumplabel.com.br.evil.com", False),
        ("a@evil-jumplabel.com.br", False),
        ("a@sub.jumplabel.com.br", False),
        ("", False),
    ],
)
def test_email_permitido(email, ok):
    assert auth.email_permitido(email, "jumplabel.com.br") is ok


def test_sem_dominio_configurado_recusa_todos():
    assert auth.email_permitido("a@jumplabel.com.br", "") is False
