"""Agente de estudo, fase 1 (docs/04-agentes.md, etapa 8 do plano).

Lê as fontes, pede o estudo à Claude em JSON (formato fixo), passa pela checagem
fixa e grava em `studies` e `agent_log`.
"""
import json
import re

import anthropic

from app import icp_jump, martech
from app.auditoria import TRAVESSOES, _cita, clientes_bloqueados
from app.config import env

AGENTE = "estudo"

# US$ por milhão de tokens (entrada, saída), da tabela de preços da Anthropic.
PRECOS = {
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-opus-5-5": (4.00, 20.00),
    "claude-haiku-5-5": (0.10, 0.50),
}

ESQUEMA = {
    "type": "object",
    "properties": {
        "mercado": {"type": "string"},
        "concorrentes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"nome": {"type": "string"}, "movimento": {"type": "string"}, "implicacao": {"type": "string"}},
                "required": ["nome", "movimento", "implicacao"],
                "additionalProperties": False,
            },
        },
        "oportunidades": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "titulo": {"type": "string"},
                    "porque": {"type": "string"},
                    "impacto": {"type": "string", "enum": ["baixo", "medio", "alto"]},
                },
                "required": ["titulo", "porque", "impacto"],
                "additionalProperties": False,
            },
        },
        "riscos": {"type": "array", "items": {"type": "string"}},
        "perguntas_em_aberto": {"type": "array", "items": {"type": "string"}},
        "fontes": {
            "type": "object",
            "properties": {
                "lidas": {"type": "array", "items": {"type": "string"}},
                "ausentes": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["lidas", "ausentes"],
            "additionalProperties": False,
        },
    },
    "required": ["mercado", "concorrentes", "oportunidades", "riscos", "perguntas_em_aberto", "fontes"],
    "additionalProperties": False,
}

SISTEMA = """Você é o agente de estudo da Operação GTM Jump. Faz o estudo de mercado da fase 1 de um lançamento, a partir do briefing e das fontes fornecidas.

Regras obrigatórias:
- Escreva em português do Brasil.
- Nunca use travessão nem meia-risca. Use vírgula, ponto ou dois-pontos.
- Nunca cite nome de cliente da Jump. Provas permitidas: mais de 60 clientes, mais de 600 profissionais, ISO 27001, 27701, 42001, 9001 e 14001, prêmio Negócios em Expansão 2025 da Exame, AWS Partner Network. Só ao falar do OPT-3: ROI documentado de até 61% em otimização de custo (cerca de 36% já formalizado, medido com baseline caso a caso) e primeiros insights em 10 dias de onboarding.
- Não invente números, nomes de clientes ou ferramentas. Só use números que estejam no briefing, nas fontes ou nas provas permitidas. Quando faltar dado, diga que falta e coloque em perguntas em aberto.
- Concorrentes são os listados nas fontes. Não acrescente outros.
- Em fontes, liste em "lidas" e "ausentes" exatamente os nomes de fonte informados.
- Responda só com o JSON no formato pedido."""


class EstudoInvalido(Exception):
    pass


def ler_fontes() -> tuple[dict, dict]:
    """Devolve (dados por fonte, {"lidas": [...], "ausentes": [...]})."""
    dados, lidas, ausentes = {}, [], []
    try:
        dados["martech-monitor"] = martech.coletar()
        lidas.append("martech-monitor")
    except Exception:
        ausentes.append("martech-monitor")
    try:
        aderentes = icp_jump.list_accounts(min_score=60)
        dados["ICP Jump"] = {
            "contas_aderentes_score_60_ou_mais": len(aderentes),
            "setores": sorted({c["sector"] for c in aderentes}),
        }
        lidas.append("ICP Jump")
    except Exception:
        ausentes.append("ICP Jump")
    ausentes.append("Jump Bases")  # fora do marco 1 (docs/03-integracoes.md)
    return dados, {"lidas": lidas, "ausentes": ausentes}


