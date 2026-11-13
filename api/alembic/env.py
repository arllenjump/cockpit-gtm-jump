from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from app.config import database_url

# Logs do alembic.ini (mostra cada migração aplicada, inclusive no pré-deploy do Railway).
if context.config.config_file_name:
    fileConfig(context.config.config_file_name, disable_existing_loggers=False)

# As tabelas entram uma migração por etapa do plano (docs/02-modelo-de-dados.md).
target_metadata = None


def run_migrations_offline():
    context.configure(url=database_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    engine = create_engine(database_url())
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
