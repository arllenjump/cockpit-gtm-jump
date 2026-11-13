"""Agente de contrato, fase 2 (docs/04-agentes.md, etapa 11 do plano).

Gera as 10 cláusulas e o plano de testes a partir do briefing, do estudo aprovado
e do resumo das contas; passa pela checagem fixa e pela auditoria da camada 1.
"""
import json
from collections import Counter

from app import estudo as base
from app import icp_jump
from app.auditoria import CHAVES
from app.config import env

AGENTE = "contrato"

ESQUEMA = {
    "type": "object",
    "properties": {
        "clausulas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "enum": CHAVES},
                    "estrategia": {"type": "string"},
                    "execucao": {"type": "string"},
                },
                "required": ["key", "estrategia", "execucao"],
                "additionalProperties": False,
            },
        },
        "testes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "codigo": {"type": "string"},
                    "hipotese": {"type": "string"},
                    "caminho_a": {"type": "string"},
                    "caminho_b": {"type": "string"},
                    "sinal_rapido": {"type": "string"},
                    "sinal_lento": {"type": "string"},
                    "faixa_prevista": {"type": "string"},
                    "regra": {"type": "string"},
                    "status": {"type": "string", "enum": ["ativa", "na_fila"]},
                },
                "required": ["codigo", "hipotese", "caminho_a", "caminho_b", "sinal_rapido", "sinal_lento", "faixa_prevista", "regra", "status"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["clausulas", "testes"],
    "additionalProperties": False,
}

# Os 10 itens do contrato (docs/00-contexto.md): estratégia e execução de cada chave.
# Apostas iniciais por produto (docs/04-agentes.md, "Apostas iniciais do OPT-3").
APOSTAS_INICIAIS = {
    "opt3": [
        {"codigo": "H1", "hipotese": "Para o CFO, a dor de custo engaja mais que governança",
         "caminho_a": "Custo da fatura de nuvem", "caminho_b": "Governança e controle",
         "sinal_rapido": "CTR e engajamento por conta", "sinal_lento": "Contas que viram SQL", "status": "ativa"},
        {"codigo": "H2", "hipotese": "O primeiro contato rende mais pelo CFO do que pelo CTO",
         "caminho_a": "Sequência pelo CFO", "caminho_b": "Sequência pelo CTO ou Diretor de TI",
         "sinal_rapido": "Taxa de resposta", "sinal_lento": "SQLs aceitos", "status": "ativa"},
        {"codigo": "H3", "hipotese": "Oferta de entrada sem reunião converte mais que pedir conversa",
         "caminho_a": "Material ou diagnóstico sem reunião", "caminho_b": "Falar com especialista",
         "sinal_rapido": "Conversão do anúncio", "sinal_lento": "Contas que vão à reunião", "status": "na_fila"},
    ],
}

ITENS = """icp: ICP | Filtros de conta e lista-alvo
comite: Comitê de compra por função | Kit de consenso por função
categoria: Justificativa da categoria | Conteúdo aberto de categoria e business case
gatilhos: Gatilhos positivos e reativos | Sinais de intenção classificados por tipo
posicionamento: Posicionamento e pontos de entrada | Mensagem por canal e frequência por conta
provas: Provas por voz (marca, especialista, par) | Distribuição por voz e dados estruturados
estagio: Estágio da conta | Scoring de conta e roteamento
validacao: Argumento de validação | Roteiro da primeira reunião e battlecard
pausa: Motivos de pausa | Fluxo de reciclagem
sucesso: Hipótese de sucesso e plano de testes | Métricas por conta e faixa prevista"""

