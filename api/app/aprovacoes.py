"""Página Aprovações (etapa 13): fila única de tudo que precisa de decisão humana."""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from app.auth import usuario_logado
from app.contratos import decidir_contrato
from app.db import engine
from app.lancamentos import decidir_estudo

router = APIRouter(prefix="/api/aprovacoes", dependencies=[Depends(usuario_logado)])

CAMPOS = "id, item_type, item_id, phase, summary, status, note, decided_by, decided_at, created_at"


class Decisao(BaseModel):
    acao: Literal["aprovar", "ajustar", "devolver"]
    nota: str = ""


@router.get("")
def fila():
    with engine.connect() as conn:
        pendentes = conn.execute(text(f"select {CAMPOS} from approvals where status = 'pendente' order by created_at")).mappings().all()
        decididos = conn.execute(
            text(f"select {CAMPOS} from approvals where status <> 'pendente' order by decided_at desc nulls last limit 20")
        ).mappings().all()
    return {"pendentes": [dict(a) for a in pendentes], "decididos": [dict(a) for a in decididos]}


@router.post("/{aprovacao_id}/decisao")
def decidir(aprovacao_id: int, decisao: Decisao, usuario: dict = Depends(usuario_logado)):
    with engine.connect() as conn:
        item = conn.execute(
            text("select item_type, item_id, status from approvals where id = :id"), {"id": aprovacao_id}
        ).mappings().first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado na fila.")
    if item["status"] != "pendente":
        raise HTTPException(status_code=409, detail="Este item já foi decidido.")
    if item["item_type"] == "estudo":
        return decidir_estudo(item["item_id"], decisao.acao, decisao.nota, usuario["email"])
    if item["item_type"] == "contrato":
        return decidir_contrato(item["item_id"], decisao.acao, decisao.nota, usuario["email"])
    # A lista de contas já nasce aprovada.
    raise HTTPException(status_code=422, detail=f"Itens do tipo {item['item_type']} não são decididos pela fila.")
