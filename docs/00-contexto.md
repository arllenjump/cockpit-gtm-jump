# Contexto da operação

## Em uma frase
Agentes de IA executam cada etapa do go-to-market de um produto da Jump, e o marketing aprova tudo o que sai. O piloto é o Opt3; o RadarAI entra depois do ciclo de 42 dias do Opt3.

## As 10 fases
| Fase | Ciclo | O agente faz | O humano faz |
| --- | --- | --- | --- |
| 1. Planejamento e estudo | Por produto | Pesquisa mercado, concorrentes e sinais | Passa o briefing e aprova o estudo |
| 2. Criação do GTM | Por produto | Gera o contrato de GTM e o plano de testes | Revisa, ajusta e aprova |
| 3. Copys e artes | Por produto | Copys, variações e artes | Revisa marca e peças |
| 4. Ativação | Por produto | Automações, e-mails, UTMs e listas | Sobe os ads e aprova mensagens |
| 5. Monitoramento | Por produto | Compara previsto e real, gera alertas | Acompanha e direciona |
| 6. Nutrição e qualificação | Por lead e conta | Cruza cargo, ação e mensagem | Ajusta regras e aprova envios |
| 7. Score | Por lead e conta | Soma o score do lead ao GTM Score | Valida |
| 8. Handoff e SQL | Por lead e conta | Ficha, briefing e pré-atendimento | Comercial aceita ou recusa |
| 9. Comercial | Por lead e conta | Roteiro e resumo | Comercial conduz e registra o motivo |
| 10. Retorno e correção | Por lead e conta | Lê os gates e propõe correções | Decide o que corrigir |

Entre cada fase há um gate que registra se avançou, o tempo na fase e, se travou, o motivo (lista fixa).

## Princípios
1. Nada fala com o mercado sem aprovação humana, em todos os tiers.
2. Toda campanha e todo lead desqualificado geram aprendizado registrado.
3. Cada aposta tem faixa prevista e regra de decisão combinada antes.
4. Aproveitar o que já existe antes de construir.
5. Construção interna: o marketing monta o esqueleto, outra equipe lapida.

## Decisões já tomadas
- O cockpit é uma aplicação própria, separada do AdView, com identidade visual própria. O AdView continua como dashboard de mídia paga e pode ser integrado depois.
- O contrato de GTM é a fonte única de cada produto e é versionado.
- O ICP Jump é o motor de contas (GTM Score, sinais, dossiê) e pertence à área de Tecnologia e dados.
- Envio de e-mail frio, LinkedIn assistido e WhatsApp oficial ficam para o marco 2.
- A CAIXA Pré-Pagos não faz parte desta operação.

## Os 10 itens do contrato de GTM (chaves usadas no código)
| clause_key | Estratégia | Execução |
| --- | --- | --- |
| icp | ICP | Filtros de conta e lista-alvo |
| comite | Comitê de compra por função | Kit de consenso por função |
| categoria | Justificativa da categoria | Conteúdo aberto de categoria e business case |
| gatilhos | Gatilhos positivos e reativos | Sinais de intenção classificados por tipo |
| posicionamento | Posicionamento e pontos de entrada | Mensagem por canal e frequência por conta |
| provas | Provas por voz (marca, especialista, par) | Distribuição por voz e dados estruturados |
| estagio | Estágio da conta | Scoring de conta e roteamento |
| validacao | Argumento de validação | Roteiro da primeira reunião e battlecard |
| pausa | Motivos de pausa | Fluxo de reciclagem |
| sucesso | Hipótese de sucesso e plano de testes | Métricas por conta e faixa prevista |
