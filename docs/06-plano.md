# Plano do marco 1

Uma etapa por vez. Cada etapa tem uma verificação; só avance quando ela passar.

| Etapa | O que fazer | Verificação |
| --- | --- | --- |
| 0. Esqueleto local | Criar `web/` (React, Vite, TypeScript, Tailwind) e `api/` (FastAPI) com `GET /api/health`, `.env.example` e README com o comando para rodar local | Rodando local, a tela abre e `/api/health` responde ok |
| 1. Identidade e layout | Tokens de cor e fontes de `05-telas.md`, modo claro e escuro, barra lateral | A tela base aparece nos dois modos com a barra lateral |
| 2. Deploy | Projeto próprio no Railway com Postgres e os serviços `web` e `api`, publicando da `main` | A URL pública abre a tela base e `/api/health` responde ok |
| 3. Login | Conta Microsoft restrita ao domínio da Jump | Um e-mail da Jump entra; um e-mail de fora é recusado |
| 4. Banco | Migrações Alembic das tabelas de `02-modelo-de-dados.md` e cadastro do produto Opt3 | `alembic upgrade head` e `downgrade` funcionam; `select * from products` mostra o Opt3 |
| 5. Adapter do ICP Jump | Adapter em modo `fixture` | Teste: `list_accounts(min_score=60)` devolve 5 contas em ordem decrescente de score |
| 6. Página Contas | Lista, dossiê e validação semanal | A validação grava `account_list_validations` e um item aprovado em `approvals` |
| 7. Martech-monitor | Conectar ao servidor MCP e chamar as 6 ferramentas | Script de verificação imprime o perfil da Jump e a contagem de concorrentes |
| 8. Agente de estudo | Briefing, chamada à Claude API, validação do JSON, gravação | Um briefing do Opt3 gera um estudo válido, com fontes lidas e ausentes, e uma linha em `agent_log` |
| 9. Aprovação do estudo | Fila de aprovação e gate 1 para 2 | Aprovar grava `approvals` decidido e `gate_events` de 1 para 2 |
| 10. Auditoria fixa | As 7 regras em código | Testes das 7 regras passam no pytest |
| 11. Agente de contrato | Geração das 10 cláusulas e dos testes, com auditoria aplicada | Contrato v1 gravado com 10 cláusulas e no máximo 2 testes ativos |
| 12. Página Contrato de GTM | Tabela, edição por cláusula, aprovação e versão | Editar e aprovar cria a v2 e deixa a v1 como substituido; gate 2 para 3 gravado |
| 13. Página Aprovações | Fila única com as três ações | Cada ação muda o status e grava quem decidiu e quando |

As etapas 0 e 1 não dependem de ninguém. A etapa 2 precisa de acesso ao Railway, a 3 do registro de aplicativo na Microsoft e a 8 da `ANTHROPIC_API_KEY`.

Quando a API do ICP Jump for confirmada: trocar `ICP_JUMP_MODE` para `api` e repetir a verificação da etapa 5 com dados reais.
