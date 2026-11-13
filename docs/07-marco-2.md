# Marco 2: copys, artes e ativação (rascunho)

**Status: rascunho para discussão.** Montado a partir da apresentação da operação, do que ficou fora do marco 1 e das decisões de `00-contexto.md`. Nada aqui foi aprovado; as perguntas em aberto no fim decidem o formato final.

## Objetivo
Do contrato de GTM aprovado até o primeiro contato com as contas do ICP: copys e artes aprovadas (fase 3) e mensagens saindo pelos canais combinados (fase 4), sempre com aprovação humana em lote, checagem automática antes da fila e pausa.

## Entregáveis e critérios de aceite (proposta)

### 1. Agente de copys (fase 3)
- Lê o contrato aprovado (posicionamento, provas, comitê de compra e as apostas ativas) e gera as copys por canal e por caminho A e B de cada teste ativo:
  - e-mail: assunto e corpo;
  - LinkedIn: mensagem 1 a 1;
  - anúncio: título e texto.
- Passa pela checagem fixa (sem travessão, sem nome de cliente, sem número inventado) e por limites de tamanho por canal.
- As copys vão para a fila de aprovação; cada peça é aprovada, ajustada ou devolvida.
- Aceite: para o OPT-3, o agente gera as variações A e B das apostas ativas para os três canais; cada aprovação grava `approvals`; com todas as peças aprovadas, o gate 3 para 4 é registrado.

### 2. Artes (fase 3)
- Proposta: o cockpit gera o **briefing de cada arte** (peça, formato, mensagem, caminho do teste, identidade Jump) para a criação produzir no Claude Design ou no Figma; a arte pronta volta para o cockpit e entra na fila de aprovação.
- Aceite: cada copy de anúncio aprovada gera um briefing de arte; a arte anexada passa pela aprovação antes de ir para a ativação.

### 3. Fila de saída em lote (cockpit)
- Fila única do que está pronto para sair, por conta e por canal, com a prévia de cada mensagem; aprovar ou rejeitar em lote.
- Checagem automática **antes** de entrar na fila:
  - lista de exclusão (clientes e concorrentes, motivo `cliente_concorrente`);
  - nomes de clientes e travessões;
  - limite de 3 a 6 toques por empresa por semana, somando os canais.
- Pausa geral (um botão) e pausa automática por rejeição, spam ou denúncia.
- Aceite: mensagem para conta da lista de exclusão não entra na fila; o toque acima do limite semanal é barrado com o motivo; com a pausa geral ligada nada sai, e a pausa fica registrada com quem e quando.

### 4. UTMs e listas (fase 4)
- Padrão de UTM com o código do teste e o caminho (ex.: H1 caminho A), para o AdView ler os resultados por teste depois.
- Lista-alvo vem do ICP Jump, filtrada pela cláusula `icp` do contrato aprovado.
- Aceite: todo link que sai tem UTM no padrão; a lista da semana usada na ativação é a validada na página Contas.

### 5. LinkedIn assistido (fase 4)
- O cockpit prepara a mensagem aprovada e o link do perfil; o responsável do comercial envia manualmente e marca como enviado. Sem automação e fora do perfil do CEO.
- Aceite: a mensagem só aparece para o comercial depois de aprovada; marcar como enviado conta no limite de toques.

### 6. E-mail frio (fase 4)
- Caixas do Microsoft 365 num domínio secundário, com SPF, DKIM, DMARC, aquecimento e limite diário por caixa.
- Só sai o que foi aprovado na fila; o cockpit registra entrega, abertura, clique e resposta.
- Aceite: um envio de teste aprovado sai pela caixa do domínio secundário, respeita o limite diário e registra o retorno.

### 7. Gates e logs
- Gates 3 para 4 e 4 para 5 em `gate_events`; cada toque registrado por conta e canal.
- Toda ação de agente em `agent_log`, como no marco 1.

## Modelo de dados (a detalhar depois das respostas)
Tabelas prováveis: peças (copys e artes, com canal, teste e caminho), mensagens de saída, toques por conta e canal, lista de exclusão, caixas de envio e pausas. Dados pessoais (e-mail e perfil de pessoas) só entram depois da validação de LGPD.

## Fora do marco 2
WhatsApp oficial, SDR agêntico, nutrição no Mailchimp, score de engajamento, handoff e CRM, monitoramento previsto contra real com o AdView, relatório de gates e resumo semanal.

## Dependências
- **Produtos**: domínio secundário, DNS e uso do Microsoft 365 para envio. O aquecimento do domínio leva semanas, por isso o pedido deve sair já.
- **Privacidade**: base legal (LGPD) para enriquecer dados e enviar e-mail frio, com opt-out. Trava os itens 5 e 6.
- **Tecnologia e dados**: ICP Jump real, com as listas; de onde vêm os contatos das pessoas.
- **Comercial**: o responsável que envia no LinkedIn.
- **Microsoft 365**: se o envio for pela API do Microsoft Graph, o app do Entra ID precisa de permissão de envio.
- Do marco 1: `ANTHROPIC_API_KEY` no Railway e o fluxo real das etapas 8 e 11 verificado.

## Ordem proposta
1. Lista de exclusão, limite de toques e pausas (não dependem de ninguém).
2. Agente de copys e fila de aprovação das peças.
3. Fila de saída em lote com a checagem automática.
4. UTMs e lista-alvo.
5. Briefing de artes.
6. LinkedIn assistido (depende da LGPD e do responsável do comercial).
7. E-mail frio (depende do domínio aquecido e da LGPD).

## Perguntas em aberto
1. **Artes**: o cockpit só gera o briefing para a criação, ou deve gerar imagens?
2. **Contatos**: de onde vêm os e-mails e perfis das pessoas (ICP Jump, LinkdAPI)? Depende da LGPD.
3. **Envio de e-mail**: API do Microsoft Graph ou SMTP das caixas do domínio secundário?
4. **Anúncios**: o marketing sobe manualmente, como diz a apresentação, e o cockpit só entrega copy, arte e UTM?
5. **Limite de toques**: a apresentação fala de 3 a 6 por semana. Qual valor começa?
6. **Pausa automática**: a partir de quanto de rejeição, spam ou denúncia?
7. **Aprovação em lote**: quem aprova além do marketing (criação para artes, comercial para LinkedIn)?
