"""Tabelas do marco 1 (docs/02-modelo-de-dados.md) e cadastro do OPT-3

Revision ID: 0001
Revises:
Create Date: 2026-11-13
"""
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

# Mesma estrutura de docs/02-modelo-de-dados.md (os comentários das colunas estão lá).
TABELAS = """
create table products (
  id serial primary key,
  slug text unique not null,
  name text not null,
  created_at timestamptz default now()
);

create table launches (
  id serial primary key,
  product_id int references products(id),
  phase int not null default 1,
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
  content jsonb not null,
  sources jsonb not null,
  status text not null default 'rascunho',
  created_at timestamptz default now()
);

create table gtm_contracts (
  id serial primary key,
  product_id int references products(id),
  launch_id int references launches(id),
  version int not null,
  status text not null default 'rascunho',
  created_at timestamptz default now(),
  unique (product_id, version)
);

create table contract_clauses (
  id serial primary key,
  contract_id int references gtm_contracts(id),
  clause_key text not null,
  strategy text,
  execution text,
  owner_area text,
  audit_verdict text,
  audit_note text,
  reviewed_at timestamptz,
  unique (contract_id, clause_key)
);

create table test_hypotheses (
  id serial primary key,
  contract_id int references gtm_contracts(id),
  code text not null,
  hypothesis text not null,
  path_a text not null,
  path_b text not null,
  fast_signal text not null,
  slow_signal text not null,
  expected_range jsonb,
  decision_rule text not null,
  status text not null default 'na_fila',
  decision text,
  learning text
);

create table account_snapshots (
  id serial primary key,
  external_id text not null,
  name text not null,
  sector text,
  employees int,
  gtm_score int,
  tier text,
  signals jsonb,
  dossier jsonb,
  week text not null,
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
  item_type text not null,
  item_id int not null,
  phase int not null,
  summary text not null,
  status text not null default 'pendente',
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
  reason_code text,
  entered_at timestamptz,
  exited_at timestamptz default now()
);

create table agent_log (
  id serial primary key,
  agent text not null,
  action text not null,
  input_ref jsonb,
  output_ref jsonb,
  model text,
  tokens_in int,
  tokens_out int,
  cost_estimate numeric(10,4),
  created_at timestamptz default now()
);
"""

# Ordem inversa por causa das chaves estrangeiras.
ORDEM_DROP = [
    "agent_log",
    "gate_events",
    "approvals",
    "account_list_validations",
    "account_snapshots",
    "test_hypotheses",
    "contract_clauses",
    "gtm_contracts",
    "studies",
    "briefings",
    "launches",
    "products",
]


def upgrade():
    op.execute(TABELAS)
    op.execute("insert into products (slug, name) values ('opt3', 'OPT-3')")


def downgrade():
    for tabela in ORDEM_DROP:
        op.execute(f"drop table {tabela}")
