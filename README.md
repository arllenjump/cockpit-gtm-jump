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

Com [uv](https://docs.astral.sh/uv/), um Postgres rodando e `DATABASE_URL` definido:

```bash
cd api && uv sync --extra dev
uv run alembic upgrade head && uv run uvicorn app.main:app --reload
```

```bash
cd web && npm install && npm run dev
```

### Testes

```bash
cd api && uv run pytest
```

## Deploy (Railway)

Projeto `cockpit-gtm-jump`, publicado a partir da `main`, com build pelo Railpack (sem Dockerfile), como os outros projetos da Jump.

| Serviço | Pasta raiz | Build e início | Variáveis principais |
| --- | --- | --- | --- |
| Postgres | (banco do Railway) | | |
| api | `api/` | Railpack (uv); pré-deploy `alembic upgrade head`; início `uvicorn` | as do `.env.example`, com `DATABASE_URL=${{Postgres.DATABASE_URL}}` e `APP_URL=https://cockpit.jump.tec.br` |
| web | `web/` | Railpack (Vite), servido pelo Caddy com o `web/Caddyfile` | `API_INTERNAL_URL=http://api.railway.internal:8000` |

Só o `web` é público (`cockpit.jump.tec.br`); ele repassa `/api/*` para a `api` pela rede interna. A URL de retorno do login é `https://cockpit.jump.tec.br/api/auth/callback`.
