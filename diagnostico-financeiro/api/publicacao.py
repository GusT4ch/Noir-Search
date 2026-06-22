"""
Rotas multi-escola: cadastro de escolas e usuários (pelo consultor) e
diagnósticos salvos (por escola/ano), com controle de acesso.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import Diagnostico, Escola, Usuario
from db.security import hash_senha

from .auth import pode_acessar_escola, somente_consultor, usuario_atual

router = APIRouter(prefix="/api", tags=["publicacao"])


# ------------------------------------------------------------------ Escolas
class EscolaPayload(BaseModel):
    nome: str
    cnpj: str | None = None


@router.post("/escolas")
def criar_escola(
    payload: EscolaPayload,
    _: Usuario = Depends(somente_consultor),
    db: Session = Depends(get_db),
) -> dict:
    e = Escola(nome=payload.nome.strip(), cnpj=payload.cnpj)
    db.add(e)
    db.commit()
    db.refresh(e)
    return {"id": e.id, "nome": e.nome, "cnpj": e.cnpj}


@router.get("/escolas")
def listar_escolas(
    u: Usuario = Depends(usuario_atual),
    db: Session = Depends(get_db),
) -> list[dict]:
    q = db.query(Escola)
    if u.papel != "consultor":
        q = q.filter(Escola.id == u.escola_id)
    return [{"id": e.id, "nome": e.nome, "cnpj": e.cnpj} for e in q.order_by(Escola.nome)]


# ----------------------------------------------------------------- Usuários
class UsuarioPayload(BaseModel):
    email: str
    nome: str
    senha: str = Field(min_length=6)
    papel: str = "escola"                 # consultor | escola
    escola_id: int | None = None


@router.post("/usuarios")
def criar_usuario(
    payload: UsuarioPayload,
    _: Usuario = Depends(somente_consultor),
    db: Session = Depends(get_db),
) -> dict:
    if payload.papel not in ("consultor", "escola"):
        raise HTTPException(status_code=400, detail="Papel inválido.")
    if payload.papel == "escola" and not payload.escola_id:
        raise HTTPException(status_code=400, detail="Usuário de escola exige escola_id.")
    if payload.escola_id and not db.get(Escola, payload.escola_id):
        raise HTTPException(status_code=404, detail="Escola não encontrada.")
    email = payload.email.lower().strip()
    if db.query(Usuario).filter(Usuario.email == email).first():
        raise HTTPException(status_code=409, detail="E-mail já cadastrado.")
    u = Usuario(
        email=email, nome=payload.nome.strip(),
        senha_hash=hash_senha(payload.senha),
        papel=payload.papel,
        escola_id=payload.escola_id if payload.papel == "escola" else None,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return {"id": u.id, "email": u.email, "papel": u.papel, "escola_id": u.escola_id}


# ------------------------------------------------------------ Diagnósticos
class DiagnosticoPayload(BaseModel):
    escola_id: int
    ano: int
    titulo: str = "Diagnóstico"
    dados: dict = {}


def _diag_dict(d: Diagnostico, incluir_dados: bool = False) -> dict:
    out = {
        "id": d.id, "escola_id": d.escola_id, "ano": d.ano, "titulo": d.titulo,
        "criado_em": d.criado_em.isoformat() if d.criado_em else None,
        "atualizado_em": d.atualizado_em.isoformat() if d.atualizado_em else None,
    }
    if incluir_dados:
        out["dados"] = json.loads(d.dados or "{}")
    return out


@router.post("/diagnosticos")
def salvar_diagnostico(
    payload: DiagnosticoPayload,
    u: Usuario = Depends(usuario_atual),
    db: Session = Depends(get_db),
) -> dict:
    if not pode_acessar_escola(u, payload.escola_id):
        raise HTTPException(status_code=403, detail="Sem acesso a esta escola.")
    if not db.get(Escola, payload.escola_id):
        raise HTTPException(status_code=404, detail="Escola não encontrada.")
    # upsert por (escola, ano, titulo)
    d = (
        db.query(Diagnostico)
        .filter(
            Diagnostico.escola_id == payload.escola_id,
            Diagnostico.ano == payload.ano,
            Diagnostico.titulo == payload.titulo,
        )
        .first()
    )
    if d:
        d.dados = json.dumps(payload.dados, ensure_ascii=False)
    else:
        d = Diagnostico(
            escola_id=payload.escola_id, ano=payload.ano, titulo=payload.titulo,
            dados=json.dumps(payload.dados, ensure_ascii=False),
        )
        db.add(d)
    db.commit()
    db.refresh(d)
    return _diag_dict(d)


@router.get("/diagnosticos")
def listar_diagnosticos(
    escola_id: int | None = None,
    u: Usuario = Depends(usuario_atual),
    db: Session = Depends(get_db),
) -> list[dict]:
    q = db.query(Diagnostico)
    if u.papel != "consultor":
        q = q.filter(Diagnostico.escola_id == u.escola_id)
    elif escola_id:
        q = q.filter(Diagnostico.escola_id == escola_id)
    return [_diag_dict(d) for d in q.order_by(Diagnostico.atualizado_em.desc())]


@router.get("/diagnosticos/{diag_id}")
def obter_diagnostico(
    diag_id: int,
    u: Usuario = Depends(usuario_atual),
    db: Session = Depends(get_db),
) -> dict:
    d = db.get(Diagnostico, diag_id)
    if not d:
        raise HTTPException(status_code=404, detail="Diagnóstico não encontrado.")
    if not pode_acessar_escola(u, d.escola_id):
        raise HTTPException(status_code=403, detail="Sem acesso a este diagnóstico.")
    return _diag_dict(d, incluir_dados=True)
