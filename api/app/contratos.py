"""Página Contrato de GTM (etapa 12): tabela, edição por cláusula, aprovação e versão."""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from app.auditoria import CHAVES, auditar
from app.auth import usuario_logado
from app.db import engine

router = APIRouter(prefix="/api/contratos", dependencies=[Depends(usuario_logado)])

PRODUTO = "opt3"  # piloto: só o OPT-3
EDITAVEIS = ("rascunho", "em_revisao")


def _testes(conn, contrato_id: int) -> list[dict]:
    return [
        dict(t)
        for t in conn.execute(
            text(
                """select id, code, hypothesis, path_a, path_b, fast_signal, slow_signal, expected_range, decision_rule, status
                   from test_hypotheses where contract_id = :c order by code"""
            ),
            {"c": contrato_id},
        ).mappings()
    ]


def _clausulas(conn, contrato_id: int) -> list[dict]:
    linhas = {
        k["clause_key"]: dict(k)
        for k in conn.execute(
            text(
                """select clause_key, strategy, execution, owner_area, audit_verdict, audit_note, reviewed_at
                   from contract_clauses where contract_id = :c"""
            ),
            {"c": contrato_id},
        ).mappings()
    }
    return [linhas[k] for k in CHAVES if k in linhas]


@router.get("/atual")
def atual():
    with engine.connect() as conn:
        versoes = conn.execute(
            text(
                """select c.id, c.version, c.status, c.created_at, c.launch_id
                   from gtm_contracts c join products p on p.id = c.product_id
                   where p.slug = :s order by c.version desc"""
            ),
            {"s": PRODUTO},
        ).mappings().all()
        if not versoes:
            return {"contrato": None, "versoes": []}
        c = dict(versoes[0])
        aprovacao = conn.execute(
            text(
                """select id, status, note, decided_by, decided_at from approvals
                   where item_type = 'contrato' and item_id = :c order by id desc limit 1"""
            ),
            {"c": c["id"]},
        ).mappings().first()
        c["clausulas"] = _clausulas(conn, c["id"])
        c["testes"] = _testes(conn, c["id"])
        c["aprovacao"] = dict(aprovacao) if aprovacao else None
    return {"contrato": c, "versoes": [dict(v) for v in versoes]}


class Edicao(BaseModel):
    estrategia: str
    execucao: str


@router.put("/{contrato_id}/clausulas/{chave}")
def editar(contrato_id: int, chave: str, edicao: Edicao):
    """A primeira edição de uma versão do agente cria a próxima versão (em_revisao); as seguintes alteram essa versão.
    A auditoria roda de novo só na cláusula editada."""
    if chave not in CHAVES:
        raise HTTPException(status_code=404, detail="Cláusula inexistente.")
    with engine.begin() as conn:
        c = conn.execute(
            text(
                """select c.id, c.version, c.status, c.product_id, c.launch_id, p.slug from gtm_contracts c
                   join products p on p.id = c.product_id where c.id = :c for update of c"""
            ),
            {"c": contrato_id},
        ).mappings().first()
        if not c:
            raise HTTPException(status_code=404, detail="Contrato não encontrado.")
        ultima = conn.execute(text("select max(version) from gtm_contracts where product_id = :p"), {"p": c["product_id"]}).scalar_one()
        if c["status"] not in EDITAVEIS or c["version"] != ultima:
            raise HTTPException(status_code=409, detail="Só a versão mais nova, ainda não aprovada, pode ser editada.")

        alvo = c["id"]
        if c["status"] == "rascunho":
            alvo = conn.execute(
                text(
                    """insert into gtm_contracts (product_id, launch_id, version, status)
                       values (:p, :l, :v, 'em_revisao') returning id"""
                ),
                {"p": c["product_id"], "l": c["launch_id"], "v": ultima + 1},
            ).scalar_one()
            conn.execute(
                text(
                    """insert into contract_clauses (contract_id, clause_key, strategy, execution, owner_area, audit_verdict, audit_note, reviewed_at)
                       select :novo, clause_key, strategy, execution, owner_area, audit_verdict, audit_note, reviewed_at
                       from contract_clauses where contract_id = :c"""
                ),
                {"novo": alvo, "c": c["id"]},
            )
            conn.execute(
                text(
                    """insert into test_hypotheses
                       (contract_id, code, hypothesis, path_a, path_b, fast_signal, slow_signal, expected_range, decision_rule, status, decision, learning)
                       select :novo, code, hypothesis, path_a, path_b, fast_signal, slow_signal, expected_range, decision_rule, status, decision, learning
                       from test_hypotheses where contract_id = :c"""
                ),
                {"novo": alvo, "c": c["id"]},
            )
            conn.execute(
                text(
                    """update approvals set item_id = :novo, summary = :r
                       where item_type = 'contrato' and status = 'pendente' and item_id = :c"""
                ),
                {"novo": alvo, "c": c["id"], "r": f"Contrato de GTM v{ultima + 1} do OPT-3 (lançamento {c['launch_id']})"},
            )

        conn.execute(
            text("update contract_clauses set strategy = :e, execution = :x where contract_id = :c and clause_key = :k"),
            {"e": edicao.estrategia, "x": edicao.execucao, "c": alvo, "k": chave},
        )
        clausulas = [
            {"key": k["clause_key"], "estrategia": k["strategy"] or "", "execucao": k["execution"] or ""}
            for k in _clausulas(conn, alvo)
        ]
        testes = [{"status": t["status"]} for t in _testes(conn, alvo)]
        v = auditar(clausulas, testes, c["slug"])[chave]
        conn.execute(
            text(
                """update contract_clauses set audit_verdict = :v, audit_note = :n, reviewed_at = now()
                   where contract_id = :c and clause_key = :k"""
            ),
            {"v": v["veredito"], "n": v["nota"] or None, "c": alvo, "k": chave},
        )
        versao = conn.execute(text("select version from gtm_contracts where id = :c"), {"c": alvo}).scalar_one()
    return {"id": alvo, "versao": versao, "veredito": v["veredito"], "nota": v["nota"]}


