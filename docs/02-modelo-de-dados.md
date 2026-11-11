# Modelo de dados (Postgres)

Banco próprio do cockpit, separado do banco do AdView. Crie as tabelas com migrações Alembic, uma migração por etapa do plano.

```sql
create table products (
  id serial primary key,
  slug text unique not null,           -- 'opt3', 'radarai'
  name text not null,
  created_at timestamptz default now()
);

create table launches (
  id serial primary key,
  product_id int references products(id),
  phase int not null default 1,        -- fase atual, 1 a 10
  status text not null default 'ativo',
  started_at timestamptz default now(),
  created_by text not null
);

create table briefings (
  id serial primary key,
  launch_id int references launches(id),
  objetivo text not null,
  contexto text,
  provas text,
  prazo_dias int default 42,
  created_by text not null,
  created_at timestamptz default now()
);

create table studies (
  id serial primary key,
  launch_id int references launches(id),
  content jsonb not null,              -- formato em 04-agentes.md
  sources jsonb not null,              -- fontes lidas e fontes ausentes
  status text not null default 'rascunho',  -- rascunho | aprovado | devolvido
  created_at timestamptz default now()
);

create table gtm_contracts (
  id serial primary key,
  product_id int references products(id),
  launch_id int references launches(id),
  version int not null,
  status text not null default 'rascunho',  -- rascunho | em_revisao | aprovado | substituido
  created_at timestamptz default now(),
  unique (product_id, version)
);

create table contract_clauses (
  id serial primary key,
  contract_id int references gtm_contracts(id),
  clause_key text not null,            -- chaves em 00-contexto.md
  strategy text,
  execution text,
  owner_area text,                     -- Marketing | Comercial | Tecnologia e dados
  audit_verdict text,                  -- alinhado | ajustar | conflito
  audit_note text,
  reviewed_at timestamptz,
  unique (contract_id, clause_key)
);

create table test_hypotheses (
  id serial primary key,
  contract_id int references gtm_contracts(id),
  code text not null,                  -- H1, H2, H3
  hypothesis text not null,
  path_a text not null,
  path_b text not null,
  fast_signal text not null,
  slow_signal text not null,
  expected_range jsonb,                -- calibrada com histórico da Jump
  decision_rule text not null,
  status text not null default 'na_fila',  -- ativa | na_fila | decidida
  decision text,
  learning text
);

create table account_snapshots (
  id serial primary key,
  external_id text not null,           -- id da conta no ICP Jump
  name text not null,
  sector text,
  employees int,
  gtm_score int,
  tier text,
  signals jsonb,
  dossier jsonb,                       -- why_now, why_us, suggested_approach, risks, recommended_offer
  week text not null,                  -- '2026-W46'
  snapshot_at timestamptz default now()
);

create table account_list_validations (
  id serial primary key,
  product_id int references products(id),
  week text not null,
  account_ids jsonb not null,
  validated_by text not null,
  validated_at timestamptz default now()
);

create table approvals (
  id serial primary key,
  item_type text not null,             -- lista_contas | estudo | contrato
  item_id int not null,
  phase int not null,
  summary text not null,
  status text not null default 'pendente',  -- pendente | aprovado | ajustado | devolvido
  note text,
  decided_by text,
  decided_at timestamptz,
  created_at timestamptz default now()
);

create table gate_events (
  id serial primary key,
  product_id int references products(id),
  launch_id int references launches(id),
  from_phase int not null,
  to_phase int not null,
  advanced boolean not null,
  reason_code text,                    -- lista fixa abaixo; obrigatório quando advanced = false
  entered_at timestamptz,
  exited_at timestamptz default now()
);

create table agent_log (
  id serial primary key,
  agent text not null,                 -- estudo | contrato | auditoria
  action text not null,
  input_ref jsonb,
  output_ref jsonb,
  model text,
  tokens_in int,
  tokens_out int,
  cost_estimate numeric(10,4),
  created_at timestamptz default now()
);
```

## Motivos fixos (reason_code)
| reason_code | Motivo | Onde se corrige |
| --- | --- | --- |
| fora_icp | Fora do ICP (porte ou setor) | Fase 4 |
| cargo_sem_decisao | Cargo sem poder de decisão | Fases 4 e 6 |
| mensagem_dor | Mensagem não bate com a dor | Fases 2 e 3 |
| sem_timing | Sem timing ou orçamento agora | Fase 6 |
| dado_falso | Dado falso ou só curiosidade | Fase 6 |
| cliente_concorrente | Já cliente ou concorrente | Fase 4 |

## Dados pessoais
No marco 1 não guardamos e-mail, telefone ou perfil de pessoas. O snapshot guarda dados de empresa e os cargos dos decisores mapeados. Dados pessoais entram só depois da validação de LGPD.
