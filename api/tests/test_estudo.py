import json
from types import SimpleNamespace

import pytest
from sqlalchemy import text

from app import estudo
from app.db import engine
from tests.test_contas import logado  # noqa: F401  (fixture de sessão)

ESTUDO_OK = {
    "mercado": "FinOps de IA é um tema ativo, sem concorrente mapeado comunicando o assunto.",
    "concorrentes": [{"nome": "Objective", "movimento": "Aquisição da Eleflow.", "implicacao": "Reforça a disputa em maturidade de IA."}],
    "oportunidades": [{"titulo": "FinOps de IA (OPT-3)", "porque": "Comprador é o CFO e o OPT-3 está pronto.", "impacto": "alto"}],
    "riscos": ["Falta histórico de propostas, porque o Jump Bases está fora do marco 1."],
    "perguntas_em_aberto": ["Qual o volume de gasto em nuvem das contas aderentes?"],
    "fontes": {"lidas": ["martech-monitor", "ICP Jump"], "ausentes": ["Jump Bases"]},
}


def resposta(conteudo, stop="end_turn"):
    texto = conteudo if isinstance(conteudo, str) else json.dumps(conteudo, ensure_ascii=False)
    return SimpleNamespace(
        stop_reason=stop,
        content=[SimpleNamespace(type="text", text=texto)],
        usage=SimpleNamespace(input_tokens=12000, output_tokens=1500),
        model="claude-sonnet-5-5",
    )


@pytest.fixture(autouse=True)
def ambiente(monkeypatch):
    monkeypatch.setenv("ICP_JUMP_MODE", "fixture")
    monkeypatch.setenv("MARTECH_MODE", "fixture")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "chave-de-teste")
    monkeypatch.setenv("CLAUDE_MODEL", "claude-sonnet-5-5")
    limpar = "delete from agent_log; delete from studies; delete from briefings; delete from launches;"
    with engine.begin() as conn:
        conn.execute(text(limpar))
    yield
    with engine.begin() as conn:
        conn.execute(text(limpar))


def fila(monkeypatch, *respostas):
    pendentes = list(respostas)
    chamadas = []

    def falsa(mensagens, modelo):
        chamadas.append(mensagens)
        return pendentes.pop(0)

    monkeypatch.setattr(estudo, "chamar_claude", falsa)
    return chamadas


def criar_lancamento(cliente):
    r = cliente.post("/api/lancamentos", json={"objetivo": "Lançar o OPT-3 para CFOs", "contexto": "Piloto", "provas": "", "prazo_dias": 42})
    assert r.status_code == 200
    return r.json()["id"]


def contar(tabela):
    with engine.connect() as conn:
        return conn.execute(text(f"select count(*) from {tabela}")).scalar_one()


def test_estudo_valido_grava_estudo_e_agent_log(logado, monkeypatch):  # noqa: F811
    fila(monkeypatch, resposta(ESTUDO_OK))
    lid = criar_lancamento(logado)
    r = logado.post(f"/api/lancamentos/{lid}/estudo")
    assert r.status_code == 200
    with engine.connect() as conn:
        s = conn.execute(text("select content, sources, status from studies")).mappings().one()
        log = conn.execute(text("select agent, model, tokens_in, tokens_out, cost_estimate, output_ref from agent_log")).mappings().one()
    assert s["status"] == "rascunho"
    assert s["sources"] == {"lidas": ["martech-monitor", "ICP Jump"], "ausentes": ["Jump Bases"]}
    assert set(s["content"]) == set(ESTUDO_OK)
    assert log["agent"] == "estudo" and log["model"] == "claude-sonnet-5-5"
    assert (log["tokens_in"], log["tokens_out"]) == (12000, 1500)
    assert float(log["cost_estimate"]) == 0.039  # 12k x $2/M + 1,5k x $10/M
    assert log["output_ref"]["study_id"] == r.json()["id"]
    assert logado.get("/api/lancamentos").json()["custo"]["gasto_usd"] == 0.039


def test_nova_tentativa_quando_a_checagem_falha(logado, monkeypatch):  # noqa: F811
    ruim = {**ESTUDO_OK, "mercado": "Mercado grande — cresce 47% ao ano."}
    chamadas = fila(monkeypatch, resposta(ruim), resposta(ESTUDO_OK))
    lid = criar_lancamento(logado)
    assert logado.post(f"/api/lancamentos/{lid}/estudo").status_code == 200
    assert contar("agent_log") == 2 and contar("studies") == 1
    pedido_de_correcao = chamadas[1][-1]["content"]
    assert "travessão" in pedido_de_correcao and "47" in pedido_de_correcao


def test_duas_falhas_dao_erro_visivel_e_nao_gravam_estudo(logado, monkeypatch):  # noqa: F811
    fila(monkeypatch, resposta("isso não é json"), resposta(ESTUDO_OK, stop="refusal"))
    lid = criar_lancamento(logado)
    r = logado.post(f"/api/lancamentos/{lid}/estudo")
    assert r.status_code == 422
    assert "duas tentativas" in r.json()["detail"]
    assert contar("agent_log") == 2 and contar("studies") == 0


def test_sem_chave_da_claude(logado, monkeypatch):  # noqa: F811
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    lid = criar_lancamento(logado)
    r = logado.post(f"/api/lancamentos/{lid}/estudo")
    assert r.status_code == 503


def test_exige_login(client):
    assert client.get("/api/lancamentos").status_code == 401


def test_checagem_numero_inventado():
    corpus = "Prazo de 42 dias. Mais de 60 clientes."
    assert estudo.checar({"mercado": "Prazo de 42 dias e mais de 60 clientes."}, corpus, []) == []
    problemas = estudo.checar({"mercado": "Mercado de 3,5 bilhões."}, corpus, [])
    assert problemas and "35" in problemas[0]


def test_checagem_cliente_bloqueado():
    assert estudo.checar({"riscos": ["Perder o Cliente Fictício Ômega."]}, "", ["Cliente Ficticio Omega"])


def test_fontes_marcam_jump_bases_como_ausente():
    _, fontes = estudo.ler_fontes()
    assert fontes == {"lidas": ["martech-monitor", "ICP Jump"], "ausentes": ["Jump Bases"]}
