"""Página Contas (etapa 6): lista do ICP Jump, dossiê e validação semanal."""
import json
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from app import icp_jump
from app.auth import usuario_logado
from app.db import engine

router = APIRouter(prefix="/api/contas", dependencies=[Depends(usuario_logado)])

PRODUTO = "opt3"  # piloto: só o OPT-3


def semana_atual() -> str:
    ano, semana, _ = datetime.now(ZoneInfo("America/Sao_Paulo")).isocalendar()
    return f"{ano}-W{semana:02d}"


def _validacao_da_semana(conn, semana: str) -> dict | None:
    linha = conn.execute(
        text(
            """select v.id, v.validated_by, v.validated_at, jsonb_array_length(v.account_ids) as total
               from account_list_validations v join products p on p.id = v.product_id
               where p.slug = :slug and v.week = :semana order by v.id desc limit 1"""
        ),
        {"slug": PRODUTO, "semana": semana},
    ).mappings().first()
    return dict(linha) if linha else None


@router.get("")
def listar():
    semana = semana_atual()
    with engine.connect() as conn:
        validacao = _validacao_da_semana(conn, semana)
    return {
        "simulacao": icp_jump.modo() == "fixture",
        "semana": semana,
        "validacao": validacao,
        "contas": icp_jump.list_accounts(),
    }


@router.get("/{external_id}")
def detalhe(external_id: str):
    conta = icp_jump.get_account(external_id)
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    return conta


@router.post("/validar")
def validar(usuario: dict = Depends(usuario_logado)):
    semana = semana_atual()
    contas = icp_jump.list_accounts()
    ids = [c["external_id"] for c in contas]
    with engine.begin() as conn:
        if _validacao_da_semana(conn, semana):
            raise HTTPException(status_code=409, detail=f"A lista da semana {semana} já foi validada.")
        produto_id = conn.execute(text("select id from products where slug = :slug"), {"slug": PRODUTO}).scalar_one()
        validacao_id = conn.execute(
            text(
                """insert into account_list_validations (product_id, week, account_ids, validated_by)
                   values (:produto, :semana, cast(:ids as jsonb), :email) returning id"""
            ),
            {"produto": produto_id, "semana": semana, "ids": json.dumps(ids), "email": usuario["email"]},
        ).scalar_one()
        conn.execute(
            text(
                """insert into approvals (item_type, item_id, phase, summary, status, decided_by, decided_at)
                   values ('lista_contas', :item, 1, :resumo, 'aprovado', :email, now())"""
            ),
            {
                "item": validacao_id,
                "resumo": f"Lista de contas da semana {semana} ({len(ids)} contas)",
                "email": usuario["email"],
            },
        )
        # Snapshot para o histórico não depender do ICP Jump (docs/03-integracoes.md).
        for c in contas:
            conn.execute(
                text(
                    """insert into account_snapshots
                       (external_id, name, sector, employees, gtm_score, tier, signals, dossier, week)
                       values (:id, :nome, :setor, :func, :score, :tier, cast(:sinais as jsonb), cast(:dossie as jsonb), :semana)"""
                ),
                {
                    "id": c["external_id"],
                    "nome": c["name"],
                    "setor": c["sector"],
                    "func": c["employees"],
                    "score": c["gtm_score"],
                    "tier": c["tier"],
                    "sinais": json.dumps(c["signals"], ensure_ascii=False),
                    "dossie": json.dumps({**c["dossier"], "decision_makers": c["decision_makers"]}, ensure_ascii=False),
                    "semana": semana,
                },
            )
        return _validacao_da_semana(conn, semana)
