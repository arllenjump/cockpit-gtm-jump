import pytest

from app import icp_jump


@pytest.fixture(autouse=True)
def modo_fixture(monkeypatch):
    monkeypatch.setenv("ICP_JUMP_MODE", "fixture")


def test_min_score_60_devolve_5_contas_em_ordem_decrescente():
    contas = icp_jump.list_accounts(min_score=60)
    scores = [c["gtm_score"] for c in contas]
    assert len(contas) == 5
    assert scores == sorted(scores, reverse=True)
    assert min(scores) >= 60


def test_sem_filtro_devolve_as_6_contas_ordenadas():
    scores = [c["gtm_score"] for c in icp_jump.list_accounts()]
    assert scores == [91, 84, 77, 68, 62, 47]


def test_filtro_por_vertical():
    contas = icp_jump.list_accounts(vertical="Saúde")
    assert [c["external_id"] for c in contas] == ["sim-003"]


def test_filtro_por_sinais_ativos():
    com = icp_jump.list_accounts(has_active_signals=True)
    sem = icp_jump.list_accounts(has_active_signals=False)
    assert len(com) == 5
    assert [c["external_id"] for c in sem] == ["sim-006"]


def test_get_account_traz_dossie_e_decisores():
    conta = icp_jump.get_account("sim-001")
    assert set(conta["dossier"]) == {"why_now", "why_us", "suggested_approach", "risks", "recommended_offer"}
    assert any(d["is_decision_maker"] for d in conta["decision_makers"])


def test_get_account_inexistente():
    assert icp_jump.get_account("nao-existe") is None


def test_modo_api_ainda_nao_implementado(monkeypatch):
    monkeypatch.setenv("ICP_JUMP_MODE", "api")
    with pytest.raises(NotImplementedError):
        icp_jump.list_accounts()


def test_fixture_sem_dado_pessoal_nem_travessao():
    texto = icp_jump.FIXTURE.read_text(encoding="utf-8")
    assert "—" not in texto
    assert "@" not in texto  # sem e-mails (docs/02: nada de dado pessoal no marco 1)
