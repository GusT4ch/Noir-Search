"""
Modelos de dados (multi-escola).

  * Escola      — cada escola atendida.
  * Usuario     — consultor (acesso a todas) ou usuário de escola (acesso só
                  à sua escola). Senha guardada com hash (nunca em texto).
  * Diagnostico — um diagnóstico salvo, vinculado a uma escola e a um ano.
                  Os dados ficam em JSON (entradas dos módulos + resultados).
  * Sessao      — token de acesso (login), revogável e com validade.

Princípio LGPD: nenhum dado pessoal de aluno é armazenado — apenas números
agregados dentro do JSON do diagnóstico.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def agora() -> datetime:
    return datetime.now(timezone.utc)


class Escola(Base):
    __tablename__ = "escolas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    cnpj: Mapped[str | None] = mapped_column(String(20), nullable=True)
    criada_em: Mapped[datetime] = mapped_column(DateTime, default=agora)

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="escola")
    diagnosticos: Mapped[list["Diagnostico"]] = relationship(back_populates="escola")


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    papel: Mapped[str] = mapped_column(String(20), nullable=False)  # consultor | escola
    escola_id: Mapped[int | None] = mapped_column(ForeignKey("escolas.id"), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=agora)

    escola: Mapped[Escola | None] = relationship(back_populates="usuarios")
    sessoes: Mapped[list["Sessao"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )


class Diagnostico(Base):
    __tablename__ = "diagnosticos"
    __table_args__ = (UniqueConstraint("escola_id", "ano", "titulo", name="uq_diag"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    escola_id: Mapped[int] = mapped_column(ForeignKey("escolas.id"), nullable=False, index=True)
    ano: Mapped[int] = mapped_column(Integer, nullable=False)
    titulo: Mapped[str] = mapped_column(String(200), default="Diagnóstico")
    dados: Mapped[str] = mapped_column(Text, default="{}")  # JSON
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=agora)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=agora, onupdate=agora)

    escola: Mapped[Escola] = relationship(back_populates="diagnosticos")


class Sessao(Base):
    __tablename__ = "sessoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expira_em: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    criada_em: Mapped[datetime] = mapped_column(DateTime, default=agora)

    usuario: Mapped[Usuario] = relationship(back_populates="sessoes")
