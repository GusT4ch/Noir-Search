"""
API do Diagnóstico Financeiro — módulo de Receitas.

Sobe um servidor FastAPI que:
  * serve o formulário/painel (pasta web/)
  * recebe as respostas da escola e devolve a análise calculada

Como rodar:
    pip install -r requirements.txt
    uvicorn api.main:app --reload
    abra http://127.0.0.1:8000
"""

from __future__ import annotations

import os
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from engine import (
    Colaborador,
    Encargos,
    FolhaInput,
    OutraReceita,
    ReceitasInput,
    SegmentoInput,
    calcular_folha,
    calcular_receitas,
)

WEB_DIR = os.path.join(os.path.dirname(__file__), "..", "web")

app = FastAPI(title="Diagnóstico Financeiro — Receitas", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------- #
# Schemas de entrada/saída (o que a "LP" envia)
# --------------------------------------------------------------------------- #
class SegmentoPayload(BaseModel):
    nome: str
    alunos: int = Field(ge=0)
    mensalidade_media: float = Field(ge=0)
    desconto_pct: float = Field(ge=0, le=1, default=0.0)
    inadimplencia_pct: float = Field(ge=0, le=1, default=0.0)


class OutraReceitaPayload(BaseModel):
    nome: str
    valor_mensal: float = Field(ge=0)


class ReceitasPayload(BaseModel):
    escola: str
    ano_referencia: int
    segmentos: List[SegmentoPayload]
    outras_receitas: List[OutraReceitaPayload] = []


# --------------------------------------------------------------------------- #
# Rotas
# --------------------------------------------------------------------------- #
@app.post("/api/receitas")
def analisar_receitas(payload: ReceitasPayload) -> dict:
    dados = ReceitasInput(
        escola=payload.escola,
        ano_referencia=payload.ano_referencia,
        segmentos=[SegmentoInput(**s.model_dump()) for s in payload.segmentos],
        outras_receitas=[
            OutraReceita(**o.model_dump()) for o in payload.outras_receitas
        ],
    )
    return calcular_receitas(dados).as_dict()


class ColaboradorPayload(BaseModel):
    nome: str
    categoria: str
    salario_base: float = Field(ge=0)
    alocacao: dict[str, float] = {}


class EncargosPayload(BaseModel):
    fgts: float = 0.08
    decimo_terceiro: float = 0.0833
    ferias_um_terco: float = 0.0278
    inss_patronal: float = 0.0
    outros: float = 0.0


class FolhaPayload(BaseModel):
    escola: str
    ano_referencia: int
    niveis: List[str]
    colaboradores: List[ColaboradorPayload]
    encargos: EncargosPayload = EncargosPayload()


@app.post("/api/folha")
def analisar_folha(payload: FolhaPayload) -> dict:
    dados = FolhaInput(
        escola=payload.escola,
        ano_referencia=payload.ano_referencia,
        niveis=payload.niveis,
        colaboradores=[Colaborador(**c.model_dump()) for c in payload.colaboradores],
        encargos=Encargos(**payload.encargos.model_dump()),
    )
    return calcular_folha(dados).as_dict()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(os.path.join(WEB_DIR, "index.html"))


# Arquivos estáticos (css/js/imagens), se houver
app.mount("/web", StaticFiles(directory=WEB_DIR), name="web")
