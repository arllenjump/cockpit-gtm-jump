from tests.test_aprovacao_estudo import um
from tests.test_contas import logado  # noqa: F401  (fixture de sessão)
from tests.test_contrato import CONTRATO_OK, fase_2
from tests.test_estudo import ambiente, fila, resposta  # noqa: F401


def contrato_v1(cliente, monkeypatch):
    lid = fase_2(cliente, monkeypatch)
    chamadas = fila(monkeypatch, resposta(CONTRATO_OK))
    r = cliente.post(f"/api/lancamentos/{lid}/contrato")
    assert r.status_code == 200
    return lid, r.json()["id"], chamadas


def editar(cliente, cid, chave, estrategia, execucao):
    return cliente.put(f"/api/contratos/{cid}/clausulas/{chave}", json={"estrategia": estrategia, "execucao": execucao})


def vereditos(cid):
    return {k["clause_key"]: k["audit_verdict"] for k in um("select clause_key, audit_verdict from contract_clauses where contract_id = :c", c=cid)}


def test_contrato_gerado_entra_na_fila(logado, monkeypatch):  # noqa: F811
    _, v1, _ = contrato_v1(logado, monkeypatch)
    [a] = um("select item_id, phase, status from approvals where item_type = 'contrato'")
    assert (a["item_id"], a["phase"], a["status"]) == (v1, 2, "pendente")
    pagina = logado.get("/api/contratos/atual").json()
    assert [k["clause_key"] for k in pagina["contrato"]["clausulas"]][:3] == ["icp", "comite", "categoria"]
    assert len(pagina["contrato"]["testes"]) == 3 and pagina["contrato"]["aprovacao"]["status"] == "pendente"


def test_editar_cria_v2_e_audita_so_a_clausula(logado, monkeypatch):  # noqa: F811
    _, v1, _ = contrato_v1(logado, monkeypatch)
    antes = vereditos(v1)
    r = editar(logado, v1, "categoria", "FinOps de IA como disciplina com dono.", "Comparativo aberto no site.")
    assert r.status_code == 200 and r.json()["versao"] == 2 and r.json()["veredito"] == "alinhado"
    v2 = r.json()["id"]
    assert um("select status from gtm_contracts where id = :c", c=v2)[0]["status"] == "em_revisao"
    assert vereditos(v1) == antes  # a v1 do agente fica intacta
    depois = vereditos(v2)
    assert depois["categoria"] == "alinhado" and antes["categoria"] == "ajustar"
    assert {k: v for k, v in depois.items() if k != "categoria"} == {k: v for k, v in antes.items() if k != "categoria"}
    assert len(um("select 1 from test_hypotheses where contract_id = :c", c=v2)) == 3
    assert um("select item_id from approvals where item_type = 'contrato' and status = 'pendente'")[0]["item_id"] == v2
    # segunda edição altera a própria v2
    r2 = editar(logado, v2, "posicionamento", "Mensagem forte — clara.", "Canal por conta.")
    assert r2.json()["id"] == v2 and r2.json()["veredito"] == "ajustar"
    assert um("select count(*) as n from gtm_contracts")[0]["n"] == 2


def test_editar_e_aprovar_cria_v2_e_substitui_v1_com_gate_2_para_3(logado, monkeypatch):  # noqa: F811
    lid, v1, _ = contrato_v1(logado, monkeypatch)
    v2 = editar(logado, v1, "categoria", "FinOps de IA.", "Comparativo aberto.").json()["id"]
    r = logado.post(f"/api/contratos/{v2}/decisao", json={"acao": "aprovar"})
    assert r.json() == {"status": "aprovado", "fase": 3}
    status = {c["version"]: c["status"] for c in um("select version, status from gtm_contracts")}
    assert status == {1: "substituido", 2: "aprovado"}
    [g] = um("select from_phase, to_phase, advanced, entered_at, exited_at from gate_events where from_phase = 2")
    assert (g["to_phase"], g["advanced"]) == (3, True) and g["entered_at"] <= g["exited_at"]
    assert um("select phase from launches where id = :l", l=lid)[0]["phase"] == 3
    [a] = um("select status, decided_by, decided_at from approvals where item_type = 'contrato'")
    assert a["status"] == "aprovado" and a["decided_by"] == "pessoa@jumplabel.com.br" and a["decided_at"]
    # aprovado e versões antigas não se editam mais
    assert editar(logado, v2, "icp", "x", "y").status_code == 409
    assert editar(logado, v1, "icp", "x", "y").status_code == 409


def test_aprovar_com_ressalva_pela_fila(logado, monkeypatch):  # noqa: F811
    _, v1, _ = contrato_v1(logado, monkeypatch)
    [p] = logado.get("/api/aprovacoes").json()["pendentes"]
    assert p["item_type"] == "contrato"
    r = logado.post(f"/api/aprovacoes/{p['id']}/decisao", json={"acao": "ajustar", "nota": "Revisar a cláusula de pausa no ciclo 2."})
    assert r.json() == {"status": "ajustado", "fase": 3}
    assert um("select status from gtm_contracts where id = :c", c=v1)[0]["status"] == "aprovado"


def test_devolver_leva_a_instrucao_para_a_nova_versao(logado, monkeypatch):  # noqa: F811
    lid, v1, _ = contrato_v1(logado, monkeypatch)
    r = logado.post(f"/api/contratos/{v1}/decisao", json={"acao": "devolver", "nota": "Trocar o H2 por um teste de canal."})
    assert r.json() == {"status": "devolvido", "fase": 2}
    assert um("select count(*) as n from gate_events where from_phase = 2")[0]["n"] == 0
    chamadas = fila(monkeypatch, resposta(CONTRATO_OK))
    nova = logado.post(f"/api/lancamentos/{lid}/contrato").json()
    assert nova["versao"] == 2
    assert "Trocar o H2 por um teste de canal." in chamadas[0][0]["content"]
    assert [a["status"] for a in um("select status from approvals where item_type = 'contrato' order by id")] == ["devolvido", "pendente"]


def test_exige_login(client):
    assert client.get("/api/contratos/atual").status_code == 401
