# Marco 1: ICP Jump, briefing e criação do GTM

## Objetivo
Do briefing de um produto até um contrato de GTM aprovado, usando o ICP Jump para as contas, com toda decisão passando por aprovação humana e registrada.

## Entregáveis e critérios de aceite

### 0. Esqueleto da aplicação
- Repositório com `web/` e `api/`, rodando local com um comando documentado no README da raiz.
- Projeto próprio no Railway com Postgres e dois serviços, publicado a partir da `main`.
- Login com conta Microsoft, aceitando só e-mails do domínio da Jump.
- Layout base com a barra lateral e a identidade de `05-telas.md`.
- Aceite: a URL do Railway abre a tela de login; um e-mail da Jump entra e um de fora é recusado; `GET /api/health` responde ok.

### 1. Página Contas (ICP Jump)
- Lista de contas ordenada pelo GTM Score, com porte, tier e sinal de agora.
- Clique numa conta abre o dossiê: por que agora, por que a Jump, abordagem sugerida, decisores mapeados e oferta recomendada.
- Botão "Validar lista da semana" cria um registro em `account_list_validations` e um item aprovado em `approvals`.
- Aceite: com `ICP_JUMP_MODE=fixture`, a página mostra as 6 contas do fixture ordenadas por score, e a validação grava os dois registros.

### 2. Página Lançamentos (briefing e estudo, fase 1)
- Formulário de briefing: produto, objetivo, contexto e provas, prazo.
- "Enviar ao agente de estudo" gera o estudo (ver `04-agentes.md`) e mostra o progresso por fonte.
- O estudo vai para a fila de aprovação. Aprovado, registra o gate 1 para 2.
- Aceite: um briefing do Opt3 produz um estudo com JSON válido, fontes listadas, registro em `agent_log`, e a aprovação grava `gate_events` com `from_phase=1, to_phase=2, advanced=true`.

### 3. Página Contrato de GTM (fase 2)
- O agente gera as 10 cláusulas e o plano de testes (no máximo 2 apostas ativas e 1 na fila).
- A auditoria fixa roda e marca cada cláusula como alinhado, ajustar ou conflito, com nota.
- O marketing pode editar uma cláusula; a auditoria roda de novo só nela.
- "Aprovar contrato" cria a versão aprovada; a versão anterior passa a "substituido".
- Aceite: os testes das regras de auditoria passam; aprovar a v2 deixa a v1 como "substituido"; o gate 2 para 3 é registrado.

### 4. Página Aprovações (mínima)
- Fila única com tudo que está pendente: lista de contas, estudo e contrato.
- Ações: aprovar, ajustar (com nota) e devolver ao agente (com instrução).
- Aceite: cada ação muda o status do item e grava quem decidiu e quando.

### 5. Logs
- `agent_log` com cada chamada de agente (modelo, tokens e custo estimado).
- `gate_events` com cada passagem de fase.

## Fora do marco 1
Envio de e-mail, LinkedIn assistido, WhatsApp, Mailchimp, score de engajamento, handoff e CRM, motor de testes rodando com dados reais, insights e alertas, resumo semanal.

## Dependências
- ICP Jump: confirmar onde roda e como autenticar. Enquanto isso, modo fixture.
- Martech-monitor: confirmar a forma de autenticação do servidor MCP.
- `ANTHROPIC_API_KEY` criada e colocada nas variáveis do Railway pelo marketing.
- Registro de aplicativo na Microsoft (Entra ID) para o login, feito por quem administra o Microsoft 365 da Jump.
