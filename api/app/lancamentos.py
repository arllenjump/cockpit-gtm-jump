"""Página Lançamentos (etapa 8): briefing e estudo da fase 1."""
import json

import anthropic
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from app import estudo as agente
from app.auth import usuario_logado
from app.config import env
from app.db import engine

router = APIRouter(prefix="/api/lancamentos", dependencies=[Depends(usuario_logado)])

PRODUTO = "opt3"  # piloto: só o OPT-3


class Briefing(BaseModel):
    objetivo: str = Field(min_length=1)
    contexto: str = ""
    provas: str = ""
    prazo_dias: int = Field(default=42, ge=1, le=365)


def custo_do_mes(conn) -> dict:
    gasto = conn.execute(
        text("select coalesce(sum(cost_estimate), 0) from agent_log where created_at >= date_trunc('month', now())")
    ).scalar_one()
    teto = float(env("CLAUDE_MONTHLY_BUDGET_USD", "50"))
    gasto = float(gasto)
    return {"gasto_usd": round(gasto, 4), "teto_usd": teto, "alerta": gasto >= 0.8 * teto}


@router.get("")
def atual():
    with engine.connect() as conn:
        lancamento = conn.execute(
            text(
                """select l.id, l.phase, l.status, l.started_at, l.created_by,
                          b.id as briefing_id, b.objetivo, b.contexto, b.provas, b.prazo_dias
                   from launches l join products p on p.id = l.product_id
                   left join briefings b on b.launch_id = l.id
                   where p.slug = :slug order by l.id desc, b.id desc limit 1"""
            ),
            {"slug": PRODUTO},
        ).mappings().first()
        estudo = None
        if lancamento:
            estudo = conn.execute(
                text("select id, content, sources, status, created_at from studies where launch_id = :l order by id desc limit 1"),
                {"l": lancamento["id"]},
            ).mappings().first()
        return {
            "produto": "OPT-3",
            "lancamento": dict(lancamento) if lancamento else None,
            "estudo": dict(estudo) if estudo else None,
            "custo": custo_do_mes(conn),
        }


@router.post("")
def criar(briefing: Briefing, usuario: dict = Depends(usuario_logado)):
    with engine.begin() as conn:
        produto_id = conn.execute(text("select id from products where slug = :s"), {"s": PRODUTO}).scalar_one()
        lancamento_id = conn.execute(
            text("insert into launches (product_id, created_by) values (:p, :e) returning id"),
            {"p": produto_id, "e": usuario["email"]},
        ).scalar_one()
        conn.execute(
            text(
                """insert into briefings (launch_id, objetivo, contexto, provas, prazo_dias, created_by)
                   values (:l, :o, :c, :pr, :d, :e)"""
            ),
            {"l": lancamento_id, "o": briefing.objetivo, "c": briefing.contexto, "pr": briefing.provas,
             "d": briefing.prazo_dias, "e": usuario["email"]},
        )
    return {"id": lancamento_id}


@router.post("/{lancamento_id}/estudo")
def gerar_estudo(lancamento_id: int):
    if not env("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=503, detail="A chave da Claude (ANTHROPIC_API_KEY) ainda não foi configurada.")
    with engine.connect() as conn:
        b = conn.execute(
            text("select id, objetivo, contexto, provas, prazo_dias from briefings where launch_id = :l order by id desc limit 1"),
            {"l": lancamento_id},
        ).mappings().first()
    if not b:
        raise HTTPException(status_code=404, detail="Lançamento sem briefing.")
    briefing = {k: b[k] for k in ("objetivo", "contexto", "provas", "prazo_dias")}
    logs: list[int] = []

    def registrar(resposta, modelo, tentativa, problemas):
        uso = resposta.usage
        servido = getattr(resposta, "model", None) or modelo
        with engine.begin() as conn:
            logs.append(
                conn.execute(
                    text(
                        """insert into agent_log (agent, action, input_ref, output_ref, model, tokens_in, tokens_out, cost_estimate)
                           values (:a, :ac, cast(:i as jsonb), cast(:o as jsonb), :m, :ti, :to, :c) returning id"""
                    ),
                    {
                        "a": agente.AGENTE,
                        "ac": f"gerar_estudo (tentativa {tentativa})",
                        "i": json.dumps({"launch_id": lancamento_id, "briefing_id": b["id"]}),
                        "o": json.dumps({"ok": not problemas, "problemas": problemas, "stop_reason": resposta.stop_reason,
                                         "request_id": getattr(resposta, "_request_id", None)}, ensure_ascii=False),
                        "m": servido,
                        "ti": uso.input_tokens,
                        "to": uso.output_tokens,
                        "c": agente.custo(servido, uso.input_tokens, uso.output_tokens),
                    },
                ).scalar_one()
            )

    try:
        resultado = agente.gerar(briefing, "OPT-3", registrar)
    except agente.EstudoInvalido as erro:
        raise HTTPException(status_code=422, detail=f"O estudo não passou na checagem depois de duas tentativas: {erro}")
    except anthropic.APIError as erro:
        raise HTTPException(status_code=502, detail=f"Falha ao chamar a Claude ({type(erro).__name__}).")

    with engine.begin() as conn:
        estudo_id = conn.execute(
            text("insert into studies (launch_id, content, sources) values (:l, cast(:c as jsonb), cast(:s as jsonb)) returning id"),
            {"l": lancamento_id, "c": json.dumps(resultado["estudo"], ensure_ascii=False),
             "s": json.dumps(resultado["fontes"], ensure_ascii=False)},
        ).scalar_one()
        conn.execute(
            text("update agent_log set output_ref = output_ref || cast(:o as jsonb) where id = :id"),
            {"o": json.dumps({"study_id": estudo_id}), "id": logs[-1]},
        )
    return {"id": estudo_id, **resultado}
