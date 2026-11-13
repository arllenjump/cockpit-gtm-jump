import copy

from app.auditoria import CHAVES
from tests.test_aprovacao_estudo import gerar as gerar_estudo
from tests.test_aprovacao_estudo import um
from tests.test_contas import logado  # noqa: F401  (fixture de sessão)
from tests.test_estudo import ambiente, fila, resposta  # noqa: F401


def clausula(k):
    textos = {
        "sucesso": ("Provar que o OPT-3 gera reunião com CFO.", "Medir reuniões por conta e pipeline por conta, faixa a calibrar com o histórico."),
        "categoria": ("FinOps de IA como disciplina com dono.", "Comparativo disponível após cadastro em formulário."),
    }
    estrategia, execucao = textos.get(k, (f"Estratégia de {k} para o OPT-3.", f"Execução de {k} com CFO e CTO."))
    return {"key": k, "estrategia": estrategia, "execucao": execucao}


def um_teste(codigo, status):
    return {"codigo": codigo, "hipotese": "CFO responde melhor a custo por agente.", "caminho_a": "Mensagem de custo.",
            "caminho_b": "Mensagem de governança.", "sinal_rapido": "Resposta ao primeiro contato.",
            "sinal_lento": "Reunião marcada.", "faixa_prevista": "a calibrar com o histórico",
            "regra": "Fica o caminho com mais reuniões por conta.", "status": status}


CONTRATO_OK = {"clausulas": [clausula(k) for k in CHAVES], "testes": [um_teste("H1", "ativa"), um_teste("H2", "ativa"), um_teste("H3", "na_fila")]}


def fase_2(cliente, monkeypatch):
    lid, sid, _ = gerar_estudo(cliente, monkeypatch)
    assert cliente.post(f"/api/lancamentos/estudos/{sid}/decisao", json={"acao": "ajustar", "nota": "Dar mais peso ao CFO."}).status_code == 200
    return lid


def test_contrato_v1_com_10_clausulas_testes_e_auditoria(logado, monkeypatch):  # noqa: F811
    lid = fase_2(logado, monkeypatch)
    chamadas = fila(monkeypatch, resposta(CONTRATO_OK))
    r = logado.post(f"/api/lancamentos/{lid}/contrato")
    assert r.status_code == 200
    assert r.json()["versao"] == 1 and r.json()["clausulas"] == 10
    [c] = um("select id, version, status from gtm_contracts")
    assert (c["version"], c["status"]) == (1, "rascunho")
    clausulas = um("select clause_key, audit_verdict, audit_note, reviewed_at from contract_clauses where contract_id = :c", c=c["id"])
    assert sorted(k["clause_key"] for k in clausulas) == sorted(CHAVES)
    assert all(k["reviewed_at"] for k in clausulas)
    vereditos = {k["clause_key"]: k["audit_verdict"] for k in clausulas}
    assert vereditos["categoria"] == "ajustar"  # comparativo atrás de formulário (regra 6)
    assert vereditos["sucesso"] == "alinhado"
    testes = um("select code, status, expected_range from test_hypotheses where contract_id = :c order by code", c=c["id"])
    assert [t["status"] for t in testes] == ["ativa", "ativa", "na_fila"]
    assert testes[0]["expected_range"] == {"texto": "a calibrar com o histórico"}
    # entrada do agente: estudo aprovado, ressalva e resumo das contas
    pedido = chamadas[0][0]["content"]
    assert "Dar mais peso ao CFO." in pedido and "estudo_aprovado" in pedido and "contas_aderentes" in pedido
    assert "apostas_iniciais" in pedido and "Para o CFO, a dor de custo engaja mais que governança" in pedido
    agentes = [a["agent"] for a in um("select agent from agent_log where agent in ('contrato', 'auditoria') order by id")]
    assert agentes == ["contrato", "auditoria"]
    assert um("select output_ref from agent_log where agent = 'contrato'")[0]["output_ref"]["contract_id"] == c["id"]
    resumo = logado.get("/api/lancamentos").json()["contrato"]
    assert (resumo["version"], resumo["alinhado"], resumo["ajustar"], resumo["conflito"]) == (1, 9, 1, 0)


def test_segunda_geracao_vira_v2(logado, monkeypatch):  # noqa: F811
    lid = fase_2(logado, monkeypatch)
    fila(monkeypatch, resposta(CONTRATO_OK), resposta(CONTRATO_OK))
    logado.post(f"/api/lancamentos/{lid}/contrato")
    assert logado.post(f"/api/lancamentos/{lid}/contrato").json()["versao"] == 2


def test_nova_tentativa_com_clausula_faltando_ou_testes_demais(logado, monkeypatch):  # noqa: F811
    lid = fase_2(logado, monkeypatch)
    ruim = copy.deepcopy(CONTRATO_OK)
    ruim["clausulas"] = ruim["clausulas"][:9]
    ruim["testes"][2]["status"] = "ativa"
    chamadas = fila(monkeypatch, resposta(ruim), resposta(CONTRATO_OK))
    assert logado.post(f"/api/lancamentos/{lid}/contrato").status_code == 200
    correcao = chamadas[1][-1]["content"]
    assert "Faltam cláusulas: sucesso" in correcao and "3 testes ativos" in correcao


def test_duas_falhas_nao_gravam_contrato(logado, monkeypatch):  # noqa: F811
    lid = fase_2(logado, monkeypatch)
    ruim = copy.deepcopy(CONTRATO_OK)
    ruim["clausulas"][0]["estrategia"] = "ICP forte — sem dúvida."
    fila(monkeypatch, resposta(ruim), resposta(ruim))
    r = logado.post(f"/api/lancamentos/{lid}/contrato")
    assert r.status_code == 422 and "travessão" in r.json()["detail"]
    assert um("select count(*) as n from gtm_contracts")[0]["n"] == 0


def test_so_gera_na_fase_2(logado, monkeypatch):  # noqa: F811
    lid, _, _ = gerar_estudo(logado, monkeypatch)
    assert logado.post(f"/api/lancamentos/{lid}/contrato").status_code == 409
