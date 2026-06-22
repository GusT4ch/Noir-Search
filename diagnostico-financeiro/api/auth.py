"""
Autenticação e autorização (multi-escola).

  * Login devolve um token de sessão (Bearer).
  * `usuario_atual` valida o token a cada requisição.
  * `somente_consultor` restringe rotas administrativas.
  * `pode_acessar_escola` aplica a regra: consultor vê tudo; usuário de
    escola só enxerga a própria escola.
"""

from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import Sessao, Usuario, agora
from db.security import gerar_token, hash_token, verificar_senha

router = APIRouter(prefix="/api/auth", tags=["auth"])

VALIDADE_HORAS = 12


class LoginPayload(BaseModel):
    email: str
    senha: str


def _usuario_dict(u: Usuario) -> dict:
    return {
        "id": u.id, "email": u.email, "nome": u.nome,
        "papel": u.papel, "escola_id": u.escola_id,
    }


@router.post("/login")
def login(payload: LoginPayload, db: Session = Depends(get_db)) -> dict:
    u = db.query(Usuario).filter(Usuario.email == payload.email.lower().strip()).first()
    if not u or not u.ativo or not verificar_senha(payload.senha, u.senha_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos.")
    token = gerar_token()
    db.add(Sessao(
        usuario_id=u.id,
        token_hash=hash_token(token),
        expira_em=agora() + timedelta(hours=VALIDADE_HORAS),
    ))
    db.commit()
    return {"token": token, "usuario": _usuario_dict(u)}


def usuario_atual(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Usuario:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Não autenticado.")
    token = authorization.split(" ", 1)[1].strip()
    sessao = db.query(Sessao).filter(Sessao.token_hash == hash_token(token)).first()
    if not sessao:
        raise HTTPException(status_code=401, detail="Sessão inválida.")
    expira = sessao.expira_em
    if expira.tzinfo is None:
        from datetime import timezone
        expira = expira.replace(tzinfo=timezone.utc)
    if expira < agora():
        db.delete(sessao)
        db.commit()
        raise HTTPException(status_code=401, detail="Sessão expirada.")
    u = db.get(Usuario, sessao.usuario_id)
    if not u or not u.ativo:
        raise HTTPException(status_code=401, detail="Usuário inativo.")
    return u


def somente_consultor(u: Usuario = Depends(usuario_atual)) -> Usuario:
    if u.papel != "consultor":
        raise HTTPException(status_code=403, detail="Acesso restrito ao consultor.")
    return u


def pode_acessar_escola(u: Usuario, escola_id: int) -> bool:
    return u.papel == "consultor" or u.escola_id == escola_id


@router.post("/logout")
def logout(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        sessao = db.query(Sessao).filter(Sessao.token_hash == hash_token(token)).first()
        if sessao:
            db.delete(sessao)
            db.commit()
    return {"ok": True}


@router.get("/me")
def me(u: Usuario = Depends(usuario_atual)) -> dict:
    return _usuario_dict(u)
