import pytest
from sqlalchemy import text

from app import auth
from app.db import engine
from tests.test_auth import FakeMsal


@pytest.fixture(autouse=True)
def banco_limpo(monkeypatch):
    monkeypatch.setenv("ICP_JUMP_MODE", "fixture")
    limpar = "delete from approvals where item_type = 'lista_contas'; delete from account_list_validations; delete from account_snapshots;"
    with engine.begin() as conn:
        conn.execute(text(limpar))
    yield
    with engine.begin() as conn:
        conn.execute(text(limpar))


@pytest.fixture
def logado(client, monkeypatch):
    monkeypatch.setenv("ALLOWED_EMAIL_DOMAIN", "jumplabel.com.br")
    monkeypatch.setattr(auth, "msal_app", lambda: FakeMsal("pessoa@jumplabel.com.br"))
    client.get("/api/auth/login", follow_redirects=False)
    client.get("/api/auth/callback?code=x&state=s", follow_redirects=False)
    return client


def test_exige_login(client):
    assert client.get("/api/contas").status_code == 401
    assert client.post("/api/contas/validar").status_code == 401


def test_lista_ordenada_e_marca_simulacao(logado):
    r = logado.get("/api/contas").json()
    assert r["simulacao"] is True
    assert r["validacao"] is None
    assert [c["gtm_score"] for c in r["contas"]] == [91, 84, 77, 68, 62, 47]


def test_detalhe_traz_dossie(logado):
    conta = logado.get("/api/contas/sim-001").json()
    assert conta["dossier"]["recommended_offer"].startswith("OPT-3")
    assert logado.get("/api/contas/nao-existe").status_code == 404


def test_validacao_grava_validacao_aprovacao_e_snapshot(logado):
    r = logado.post("/api/contas/validar")
    assert r.status_code == 200
    with engine.connect() as conn:
        v = conn.execute(text("select week, validated_by, account_ids from account_list_validations")).mappings().one()
        a = conn.execute(text("select item_id, status, decided_by, decided_at from approvals where item_type = 'lista_contas'")).mappings().one()
        snaps = conn.execute(text("select count(*) from account_snapshots where week = :w"), {"w": v["week"]}).scalar_one()
    assert v["validated_by"] == "pessoa@jumplabel.com.br"
    assert len(v["account_ids"]) == 6
    assert a["item_id"] == r.json()["id"]
    assert a["status"] == "aprovado"
    assert a["decided_by"] == "pessoa@jumplabel.com.br"
    assert a["decided_at"] is not None
    assert snaps == 6
    assert logado.get("/api/contas").json()["validacao"]["validated_by"] == "pessoa@jumplabel.com.br"


def test_nao_valida_duas_vezes_na_mesma_semana(logado):
    assert logado.post("/api/contas/validar").status_code == 200
    assert logado.post("/api/contas/validar").status_code == 409
