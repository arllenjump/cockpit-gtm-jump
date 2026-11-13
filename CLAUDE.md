# Cockpit GTM Jump

Aplicação própria da Operação GTM Jump: agentes de IA executam cada etapa do go-to-market de um produto da Jump, e o marketing aprova tudo o que sai. É separada do AdView (que continua sendo o dashboard de mídia paga) e pode se integrar a ele depois.

## Antes de qualquer tarefa
- Leia `docs/README.md` e os arquivos na ordem indicada lá.
- O plano está em `docs/06-plano.md`. Siga uma etapa por vez e só avance depois da verificação da etapa.

## Como trabalhar
- Pense antes de programar: declare as suposições e, se algo tiver mais de uma interpretação ou estiver confuso, pare e pergunte.
- Escreva o mínimo de código que resolve a etapa. Nada de funcionalidade não pedida nem abstração "para o futuro".
- Mudanças cirúrgicas: mexa só no que a etapa exige e siga o estilo que já existe no projeto.
- Cada etapa termina com uma verificação concreta (teste, consulta ao banco ou tela funcionando). Só declare concluído depois de verificar.

## Regras de produto
- Nada que fala com o mercado sai sem aprovação humana registrada na tabela `approvals`.
- Todo texto gerado por agente passa pela checagem fixa: sem travessão, sem nome de cliente, sem número inventado.
- Toda ação de agente é registrada em `agent_log`; toda passagem de fase é registrada em `gate_events`.
- Interface e textos em português do Brasil.

## Stack
- `web/`: React, Vite, TypeScript e Tailwind.
- `api/`: Python com FastAPI, migrações com Alembic, testes com pytest.
- Banco: Postgres. Deploy: Railway, num projeto próprio com Postgres e dois serviços (web e api).
- Login: conta Microsoft (Entra ID), aceitando só e-mails do domínio da Jump.
- Não adicione bibliotecas além das necessárias para a etapa em curso.

## Ambiente e segredos
- Trabalhe em branches e abra PR; a `main` faz deploy no Railway.
- Segredos só por variável de ambiente, nunca no código nem em commits. Variáveis: `DATABASE_URL`, `ANTHROPIC_API_KEY`, `CLAUDE_MODEL`, `ICP_JUMP_MODE`, `ICP_JUMP_API_URL`, `ICP_JUMP_API_TOKEN`, `MARTECH_MODE`, `MARTECH_MCP_URL`, `MARTECH_MCP_KEY`, `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET`, `MICROSOFT_TENANT_ID`, `ALLOWED_EMAIL_DOMAIN`, `SESSION_SECRET`, `APP_URL`, `BLOCKED_CLIENT_NAMES`.
- Mantenha um `.env.example` com os nomes das variáveis e nenhum valor real.
