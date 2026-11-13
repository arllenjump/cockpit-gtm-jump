# Integrações

## ICP Jump (motor de contas)
- Dono: área de Tecnologia e dados.
- Status em 10/11/2026: os deploys do projeto GTM-Jump no Railway aparecem removidos ou falhos desde 18/05/2026. Confirmar onde a API roda antes de ligar o modo `api`.
- Campos conhecidos pelo dossiê do ICP Jump: GTM Score (account_score 50%, persona_score 30%, signal_score 20%, mais bônus de vagas), tiers (Tier 1 a partir de 80, Tier 2 de 60 a 79, Tier 3 de 40 a 59), nove sinais (capital_investment, expansion, cloud_migration, digital_transformation, leadership_hire, data_initiative, security_compliance, crm_sales_initiative, cost_optimization), decisores com `is_decision_maker`, dossiê com why_now, why_us, suggested_approach, risks e recommended_offer, filtros min_gtm_score, vertical e has_active_signals.
- Endpoints, autenticação e limites: a confirmar. Não invente rotas.

### Adapter
Crie um único adapter com dois modos, escolhido por `ICP_JUMP_MODE`:
- `fixture`: lê `api/fixtures/icp-jump-contas.json` (fica dentro de `api/` porque o serviço no Railway só publica essa pasta). Hoje são contas fictícias da simulação piloto.
- `api`: chama a API real em `ICP_JUMP_API_URL` com `ICP_JUMP_API_TOKEN`.

Funções mínimas:
- `listAccounts({ minScore, vertical, hasActiveSignals })` devolve contas ordenadas por GTM Score.
- `getAccount(externalId)` devolve a conta com dossiê e decisores.

A cada validação semanal, grave um snapshot em `account_snapshots`, para o histórico não depender da API.

### Tradução dos sinais para a tela
| Sinal | Texto na tela | Tipo |
| --- | --- | --- |
| capital_investment | Investimento recente | positivo |
| expansion | Expansão | positivo |
| data_initiative | Iniciativa de dados | positivo |
| security_compliance | Exigência regulatória | positivo |
| cloud_migration | Migração para nuvem | neutro |
| digital_transformation | Transformação digital | neutro |
| crm_sales_initiative | Iniciativa comercial | neutro |
| leadership_hire | Nova liderança | reativo |
| cost_optimization | Corte de custos | reativo |

## Martech-monitor (servidor MCP)
- URL: `https://martech-monitor-production.up.railway.app/mcp` (variável `MARTECH_MCP_URL`).
- Ferramentas usadas no marco 1: `jump_get_profile`, `jump_get_brief` (days: 60), `jump_list_competitors`, `jump_list_signals`, `jump_list_opportunities`, `martech_list_themes` (status: active).
- Forma escolhida: cliente MCP no backend (SDK `mcp` 1.x para Python, transporte HTTP), em `api/app/martech.py`. O backend chama as 6 ferramentas e passa os resultados ao agente.
- Autenticação: a chave vai na query da URL (`?key=...`), em `MARTECH_MCP_KEY`. A chave do cockpit deve ser pedida ao dono do servidor; nunca no código.
- Modo escolhido por `MARTECH_MODE`:
  - `fixture`: lê `api/fixtures/martech-monitor.json`, uma fotografia das respostas reais de 13/11/2026. Usado até o cockpit ter chave própria.
  - `mcp`: chama o servidor real.
- Verificação: `uv run python -m scripts.verificar_martech` (dentro de `api/`) ou `GET /api/martech/verificacao` logado no cockpit.

## Jump Bases (histórico de propostas)
Existe um projeto no Railway, mas o formato não está documentado. Fica fora do marco 1: o agente de estudo registra a fonte como ausente.

## Claude API
- SDK oficial `anthropic` para Python, usado no `api/`. Chave em `ANTHROPIC_API_KEY`.
- Modelo em `CLAUDE_MODEL` (sugestão: `claude-sonnet-5-5`). Confirme os modelos disponíveis em https://docs.claude.com.
- Peça saída em JSON e valide contra o formato de `04-agentes.md` antes de gravar. Se não validar, uma nova tentativa e, depois, erro visível na tela.
- Registre tokens e custo estimado em `agent_log`. Defina um teto mensal e mostre alerta no cockpit ao chegar a 80%.

## AdView (integração futura, fora do marco 1)
- O AdView (adview.jump.tec.br) é o dashboard de mídia paga e tem banco próprio no Railway.
- Quando a operação chegar às fases 4 e 5, o cockpit passa a ler dele os resultados de campanha por teste, usando o ID de teste nas UTMs.
- A forma de integrar (API do AdView ou leitura do banco) é decidida nessa hora. No marco 1, nada depende do AdView.

## Login com conta Microsoft
- Registro de aplicativo no Entra ID da Jump, com a URL de retorno do serviço `web` no Railway.
- O `api/` valida o token e aceita só e-mails terminados em `ALLOWED_EMAIL_DOMAIN`.
- O e-mail de quem aprova é o que vai para `decided_by`, `validated_by` e `created_by`.