def _texto(estudo: dict) -> str:
    partes = []

    def coletar(v):
        if isinstance(v, str):
            partes.append(v)
        elif isinstance(v, list):
            for i in v:
                coletar(i)
        elif isinstance(v, dict):
            for i in v.values():
                coletar(i)

    coletar({k: v for k, v in estudo.items() if k != "fontes"})
    return "\n".join(partes)


def _numeros(texto: str) -> set[str]:
    return {re.sub(r"[.,]", "", n) for n in re.findall(r"\d+(?:[.,]\d+)*", texto)}


def checar(estudo: dict, corpus: str, bloqueados: list[str] | None = None) -> list[str]:
    """Checagem fixa do CLAUDE.md: sem travessão, sem nome de cliente, sem número inventado."""
    bloqueados = clientes_bloqueados() if bloqueados is None else bloqueados
    texto = _texto(estudo)
    problemas = []
    if any(t in texto for t in TRAVESSOES):
        problemas.append("O texto tem travessão ou meia-risca.")
    if any(_cita(texto, nome) for nome in bloqueados):
        problemas.append("O texto cita um nome da lista de clientes bloqueados.")
    inventados = sorted(_numeros(texto) - _numeros(corpus))
    if inventados:
        problemas.append(f"Números que não aparecem nas fontes nem no briefing: {', '.join(inventados)}.")
    return problemas


def custo(modelo: str, tokens_in: int, tokens_out: int) -> float | None:
    preco = PRECOS.get(modelo)
    if not preco:
        return None
    return round((tokens_in * preco[0] + tokens_out * preco[1]) / 1_000_000, 4)


def chamar_claude(mensagens: list[dict], modelo: str):
    """Uma chamada à Claude com saída presa ao ESQUEMA. Recusa vira fallback do servidor."""
    cliente = anthropic.Anthropic()
    return cliente.beta.messages.create(
        model=modelo,
        max_tokens=16000,
        system=SISTEMA,
        messages=mensagens,
        output_config={"format": {"type": "json_schema", "schema": ESQUEMA}},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )


def gerar(briefing: dict, produto: str, registrar, instrucao: str | None = None) -> dict:
    """Gera o estudo. `registrar(resposta, modelo, tentativa, problemas)` grava cada chamada em agent_log.

    Faz uma nova tentativa se o JSON ou a checagem falhar; na segunda falha levanta EstudoInvalido.
    """
    modelo = env("CLAUDE_MODEL", "claude-sonnet-5-5")
    dados, fontes = ler_fontes()
    entrada = {
        "produto": produto,
        "briefing": briefing,
        "fontes_lidas": fontes["lidas"],
        "fontes_ausentes": fontes["ausentes"],
        "dados": dados,
    }
    if instrucao:
        # Estudo anterior devolvido pelo marketing: a instrução orienta a nova versão.
        entrada["instrucao_do_marketing"] = instrucao
    entrada_json = json.dumps(entrada, ensure_ascii=False)
    corpus = SISTEMA + "\n" + entrada_json
    mensagens = [{"role": "user", "content": f"Gere o estudo da fase 1 para este lançamento.\n\n{entrada_json}"}]

    problemas: list[str] = []
    for tentativa in (1, 2):
        resposta = chamar_claude(mensagens, modelo)
        if resposta.stop_reason == "refusal":
            problemas = ["A Claude recusou o pedido."]
        elif resposta.stop_reason == "max_tokens":
            problemas = ["A resposta foi cortada pelo limite de tokens."]
        else:
            texto = next((b.text for b in resposta.content if b.type == "text"), "")
            try:
                estudo = json.loads(texto)
                problemas = checar(estudo, corpus)
            except json.JSONDecodeError:
                problemas = ["A resposta não é um JSON válido."]
        registrar(resposta, modelo, tentativa, problemas)
        if not problemas:
            estudo["fontes"] = fontes  # as fontes registradas são as que o sistema leu de fato
            return {"estudo": estudo, "fontes": fontes}
        mensagens = mensagens + [
            {"role": "assistant", "content": resposta.content},
            {"role": "user", "content": "O estudo não passou na checagem: " + " ".join(problemas) + " Corrija e gere de novo."},
        ]
    raise EstudoInvalido(" ".join(problemas))
