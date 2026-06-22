"""
Inicialização do banco: cria as tabelas e garante um usuário consultor
(administrador) inicial. As credenciais vêm de variáveis de ambiente
(ADMIN_EMAIL / ADMIN_SENHA); na ausência, usa um padrão APENAS para
desenvolvimento e exibe um aviso.
"""

from __future__ import annotations

import os

from .database import Base, SessionLocal, engine
from .models import Usuario
from .security import hash_senha


def criar_tabelas() -> None:
    Base.metadata.create_all(bind=engine)


def garantir_admin() -> None:
    email = os.environ.get("ADMIN_EMAIL", "consultor@exemplo.com")
    senha = os.environ.get("ADMIN_SENHA")
    if not senha:
        senha = "trocar-esta-senha"
        print(
            "[AVISO] ADMIN_SENHA não definida. Criando consultor padrão "
            f"({email} / '{senha}'). Defina ADMIN_EMAIL e ADMIN_SENHA em "
            "produção e troque a senha no primeiro acesso."
        )
    db = SessionLocal()
    try:
        existe = db.query(Usuario).filter(Usuario.email == email).first()
        if existe:
            return
        db.add(Usuario(
            email=email,
            nome="Consultor",
            senha_hash=hash_senha(senha),
            papel="consultor",
            escola_id=None,
            ativo=True,
        ))
        db.commit()
    finally:
        db.close()


def init_db() -> None:
    criar_tabelas()
    garantir_admin()
