from sqlalchemy import create_engine

from app.config import database_url

engine = create_engine(database_url(), pool_pre_ping=True)
