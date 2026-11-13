"""Página Lançamentos (etapa 8): briefing e estudo da fase 1."""
import json
from typing import Literal

import anthropic
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from app import contrato as agente_contrato
from app import estudo as agente
from app.auditoria import auditar
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


def registrador(nome_agente: str, acao: str, entrada: dict, logs: list[int]):
    """Devolve a função que grava cada chamada à Claude em agent_log (tokens, custo, problemas)."""

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
                        "a": nome_agente,
                        "ac": f"{acao} (tentativa {tentativa})",
                        "i": json.dumps(entrada),
                        "o": json.dumps({"ok": not problemas, "problemas": problemas, "stop_reason": resposta.stop_reason,
                                         "request_id": getattr(resposta, "_request_id", None)}, ensure_ascii=False),
                        "m": servido,
                        "ti": uso.input_tokens,
                        "to": uso.output_tokens,
                        "c": agente.custo(servido, uso.input_tokens, uso.output_tokens),
                    },
                ).scalar_one()
            )

    return registrar


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
                text(
                    """select s.id, s.content, s.sources, s.status, s.created_at,
                              a.status as aprovacao, a.note as nota, a.decided_by, a.decided_at
                       from studies s left join approvals a on a.item_type = 'estudo' and a.item_id = s.id
                       where s.launch_id = :l order by s.id desc limit 1"""
                ),
                {"l": lancamento["id"]},
            ).mappings().first()
        contrato = None
        if lancamento:
            contrato = conn.execute(
                text(
                    """select c.id, c.version, c.status, c.created_at,
                              count(*) filter (where k.audit_verdict = 'alinhado') as alinhado,
                              count(*) filter (where k.audit_verdict = 'ajustar') as ajustar,
                              count(*) filter (where k.audit_verdict = 'conflito') as conflito
                       from gtm_contracts c join contract_clauses k on k.contract_id = c.id
                       where c.launch_id = :l group by c.id order by c.version desc limit 1"""
                ),
                {"l": lancamento["id"]},
            ).mappings().first()
        return {
            "produto": "OPT-3",
            "lancamento": dict(lancamento) if lancamento else None,
            "estudo": dict(estudo) if estudo else None,
            "contrato": dict(contrato) if contrato else None,
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
    with engine.connect() as conn:
        instrucao = conn.execute(
            text(
                """select a.note from studies s join approvals a on a.item_type = 'estudo' and a.item_id = s.id
                   where s.launch_id = :l and s.status = 'devolvido'
                     and s.id = (select max(id) from studies where launch_id = :l)
                   order by a.id desc limit 1"""
            ),
            {"l": lancamento_id},
        ).scalar()
    logs: list[int] = []
    registrar = registrador(agente.AGENTE, "gerar_estudo", {"launch_id": lancamento_id, "briefing_id": b["id"]}, logs)

    try:
        resultado = agente.gerar(briefing, "OPT-3", registrar, instrucao)
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
        # Fila de aprovação: o estudo só avança com decisão humana (etapa 9).
        conn.execute(
            text(
                """insert into approvals (item_type, item_id, phase, summary)
                   values ('estudo', :id, 1, :resumo)"""
            ),
            {"id": estudo_id, "resumo": f"Estudo da fase 1 do OPT-3 (lançamento {lancamento_id})"},
        )
    return {"id": estudo_id, **resultado}


class Decisao(BaseModel):
    acao: Literal["aprovar", "ajustar", "devolver"]
    nota: str = ""


@router.post("/estudos/{estudo_id}/decisao")
def decidir(estudo_id: int, decisao: Decisao, usuario: dict = Depends(usuario_logado)):
    return decidir_estudo(estudo_id, decisao.acao, decisao.nota, usuario["email"])


def decidir_estudo(estudo_id: int, acao: str, nota: str, email: str) -> dict:
    """Aprovar e ajustar (aprovar com ressalva) avançam da fase 1 para a 2; devolver volta ao agente."""
    nota = nota.strip()
    if acao in ("ajustar", "devolver") and not nota:
        raise HTTPException(status_code=422, detail="Escreva a nota (ajustar) ou a instrução (devolver).")
    with engine.begin() as conn:
        item = conn.execute(
            text(
                """select a.id as aprovacao_id, a.status, s.launch_id, l.product_id, l.started_at
                   from approvals a join studies s on s.id = a.item_id join launches l on l.id = s.launch_id
                   where a.item_type = 'estudo' and a.item_id = :id for update of a"""
            ),
            {"id": estudo_id},
        ).mappings().first()
        if not item:
            raise HTTPException(status_code=404, detail="Estudo não encontrado na fila de aprovação.")
        if item["status"] != "pendente":
            raise HTTPException(status_code=409, detail="Este estudo já foi decidido.")
        status_aprovacao = {"aprovar": "aprovado", "ajustar": "ajustado", "devolver": "devolvido"}[acao]
        conn.execute(
            text(
                """update approvals set status = :st, note = :nota, decided_by = :email, decided_at = now()
                   where id = :id"""
            ),
            {"st": status_aprovacao, "nota": nota or None, "email": email, "id": item["aprovacao_id"]},
        )
        if acao == "devolver":
            conn.execute(text("update studies set status = 'devolvido' where id = :id"), {"id": estudo_id})
            return {"status": status_aprovacao, "fase": 1}
        conn.execute(text("update studies set status = 'aprovado' where id = :id"), {"id": estudo_id})
        conn.execute(text("update launches set phase = 2 where id = :id"), {"id": item["launch_id"]})
        conn.execute(
            text(
                """insert into gate_events (product_id, launch_id, from_phase, to_phase, advanced, entered_at)
                   values (:p, :l, 1, 2, true, :entrou)"""
            ),
            {"p": item["product_id"], "l": item["launch_id"], "entrou": item["started_at"]},
        )
    return {"status": status_aprovacao, "fase": 2}


@router.post("/{lancamento_id}/contrato")
def gerar_contrato(lancamento_id: int):
    """Etapa 11: gera as 10 cláusulas e os testes, aplica a auditoria fixa e grava a próxima versão do contrato."""
    if not env("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=503, detail="A chave da Claude (ANTHROPIC_API_KEY) ainda não foi configurada.")
    with engine.connect() as conn:
        lanc = conn.execute(
            text(
                """select l.id, l.phase, l.product_id, p.slug from launches l join products p on p.id = l.product_id
                   where l.id = :l"""
            ),
            {"l": lancamento_id},
        ).mappings().first()
        if not lanc:
            raise HTTPException(status_code=404, detail="Lançamento não encontrado.")
        if lanc["phase"] < 2:
            raise HTTPException(status_code=409, detail="O contrato só é gerado depois que o estudo for aprovado (fase 2).")
        b = conn.execute(
            text("select objetivo, contexto, provas, prazo_dias from briefings where launch_id = :l order by id desc limit 1"),
            {"l": lancamento_id},
        ).mappings().first()
        e = conn.execute(
            text(
                """select s.id, s.content, a.note from studies s
                   join approvals a on a.item_type = 'estudo' and a.item_id = s.id
                   where s.launch_id = :l and s.status = 'aprovado' order by s.id desc limit 1"""
            ),
            {"l": lancamento_id},
        ).mappings().first()
        instrucao = conn.execute(
            text(
                """select a.note from approvals a join gtm_contracts c on c.id = a.item_id
                   where a.item_type = 'contrato' and a.status = 'devolvido' and c.launch_id = :l
                     and c.id = (select max(id) from gtm_contracts where launch_id = :l)
                   order by a.id desc limit 1"""
            ),
            {"l": lancamento_id},
        ).scalar()
    contexto = {"produto": "OPT-3", "briefing": dict(b), "estudo_aprovado": e["content"]}
    if instrucao:
        # Contrato anterior devolvido pelo marketing: a instrução orienta a nova versão.
        contexto["instrucao_do_marketing"] = instrucao
    if e["note"]:
        contexto["ressalva_do_marketing"] = e["note"]
    logs: list[int] = []
    registrar = registrador(agente_contrato.AGENTE, "gerar_contrato", {"launch_id": lancamento_id, "study_id": e["id"]}, logs)

    try:
        contrato = agente_contrato.gerar(contexto, registrar)
    except agente_contrato.ContratoInvalido as erro:
        raise HTTPException(status_code=422, detail=f"O contrato não passou na checagem depois de duas tentativas: {erro}")
    except anthropic.APIError as erro:
        raise HTTPException(status_code=502, detail=f"Falha ao chamar a Claude ({type(erro).__name__}).")

    vereditos = auditar(contrato["clausulas"], contrato["testes"], lanc["slug"])
    with engine.begin() as conn:
        versao = conn.execute(
            text("select coalesce(max(version), 0) + 1 from gtm_contracts where product_id = :p"), {"p": lanc["product_id"]}
        ).scalar_one()
        contrato_id = conn.execute(
            text("insert into gtm_contracts (product_id, launch_id, version) values (:p, :l, :v) returning id"),
            {"p": lanc["product_id"], "l": lancamento_id, "v": versao},
        ).scalar_one()
        for c in contrato["clausulas"]:
            v = vereditos[c["key"]]
            conn.execute(
                text(
                    """insert into contract_clauses (contract_id, clause_key, strategy, execution, audit_verdict, audit_note, reviewed_at)
                       values (:c, :k, :e, :x, :v, :n, now())"""
                ),
                {"c": contrato_id, "k": c["key"], "e": c["estrategia"], "x": c["execucao"], "v": v["veredito"], "n": v["nota"] or None},
            )
        for t in contrato["testes"]:
            conn.execute(
                text(
                    """insert into test_hypotheses
                       (contract_id, code, hypothesis, path_a, path_b, fast_signal, slow_signal, expected_range, decision_rule, status)
                       values (:c, :cod, :h, :a, :b, :fs, :ss, cast(:fx as jsonb), :r, :st)"""
                ),
                {"c": contrato_id, "cod": t["codigo"], "h": t["hipotese"], "a": t["caminho_a"], "b": t["caminho_b"],
                 "fs": t["sinal_rapido"], "ss": t["sinal_lento"], "fx": json.dumps({"texto": t["faixa_prevista"]}, ensure_ascii=False),
                 "r": t["regra"], "st": t["status"]},
            )
        conn.execute(
            text("update agent_log set output_ref = output_ref || cast(:o as jsonb) where id = :id"),
            {"o": json.dumps({"contract_id": contrato_id}), "id": logs[-1]},
        )
        contagem = {k: sum(1 for v in vereditos.values() if v["veredito"] == k) for k in ("alinhado", "ajustar", "conflito")}
        conn.execute(
            text(
                """insert into agent_log (agent, action, input_ref, output_ref)
                   values ('auditoria', 'auditoria_fixa', cast(:i as jsonb), cast(:o as jsonb))"""
            ),
            {"i": json.dumps({"contract_id": contrato_id}), "o": json.dumps(contagem)},
        )
        # Fila de aprovação: um item pendente por lançamento, sempre apontando para a versão mais nova.
        resumo = f"Contrato de GTM v{versao} do OPT-3 (lançamento {lancamento_id})"
        repontado = conn.execute(
            text(
                """update approvals set item_id = :c, summary = :r
                   where item_type = 'contrato' and status = 'pendente'
                     and item_id in (select id from gtm_contracts where launch_id = :l)"""
            ),
            {"c": contrato_id, "r": resumo, "l": lancamento_id},
        ).rowcount
        if not repontado:
            conn.execute(
                text("insert into approvals (item_type, item_id, phase, summary) values ('contrato', :c, 2, :r)"),
                {"c": contrato_id, "r": resumo},
            )
    return {"id": contrato_id, "versao": versao, "clausulas": len(contrato["clausulas"]), "vereditos": contagem}
