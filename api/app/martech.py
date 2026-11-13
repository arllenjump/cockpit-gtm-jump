"""Martech-monitor (servidor MCP) para o agente de estudo (docs/03-integracoes.md).

Modo escolhido por MARTECH_MODE:
- fixture: lê api/fixtures/martech-monitor.json (fotografia real, usada até o cockpit ter chave própria).
- mcp: chama o servidor em MARTECH_MCP_URL; a chave vai na query (?key=), como o servidor espera.
"""
import asyncio
import json
from pathlib import Path
from urllib.parse import urlencode

from fastapi import APIRouter, Depends

from app.auth import usuario_logado
from app.config import env

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "martech-monitor.json"

# As 6 ferramentas usadas no marco 1, com os argumentos de docs/03-integracoes.md.
CHAMADAS = [
    ("jump_get_profile", {}),
    ("jump_get_brief", {"params": {"days": 60}}),
    ("jump_list_competitors", {"params": {}}),
    ("jump_list_signals", {"params": {}}),
    ("jump_list_opportunities", {"params": {}}),
    ("martech_list_themes", {"params": {"status": "active"}}),
]


def modo() -> str:
    return env("MARTECH_MODE", "fixture")


def ler_resultado(texto: str):
    """O servidor devolve JSON; às vezes embrulhado em {"result": "<json>"}."""
    dado = json.loads(texto)
    if isinstance(dado, dict) and set(dado) == {"result"} and isinstance(dado["result"], str):
        return json.loads(dado["result"])
    return dado


def _url() -> str:
    url = env("MARTECH_MCP_URL", "https://martech-monitor-production.up.railway.app/mcp")
    chave = env("MARTECH_MCP_KEY")
    return f"{url}?{urlencode({'key': chave})}" if chave else url


async def _coletar_mcp() -> dict:
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    respostas = {}
    async with streamablehttp_client(_url()) as (leitura, escrita, _):
        async with ClientSession(leitura, escrita) as sessao:
            await sessao.initialize()
            for nome, argumentos in CHAMADAS:
                r = await sessao.call_tool(nome, argumentos)
                if getattr(r, "isError", False):
                    raise RuntimeError(f"{nome} devolveu erro: {r.content[0].text if r.content else ''}")
                respostas[nome] = ler_resultado(r.content[0].text)
    return respostas


def _motivo(erro: BaseException) -> str:
    """Descreve a falha sem repetir a URL (que leva a chave)."""
    for sub in getattr(erro, "exceptions", []):
        return _motivo(sub)
    resposta = getattr(erro, "response", None)
    if resposta is not None:
        return f"o servidor respondeu HTTP {resposta.status_code}"
    return type(erro).__name__


def coletar() -> dict:
    """Respostas das 6 ferramentas, por nome."""
    if modo() == "fixture":
        return json.loads(FIXTURE.read_text(encoding="utf-8"))["respostas"]
    if modo() == "mcp":
        try:
            return asyncio.run(_coletar_mcp())
        except Exception as erro:
            raise RuntimeError(f"Falha ao chamar o martech-monitor: {_motivo(erro)}") from None
    raise ValueError(f"MARTECH_MODE inválido: {modo()!r} (use 'fixture' ou 'mcp').")


def resumo(respostas: dict) -> dict:
    return {
        "modo": modo(),
        "perfil": respostas["jump_get_profile"]["profile"]["name"],
        "concorrentes": respostas["jump_list_competitors"]["total"],
        "sinais": respostas["jump_list_signals"]["total"],
        "oportunidades": respostas["jump_list_opportunities"]["count"],
        "temas_ativos": respostas["martech_list_themes"]["count"],
        "sinais_no_brief_60_dias": len(respostas["jump_get_brief"]["jump_competitor_signals"]),
    }


router = APIRouter(prefix="/api/martech", dependencies=[Depends(usuario_logado)])


@router.get("/verificacao")
def verificacao():
    try:
        return {"ok": True, **resumo(coletar())}
    except Exception as erro:
        return {"ok": False, "modo": modo(), "erro": str(erro)}
