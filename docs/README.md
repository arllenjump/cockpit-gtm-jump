# Cockpit GTM Jump: documentação

Aplicação própria da Operação GTM Jump, separada do AdView. O AdView continua como dashboard de mídia paga; a integração entre os dois fica para quando a operação chegar às fases de ativação e monitoramento.

## Ordem de leitura
1. `00-contexto.md`: a operação inteira, as 10 fases e as decisões já tomadas.
2. `01-marco-1.md`: o que entra agora (esqueleto, ICP Jump, briefing e estudo, contrato de GTM) e os critérios de aceite.
3. `02-modelo-de-dados.md`: tabelas do Postgres.
4. `03-integracoes.md`: ICP Jump, martech-monitor, Claude API e, no futuro, AdView.
5. `04-agentes.md`: agente de estudo, agente de contrato e auditoria.
6. `05-telas.md`: identidade visual e telas. Ainda não existe; a identidade aplicada vem do Figma "Identidade Jump" (cores grafite e laranja, Kanit nos títulos, logo).
7. `06-plano.md`: etapas de construção, cada uma com sua verificação.

## Referências visuais
- Demonstração animada do cockpit (conceito com dados fictícios): https://claude.ai/artifact/2o1yJMoccGTNyTKf1pDY7b
- Apresentação da operação: https://claude.ai/artifact/1nTQPq9DUm2t5ZAbrNSFxh

## Status
- Marco 1: código das etapas 0 a 13 publicado em https://cockpit.jump.tec.br. Falta a verificação real das etapas 8 (agente de estudo) e 11 (agente de contrato), que depende da `ANTHROPIC_API_KEY` no Railway.
- Simulação piloto: as contas do ICP Jump são fictícias, em `api/fixtures/icp-jump-contas.json` (`ICP_JUMP_MODE=fixture`), e o martech-monitor usa uma fotografia real de 13/11/2026 (`MARTECH_MODE=fixture`).
- Dependências abertas: onde o ICP Jump roda e como autenticar (o monitor-store está fora do ar desde outubro); chave do martech-monitor para o cockpit.
