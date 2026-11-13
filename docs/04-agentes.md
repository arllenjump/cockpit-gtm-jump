# Agentes e auditoria

## Regras comuns a todos os agentes
- Português do Brasil.
- Nunca usar travessão (—).
- Nunca citar nome de cliente da Jump. Provas permitidas: mais de 60 clientes, mais de 600 profissionais, ISO 27001, 27701, 42001, 9001 e 14001, prêmio Negócios em Expansão 2025 da Exame, AWS Partner Network. Só ao falar do OPT-3: ROI documentado de até 61% em otimização de custo (cerca de 36% já formalizado, medido com baseline caso a caso) e primeiros insights em 10 dias de onboarding.
- Não inventar números, nomes de clientes ou ferramentas. Quando faltar dado, dizer que falta.
- Saída sempre em JSON no formato pedido, sem texto fora dele.

## Agente de estudo (fase 1)
Entrada: briefing, dados do martech-monitor (perfil, brief de 60 dias, concorrentes, sinais, oportunidades, temas ativos) e a contagem de contas aderentes do ICP Jump.

Saída:
```json
{
  "mercado": "resumo do mercado para este produto",
  "concorrentes": [{ "nome": "", "movimento": "", "implicacao": "" }],
  "oportunidades": [{ "titulo": "", "porque": "", "impacto": "baixo|medio|alto" }],
  "riscos": [""],
  "perguntas_em_aberto": [""],
  "fontes": { "lidas": [""], "ausentes": [""] }
}
```

## Agente de contrato (fase 2)
Entrada: briefing, estudo aprovado, resumo das contas do ICP Jump (setores, portes, sinais mais frequentes).

Saída:
```json
{
  "clausulas": [
    { "key": "icp", "estrategia": "", "execucao": "" }
  ],
  "testes": [
    {
      "codigo": "H1",
      "hipotese": "",
      "caminho_a": "",
      "caminho_b": "",
      "sinal_rapido": "",
      "sinal_lento": "",
      "faixa_prevista": "a calibrar com o histórico",
      "regra": "",
      "status": "ativa|na_fila"
    }
  ]
}
```
As 10 chaves estão em `00-contexto.md`. No máximo 2 testes com status `ativa`.

### Apostas iniciais do OPT-3
Definidas na apresentação da operação. O agente parte delas: mantém os códigos e os status e só muda uma aposta se o estudo aprovado justificar, dizendo o motivo na própria hipótese.

| Código | Hipótese | Caminho A | Caminho B | Sinal rápido | Sinal lento | Status |
| --- | --- | --- | --- | --- | --- | --- |
| H1 | Para o CFO, a dor de custo engaja mais que governança | Custo da fatura de nuvem | Governança e controle | CTR e engajamento por conta | Contas que viram SQL | ativa |
| H2 | O primeiro contato rende mais pelo CFO do que pelo CTO | Sequência pelo CFO | Sequência pelo CTO ou Diretor de TI | Taxa de resposta | SQLs aceitos | ativa |
| H3 | Oferta de entrada sem reunião converte mais que pedir conversa | Material ou diagnóstico sem reunião | "Falar com especialista" | Conversão do anúncio | Contas que vão à reunião | na_fila |

A faixa prevista sai do histórico da Jump (campanha Farma, Sponsored Messaging e o cluster do Opt3 no Google Ads); até ser calibrada, fica "a calibrar com o histórico".

## Auditoria
Duas camadas.

### Camada 1: regras fixas, em código e com testes
1. Cláusula com estratégia ou execução vazia: `ajustar`.
2. Texto com travessão: `ajustar`.
3. Texto com nome da lista de clientes bloqueados: `conflito`.
4. Cláusula `sucesso` sem métrica por conta: `conflito`.
5. Cláusula `categoria` vazia em produto de nova categoria (RadarAI, Adoption AI): `conflito`.
6. Conteúdo de avaliação (business case, comparativo, compliance) marcado como atrás de formulário: `ajustar`.
7. Mais de 2 testes ativos: `conflito`.

Como as regras são aplicadas (`api/app/auditoria.py`, aprovado em 13/11/2026):
- Regra 1 também vale para cláusula ausente.
- Regra 2 pega travessão (—) e meia-risca (–); hífen comum não.
- Regra 3 usa a lista da variável `BLOCKED_CLIENT_NAMES` (nomes separados por ponto e vírgula), ignorando maiúsculas e acentos e só com a palavra inteira. A nota não repete o nome.
- Regra 4: a execução da cláusula `sucesso` precisa citar alguma métrica "por conta".
- Regra 5: produtos de nova categoria são `radarai` e `adoption-ai` (slug em `products`).
- Regra 6: a mesma cláusula fala de business case, comparativo ou compliance e de formulário, cadastro, "gated" ou "atrás de".
- Regra 7: o conflito fica na cláusula `sucesso`.
- Se mais de uma regra disparar, vale a mais grave (conflito, ajustar, alinhado) e as notas se somam.

### Camada 2: auditoria por IA, opcional
Lê o contrato inteiro e aponta incoerências entre cláusulas (por exemplo, público diferente do ICP, ou KPI que não mede a hipótese). Devolve veredito e nota por cláusula. Nunca sobrescreve um `conflito` da camada 1.
