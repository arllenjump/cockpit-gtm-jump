import pytest
from sqlalchemy import text

from app.db import engine
from tests.test_aprovacao_estudo import gerar, um
from tests.test_contas import logado  # noqa: F401  (fixture de sessão)
from tests.test_estudo import ambiente  # noqa: F401


@pytest.fixture(autouse=True)
def sem_listas():
    with engine.begin() as conn:
        conn.execute(text("delete from approvals where item_type = 'lista_contas'; delete from account_list_validations; delete from account_snapshots;"))
    yield
    with engine.begin() as conn:
        conn.execute(text("delete from approvals where item_type = 'lista_contas'; delete from account_list_validations; delete from account_snapshots;"))


def pendente(cliente):
    [p] = cliente.get("/api/aprovacoes").json()["pendentes"]
    return p


def test_fila_mostra_pendentes_e_historico(logado, monkeypatch):  # noqa: F811
    gerar(logado, monkeypatch)
    assert logado.post("/api/contas/validar").status_code == 200
    fila = logado.get("/api/aprovacoes").json()
    assert [p["item_type"] for p in fila["pendentes"]] == ["estudo"]
    assert [d["item_type"] for d in fila["decididos"]] == ["lista_contas"]


@pytest.mark.parametrize(
    "acao,nota,status,fase",
    [("aprovar", "", "aprovado", 2), ("ajustar", "Dar mais peso ao CFO.", "ajustado", 2), ("devolver", "Refazer riscos.", "devolvido", 1)],
)
def test_cada_acao_muda_o_status_e_grava_quem_e_quando(logado, monkeypatch, acao, nota, status, fase):  # noqa: F811
    gerar(logado, monkeypatch)
    p = pendente(logado)
    r = logado.post(f"/api/aprovacoes/{p['id']}/decisao", json={"acao": acao, "nota": nota})
    assert r.json() == {"status": status, "fase": fase}
    [a] = um("select status, note, decided_by, decided_at from approvals where id = :id", id=p["id"])
    assert a["status"] == status
    assert a["note"] == (nota or None)
    assert a["decided_by"] == "pessoa@jumplabel.com.br" and a["decided_at"] is not None
    assert logado.get("/api/aprovacoes").json()["pendentes"] == []


def test_item_decidido_ou_inexistente(logado, monkeypatch):  # noqa: F811
    gerar(logado, monkeypatch)
    p = pendente(logado)
    assert logado.post(f"/api/aprovacoes/{p['id']}/decisao", json={"acao": "aprovar"}).status_code == 200
    assert logado.post(f"/api/aprovacoes/{p['id']}/decisao", json={"acao": "aprovar"}).status_code == 409
    assert logado.post("/api/aprovacoes/999999/decisao", json={"acao": "aprovar"}).status_code == 404


def test_exige_login(client):
    assert client.get("/api/aprovacoes").status_code == 401
