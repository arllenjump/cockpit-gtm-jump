# Cockpit GTM Jump

Aplicação da Operação GTM Jump. Leia `CLAUDE.md` e `docs/` antes de mexer.

- `api/`: FastAPI, Alembic e pytest.
- `web/`: React, Vite, TypeScript e Tailwind.

## Rodar local

Pré-requisito: Docker.

```bash
cp .env.example .env
docker compose up --build
```

- Web: http://localhost:5173
- API: http://localhost:8000/api/health

Para o login funcionar localmente, preencha `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET` e `MICROSOFT_TENANT_ID` no `.env` e cadastre `http://localhost:5173/api/auth/callback` como URL de retorno no app do Entra ID.

### Sem Docker

Com um Postgres rodando e `DATABASE_URL` definido:

```bash
cd api && python -m venv .venv && .venv/bin/pip install -e '.[dev]'
.venv/bin/alembic upgrade head && .venv/bin/uvicorn app.main:app --reload
```

```bash
cd web && npm install && npm run dev
```

### Testes

```bash
cd api && .venv/bin/pytest
```

## Deploy (Railway)

Projeto próprio com três serviços, publicados a partir da `main`:

| Serviço | Pasta raiz | Variáveis principais |
| --- | --- | --- |
| Postgres | (banco do Railway) | |
| api | `api/` | as do `.env.example`, com `DATABASE_URL=${{Postgres.DATABASE_URL}}` e `APP_URL` = domínio público do web |
| web | `web/` | `API_INTERNAL_URL=http://api.railway.internal:8000` |

Só o `web` tem domínio público; ele repassa `/api/*` para a `api` pela rede interna.