def decidir_contrato(contrato_id: int, acao: str, nota: str, email: str) -> dict:
    """Aprovar e ajustar (aprovar com ressalva): a versão vira aprovada, as anteriores substituídas, fase 2 para 3.
    Devolver: o agente refaz o contrato com a instrução."""
    nota = nota.strip()
    if acao in ("ajustar", "devolver") and not nota:
        raise HTTPException(status_code=422, detail="Escreva a nota (ajustar) ou a instrução (devolver).")
    with engine.begin() as conn:
        item = conn.execute(
            text(
                """select a.id as aprovacao_id, a.status, c.product_id, c.launch_id, c.version
                   from approvals a join gtm_contracts c on c.id = a.item_id
                   where a.item_type = 'contrato' and a.item_id = :id for update of a"""
            ),
            {"id": contrato_id},
        ).mappings().first()
        if not item:
            raise HTTPException(status_code=404, detail="Contrato não encontrado na fila de aprovação.")
        if item["status"] != "pendente":
            raise HTTPException(status_code=409, detail="Este contrato já foi decidido.")
        status_aprovacao = {"aprovar": "aprovado", "ajustar": "ajustado", "devolver": "devolvido"}[acao]
        conn.execute(
            text("update approvals set status = :st, note = :nota, decided_by = :email, decided_at = now() where id = :id"),
            {"st": status_aprovacao, "nota": nota or None, "email": email, "id": item["aprovacao_id"]},
        )
        if acao == "devolver":
            return {"status": status_aprovacao, "fase": 2}
        conn.execute(text("update gtm_contracts set status = 'aprovado' where id = :id"), {"id": contrato_id})
        conn.execute(
            text("update gtm_contracts set status = 'substituido' where product_id = :p and id <> :id and status <> 'substituido'"),
            {"p": item["product_id"], "id": contrato_id},
        )
        conn.execute(text("update launches set phase = 3 where id = :l"), {"l": item["launch_id"]})
        entrou = conn.execute(
            text(
                """select max(exited_at) from gate_events
                   where launch_id = :l and to_phase = 2 and advanced"""
            ),
            {"l": item["launch_id"]},
        ).scalar()
        conn.execute(
            text(
                """insert into gate_events (product_id, launch_id, from_phase, to_phase, advanced, entered_at)
                   values (:p, :l, 2, 3, true, :entrou)"""
            ),
            {"p": item["product_id"], "l": item["launch_id"], "entrou": entrou},
        )
    return {"status": status_aprovacao, "fase": 3}


class Decisao(BaseModel):
    acao: Literal["aprovar", "ajustar", "devolver"]
    nota: str = ""


@router.post("/{contrato_id}/decisao")
def decidir(contrato_id: int, decisao: Decisao, usuario: dict = Depends(usuario_logado)):
    return decidir_contrato(contrato_id, decisao.acao, decisao.nota, usuario["email"])
