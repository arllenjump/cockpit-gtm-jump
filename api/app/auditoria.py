"""Auditoria fixa do contrato de GTM, camada 1 (docs/04-agentes.md).

Regras em código, sem IA. Cada cláusula recebe o veredito mais grave entre as
regras que dispararam (conflito > ajustar > alinhado) e a soma das notas.
"""
import re
import unicodedata

from app.config import env

CHAVES = ["icp", "comite", "categoria", "gatilhos", "posicionamento", "provas", "estagio", "validacao", "pausa", "sucesso"]

# Produtos de nova categoria (docs/04-agentes.md, regra 5), pelo slug de `products`.
NOVA_CATEGORIA = {"radarai", "adoption-ai"}

TRAVESSOES = ("—", "–")  # travessão e meia-risca
AVALIACAO = ("business case", "comparativo", "compliance")
FORMULARIO = ("formulario", "cadastro", "gated", "atras de")

GRAVIDADE = {"alinhado": 0, "ajustar": 1, "conflito": 2}


def normalizar(texto: str) -> str:
    """Minúsculas e sem acento, para comparar nomes e termos."""
    sem_acento = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return sem_acento.lower()


def clientes_bloqueados() -> list[str]:
    return [n.strip() for n in env("BLOCKED_CLIENT_NAMES").split(";") if n.strip()]


def _cita(texto: str, nome: str) -> bool:
    return re.search(rf"\b{re.escape(normalizar(nome))}\b", normalizar(texto)) is not None


def auditar(clausulas: list[dict], testes: list[dict], produto: str, bloqueados: list[str] | None = None) -> dict[str, dict]:
    """Recebe as cláusulas no formato do agente ({key, estrategia, execucao}) e os testes.

    Devolve {chave: {"veredito": ..., "nota": ...}} para as 10 chaves.
    """
    bloqueados = clientes_bloqueados() if bloqueados is None else bloqueados
    por_chave = {c["key"]: c for c in clausulas}
    achados: dict[str, list[tuple[str, str]]] = {k: [] for k in CHAVES}

    for chave in CHAVES:
        c = por_chave.get(chave)
        estrategia = (c or {}).get("estrategia", "") or ""
        execucao = (c or {}).get("execucao", "") or ""
        texto = f"{estrategia}\n{execucao}"
        norm = normalizar(texto)

        # 1. Estratégia ou execução vazia
        if c is None:
            achados[chave].append(("ajustar", "Cláusula ausente."))
        else:
            if not estrategia.strip():
                achados[chave].append(("ajustar", "Estratégia vazia."))
            if not execucao.strip():
                achados[chave].append(("ajustar", "Execução vazia."))

        # 2. Travessão
        if any(t in texto for t in TRAVESSOES):
            achados[chave].append(("ajustar", "Texto com travessão."))

        # 3. Cliente bloqueado
        if any(_cita(texto, nome) for nome in bloqueados):
            achados[chave].append(("conflito", "Cita um nome da lista de clientes bloqueados."))

        # 4. Sucesso sem métrica por conta
        if chave == "sucesso" and "por conta" not in normalizar(execucao):
            achados[chave].append(("conflito", "Sem métrica por conta na execução."))

        # 5. Categoria vazia em produto de nova categoria
        if chave == "categoria" and produto in NOVA_CATEGORIA and (not estrategia.strip() or not execucao.strip()):
            achados[chave].append(("conflito", "Produto de nova categoria exige a justificativa da categoria."))

        # 6. Conteúdo de avaliação atrás de formulário
        if any(t in norm for t in AVALIACAO) and any(t in norm for t in FORMULARIO):
            achados[chave].append(("ajustar", "Conteúdo de avaliação deve ser aberto, não atrás de formulário."))

    # 7. Mais de 2 testes ativos
    ativos = sum(1 for t in testes if t.get("status") == "ativa")
    if ativos > 2:
        achados["sucesso"].append(("conflito", f"{ativos} testes ativos; o máximo é 2."))

    resultado = {}
    for chave, lista in achados.items():
        veredito = max((v for v, _ in lista), key=GRAVIDADE.get, default="alinhado")
        resultado[chave] = {"veredito": veredito, "nota": " ".join(n for _, n in lista)}
    return resultado
