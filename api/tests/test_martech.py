import pytest

from app import martech
from tests.test_contas import logado  # noqa: F401  (fixture de sessão)


@pytest.fixture(autouse=True)
def modo_fixture(monkeypatch):
    monkeypatch.setenv("MARTECH_MODE", "fixture")


def test_fixture_traz_as_6_ferramentas():
    respostas = martech.coletar()
    assert set(respostas) == {nome for nome, _ in martech.CHAMADAS}


def test_resumo_perfil_e_concorrentes():
    r = martech.resumo(martech.coletar())
    assert r["perfil"] == "Jump"
    assert r["concorrentes"] == 14


def test_ler_resultado_com_e_sem_embrulho():
    assert martech.ler_resultado('{"a": 1}') == {"a": 1}
    assert martech.ler_resultado('{"result": "{\\"a\\": 1}"}') == {"a": 1}


def test_chave_vai_na_query(monkeypatch):
    monkeypatch.setenv("MARTECH_MCP_URL", "https://exemplo/mcp")
    monkeypatch.setenv("MARTECH_MCP_KEY", "abc")
    assert martech._url() == "https://exemplo/mcp?key=abc"


def test_erro_nao_expoe_a_chave(monkeypatch):
    class Resposta:
        status_code = 401

    class ErroHttp(Exception):
        response = Resposta()

    async def falha():
        raise ExceptionGroup("grupo", [ErroHttp("url https://exemplo/mcp?key=SEGREDO")])

    monkeypatch.setenv("MARTECH_MODE", "mcp")
    monkeypatch.setattr(martech, "_coletar_mcp", falha)
    with pytest.raises(RuntimeError) as e:
        martech.coletar()
    assert "SEGREDO" not in str(e.value)
    assert "HTTP 401" in str(e.value)


def test_verificacao_exige_login(client):
    assert client.get("/api/martech/verificacao").status_code == 401


def test_verificacao_logado(logado):  # noqa: F811
    r = logado.get("/api/martech/verificacao").json()
    assert r == {"ok": True, "modo": "fixture", "perfil": "Jump", "concorrentes": 14, "sinais": 5,
                 "oportunidades": 3, "temas_ativos": 4, "sinais_no_brief_60_dias": 4}
