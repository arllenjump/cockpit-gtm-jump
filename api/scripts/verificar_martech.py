"""Verificação da etapa 7: chama as 6 ferramentas e imprime o perfil e a contagem de concorrentes.

Uso (de dentro de api/):  uv run python -m scripts.verificar_martech
"""
from app import martech

r = martech.resumo(martech.coletar())
print(f"Modo: {r['modo']}")
print(f"Perfil: {r['perfil']}")
print(f"Concorrentes: {r['concorrentes']}")
print(f"Sinais: {r['sinais']} (no brief de 60 dias: {r['sinais_no_brief_60_dias']})")
print(f"Oportunidades: {r['oportunidades']}")
print(f"Temas ativos: {r['temas_ativos']}")