SISTEMA = f"""Você é o agente de contrato da Operação GTM Jump. Escreve o contrato de GTM da fase 2 de um lançamento: as 10 cláusulas e o plano de testes, a partir do briefing, do estudo aprovado e do resumo das contas do ICP.

As 10 cláusulas, cada uma com estratégia e execução (chave: estratégia | execução):
{ITENS}

Regras obrigatórias:
- Escreva em português do Brasil.
- Nunca use travessão nem meia-risca. Use vírgula, ponto ou dois-pontos.
- Nunca cite nome de cliente da Jump. Provas permitidas: mais de 60 clientes, mais de 600 profissionais, ISO 27001, 27701, 42001, 9001 e 14001, prêmio Negócios em Expansão 2025 da Exame, AWS Partner Network. Só ao falar do OPT-3: ROI documentado de até 61% em otimização de custo (cerca de 36% já formalizado, medido com baseline caso a caso) e primeiros insights em 10 dias de onboarding.
- Não invente números, nomes de clientes ou ferramentas. Só use números que estejam no briefing, no estudo, no resumo das contas ou nas provas permitidas. Quando faltar dado, diga que falta.
- Exatamente uma cláusula para cada uma das 10 chaves, com estratégia e execução preenchidas.
- A execução da cláusula sucesso traz métricas por conta (escreva "por conta").
- Conteúdo de avaliação (business case, comparativo, compliance) fica aberto, nunca atrás de formulário ou cadastro.
- Plano de testes: no máximo 2 testes com status ativa e no máximo 1 na_fila. Códigos H1, H2, H3. Em faixa_prevista escreva "a calibrar com o histórico".
- Se houver apostas iniciais, parta delas: mantenha os códigos e os status e só mude uma aposta se o estudo aprovado justificar, dizendo o motivo na própria hipótese.
- Se houver ressalva do marketing sobre o estudo, leve em conta.
- Responda só com o JSON no formato pedido."""


class ContratoInvalido(Exception):
    pass


def resumo_contas() -> dict:
    contas = icp_jump.list_accounts(min_score=60)
    return {
        "contas_aderentes": len(contas),
        "setores": sorted({c["sector"] for c in contas}),
        "funcionarios_min_max": [min(c["employees"] for c in contas), max(c["employees"] for c in contas)] if contas else [],
        "sinais_mais_frequentes": Counter(s["type"] for c in contas for s in c["signals"]).most_common(5),
    }


def validar(contrato: dict) -> list[str]:
    problemas = []
    chaves = [c["key"] for c in contrato["clausulas"]]
    faltando = [k for k in CHAVES if k not in chaves]
    repetidas = sorted({k for k in chaves if chaves.count(k) > 1})
    if faltando:
        problemas.append(f"Faltam cláusulas: {', '.join(faltando)}.")
    if repetidas:
        problemas.append(f"Cláusulas repetidas: {', '.join(repetidas)}.")
    status = Counter(t["status"] for t in contrato["testes"])
    if status["ativa"] > 2:
        problemas.append(f"{status['ativa']} testes ativos; o máximo é 2.")
    if status["na_fila"] > 1:
        problemas.append(f"{status['na_fila']} testes na fila; o máximo é 1.")
    return problemas


def gerar(contexto: dict, registrar, produto: str = "opt3") -> dict:
    """`contexto`: produto, briefing, estudo aprovado e ressalva. Uma nova tentativa se falhar; depois ContratoInvalido."""
    modelo = env("CLAUDE_MODEL", "claude-sonnet-5-5")
    entrada = {**contexto, "resumo_das_contas": resumo_contas()}
    if produto in APOSTAS_INICIAIS:
        entrada["apostas_iniciais"] = APOSTAS_INICIAIS[produto]
    entrada_json = json.dumps(entrada, ensure_ascii=False)
    corpus = SISTEMA + "\n" + entrada_json
    mensagens = [{"role": "user", "content": f"Escreva o contrato de GTM da fase 2 para este lançamento.\n\n{entrada_json}"}]

    problemas: list[str] = []
    for tentativa in (1, 2):
        resposta = base.chamar_claude(mensagens, modelo, SISTEMA, ESQUEMA)
        if resposta.stop_reason == "refusal":
            problemas = ["A Claude recusou o pedido."]
        elif resposta.stop_reason == "max_tokens":
            problemas = ["A resposta foi cortada pelo limite de tokens."]
        else:
            texto = next((b.text for b in resposta.content if b.type == "text"), "")
            try:
                contrato = json.loads(texto)
                problemas = validar(contrato) + base.checar(contrato, corpus)
            except json.JSONDecodeError:
                problemas = ["A resposta não é um JSON válido."]
        registrar(resposta, modelo, tentativa, problemas)
        if not problemas:
            return contrato
        mensagens = mensagens + [
            {"role": "assistant", "content": resposta.content},
            {"role": "user", "content": "O contrato não passou na checagem: " + " ".join(problemas) + " Corrija e gere de novo."},
        ]
    raise ContratoInvalido(" ".join(problemas))
