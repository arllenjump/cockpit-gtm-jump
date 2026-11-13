from sqlalchemy import text

from app.db import engine
from tests.test_contas import logado  # noqa: F401  (fixture de sessão)
from tests.test_estudo import ESTUDO_OK, ambiente, criar_lancamento, fila, resposta  # noqa: F401


def gerar(cliente, monkeypatch, *respostas):
    chamadas = fila(monkeypatch, *(respostas or (resposta(ESTUDO_OK),)))
    lid = criar_lancamento(cliente)
    r = cliente.post(f"/api/lancamentos/{lid}/estudo")
    assert r.status_code == 200
    return lid, r.json()["id"], chamadas


def um(sql, **p):
    with engine.connect() as conn:
        return conn.execute(text(sql), p).mappings().all()


def test_estudo_novo_entra_na_fila_como_pendente(logado, monkeypatch):  # noqa: F811
    _, sid, _ = gerar(logado, monkeypatch)
    [a] = um("select status, phase, item_id, decided_by from approvals where item_type = 'estudo'")
    assert (a["status"], a["phase"], a["item_id"], a["decided_by"]) == ("pendente", 1, sid, None)
    assert logado.get("/api/lancamentos").json()["estudo"]["aprovacao"] == "pendente"


def test_aprovar_grava_decisao_e_gate_de_1_para_2(logado, monkeypatch):  # noqa: F811
    lid, sid, _ = gerar(logado, monkeypatch)
    r = logado.post(f"/api/lancamentos/estudos/{sid}/decisao", json={"acao": "aprovar"})
    assert r.json() == {"status": "aprovado", "fase": 2}
    [a] = um("select status, decided_by, decided_at from approvals where item_type = 'estudo'")
    assert a["status"] == "aprovado" and a["decided_by"] == "pessoa@jumplabel.com.br" and a["decided_at"]
    [g] = um("select launch_id, from_phase, to_phase, advanced, reason_code, entered_at, exited_at from gate_events")
    assert (g["launch_id"], g["from_phase"], g["to_phase"], g["advanced"], g["reason_code"]) == (lid, 1, 2, True, None)
    assert g["entered_at"] <= g["exited_at"]
    assert um("select phase from launches where id = :l", l=lid)[0]["phase"] == 2
    assert um("select status from studies where id = :s", s=sid)[0]["status"] == "aprovado"


def test_ajustar_exige_nota_e_aprova_com_ressalva(logado, monkeypatch):  # noqa: F811
    _, sid, _ = gerar(logado, monkeypatch)
    assert logado.post(f"/api/lancamentos/estudos/{sid}/decisao", json={"acao": "ajustar"}).status_code == 422
    r = logado.post(f"/api/lancamentos/estudos/{sid}/decisao", json={"acao": "ajustar", "nota": "Dar mais peso ao CFO."})
    assert r.json() == {"status": "ajustado", "fase": 2}
    [a] = um("select status, note from approvals where item_type = 'estudo'")
    assert (a["status"], a["note"]) == ("ajustado", "Dar mais peso ao CFO.")
    assert len(um("select 1 from gate_events where from_phase = 1 and to_phase = 2 and advanced")) == 1


def test_devolver_nao_avanca_e_a_instrucao_vai_para_o_agente(logado, monkeypatch):  # noqa: F811
    lid, sid, _ = gerar(logado, monkeypatch)
    r = logado.post(f"/api/lancamentos/estudos/{sid}/decisao", json={"acao": "devolver", "nota": "Incluir o risco de prazo curto."})
    assert r.json() == {"status": "devolvido", "fase": 1}
    assert um("select count(*) as n from gate_events")[0]["n"] == 0
    assert um("select phase from launches where id = :l", l=lid)[0]["phase"] == 1
    assert um("select status from studies where id = :s", s=sid)[0]["status"] == "devolvido"
    # refazer: a instrução entra no pedido à Claude e o estudo novo volta para a fila
    chamadas = fila(monkeypatch, resposta(ESTUDO_OK))
    novo = logado.post(f"/api/lancamentos/{lid}/estudo").json()["id"]
    assert "Incluir o risco de prazo curto." in chamadas[0][0]["content"]
    assert [a["status"] for a in um("select status from approvals where item_type = 'estudo' order by id")] == ["devolvido", "pendente"]
    assert um("select item_id from approvals where status = 'pendente'")[0]["item_id"] == novo


def test_nao_decide_duas_vezes(logado, monkeypatch):  # noqa: F811
    _, sid, _ = gerar(logado, monkeypatch)
    assert logado.post(f"/api/lancamentos/estudos/{sid}/decisao", json={"acao": "aprovar"}).status_code == 200
    assert logado.post(f"/api/lancamentos/estudos/{sid}/decisao", json={"acao": "aprovar"}).status_code == 409


def test_decisao_exige_login(client):
    assert client.post("/api/lancamentos/estudos/1/decisao", json={"acao": "aprovar"}).status_code == 401
