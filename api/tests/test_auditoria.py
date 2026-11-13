import pytest

from app.auditoria import CHAVES, auditar

BLOQUEADOS = ["Cliente Fictício Ômega", "Banco Exemplo Sigma"]  # nomes fictícios


def contrato_limpo():
    clausulas = [{"key": k, "estrategia": f"Estratégia de {k}.", "execucao": f"Execução de {k}."} for k in CHAVES]
    for c in clausulas:
        if c["key"] == "sucesso":
            c["execucao"] = "Medir reuniões por conta e pipeline por conta."
    testes = [{"codigo": "H1", "status": "ativa"}, {"codigo": "H2", "status": "ativa"}, {"codigo": "H3", "status": "na_fila"}]
    return clausulas, testes


def mudar(clausulas, chave, **campos):
    next(c for c in clausulas if c["key"] == chave).update(campos)


def test_contrato_limpo_fica_todo_alinhado():
    clausulas, testes = contrato_limpo()
    r = auditar(clausulas, testes, "opt3", BLOQUEADOS)
    assert set(r) == set(CHAVES)
    assert all(v["veredito"] == "alinhado" and v["nota"] == "" for v in r.values())


# Regra 1
@pytest.mark.parametrize("campo", ["estrategia", "execucao"])
def test_r1_campo_vazio_ajustar(campo):
    clausulas, testes = contrato_limpo()
    mudar(clausulas, "icp", **{campo: "   "})
    assert auditar(clausulas, testes, "opt3", BLOQUEADOS)["icp"]["veredito"] == "ajustar"


def test_r1_clausula_ausente_ajustar():
    clausulas, testes = contrato_limpo()
    clausulas = [c for c in clausulas if c["key"] != "pausa"]
    r = auditar(clausulas, testes, "opt3", BLOQUEADOS)["pausa"]
    assert r == {"veredito": "ajustar", "nota": "Cláusula ausente."}


# Regra 2
@pytest.mark.parametrize("traco", ["—", "–"])
def test_r2_travessao_ajustar(traco):
    clausulas, testes = contrato_limpo()
    mudar(clausulas, "posicionamento", estrategia=f"Mensagem forte {traco} e clara.")
    assert auditar(clausulas, testes, "opt3", BLOQUEADOS)["posicionamento"]["veredito"] == "ajustar"


def test_r2_hifen_comum_nao_dispara():
    clausulas, testes = contrato_limpo()
    mudar(clausulas, "posicionamento", estrategia="Visão multi-cloud.")
    assert auditar(clausulas, testes, "opt3", BLOQUEADOS)["posicionamento"]["veredito"] == "alinhado"


# Regra 3
def test_r3_cliente_bloqueado_conflito_sem_acento_e_maiusculas():
    clausulas, testes = contrato_limpo()
    mudar(clausulas, "provas", execucao="Caso do cliente ficticio omega como prova.")
    r = auditar(clausulas, testes, "opt3", BLOQUEADOS)["provas"]
    assert r["veredito"] == "conflito"
    assert "Omega" not in r["nota"] and "omega" not in r["nota"]  # a nota não repete o nome


def test_r3_so_palavra_inteira():
    clausulas, testes = contrato_limpo()
    mudar(clausulas, "provas", execucao="Banco Exemplo Sigmaplus não está na lista.")
    assert auditar(clausulas, testes, "opt3", BLOQUEADOS)["provas"]["veredito"] == "alinhado"


def test_r3_lista_vem_da_variavel(monkeypatch):
    monkeypatch.setenv("BLOCKED_CLIENT_NAMES", "Cliente Fictício Ômega; Outro Nome")
    clausulas, testes = contrato_limpo()
    mudar(clausulas, "icp", estrategia="Focar em Outro Nome.")
    assert auditar(clausulas, testes, "opt3")["icp"]["veredito"] == "conflito"


# Regra 4
def test_r4_sucesso_sem_metrica_por_conta_conflito():
    clausulas, testes = contrato_limpo()
    mudar(clausulas, "sucesso", execucao="Medir leads gerados no total.")
    assert auditar(clausulas, testes, "opt3", BLOQUEADOS)["sucesso"]["veredito"] == "conflito"


# Regra 5
def test_r5_categoria_vazia_em_nova_categoria_conflito():
    clausulas, testes = contrato_limpo()
    mudar(clausulas, "categoria", estrategia="", execucao="")
    assert auditar(clausulas, testes, "radarai", BLOQUEADOS)["categoria"]["veredito"] == "conflito"


def test_r5_categoria_vazia_no_opt3_so_ajustar():
    clausulas, testes = contrato_limpo()
    mudar(clausulas, "categoria", estrategia="", execucao="")
    assert auditar(clausulas, testes, "opt3", BLOQUEADOS)["categoria"]["veredito"] == "ajustar"


# Regra 6
def test_r6_avaliacao_atras_de_formulario_ajustar():
    clausulas, testes = contrato_limpo()
    mudar(clausulas, "categoria", execucao="Business case disponível após cadastro em formulário.")
    assert auditar(clausulas, testes, "opt3", BLOQUEADOS)["categoria"]["veredito"] == "ajustar"


def test_r6_avaliacao_aberta_nao_dispara():
    clausulas, testes = contrato_limpo()
    mudar(clausulas, "categoria", execucao="Comparativo aberto no site, sem barreira.")
    assert auditar(clausulas, testes, "opt3", BLOQUEADOS)["categoria"]["veredito"] == "alinhado"


# Regra 7
def test_r7_mais_de_2_testes_ativos_conflito_em_sucesso():
    clausulas, testes = contrato_limpo()
    testes[2]["status"] = "ativa"
    r = auditar(clausulas, testes, "opt3", BLOQUEADOS)["sucesso"]
    assert r["veredito"] == "conflito"
    assert "3 testes ativos" in r["nota"]


# Prioridade e notas
def test_conflito_vence_ajustar_e_notas_se_somam():
    clausulas, testes = contrato_limpo()
    mudar(clausulas, "provas", estrategia="Prova — forte.", execucao="Caso Banco Exemplo Sigma.")
    r = auditar(clausulas, testes, "opt3", BLOQUEADOS)["provas"]
    assert r["veredito"] == "conflito"
    assert "travessão" in r["nota"] and "bloqueados" in r["nota"]
