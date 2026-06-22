"""
Configuração do banco de dados.

Por padrão usa SQLite (arquivo local), mas basta definir a variável de
ambiente DATABASE_URL para apontar para um PostgreSQL na hospedagem
(ex.: postgresql+psycopg://usuario:senha@host:5432/diagnostico). O resto do
código não muda — é a vantagem de usar SQLAlchemy.
"""

from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "sqlite:///" + os.path.join(os.path.dirname(__file__), "..", "diagnostico.db")
)

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dependência do FastAPI: abre uma sessão por requisição."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
