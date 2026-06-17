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
    DREInput,
    Encargos,
    FolhaInput,
    LinhaCusto,
    OutraReceita,
    ParametrosTributarios,
    ReceitasInput,
    SegmentoInput,
    calcular_dre,
    calcular_folha,
    calcular_receitas,
    calcular_tributos,
    inss_patronal_pct,
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


class RegimePayload(BaseModel):
    regime: str = "simples"               # simples | presumido | real
    anexo: str = "III"
    rbt12: float = 0.0
    iss_pct: float = 0.05
    inss_cpp: float = 0.20
    inss_rat: float = 0.03
    inss_terceiros: float = 0.058
    irpj_adicional_limite_mensal: float = 20_000.0


class FolhaPayload(BaseModel):
    escola: str
    ano_referencia: int
    niveis: List[str]
    colaboradores: List[ColaboradorPayload]
    encargos: EncargosPayload = EncargosPayload()
    # Se informado, o regime define automaticamente o INSS patronal da folha.
    regime: RegimePayload | None = None


@app.post("/api/folha")
def analisar_folha(payload: FolhaPayload) -> dict:
    encargos = Encargos(**payload.encargos.model_dump())
    if payload.regime is not None:
        params = ParametrosTributarios(**payload.regime.model_dump())
        encargos.inss_patronal = inss_patronal_pct(params)
    dados = FolhaInput(
        escola=payload.escola,
        ano_referencia=payload.ano_referencia,
        niveis=payload.niveis,
        colaboradores=[Colaborador(**c.model_dump()) for c in payload.colaboradores],
        encargos=encargos,
    )
    return calcular_folha(dados).as_dict()


class TributosPayload(BaseModel):
    receita_mensal: float = Field(ge=0)
    folha_bruta_mensal: float = Field(ge=0)
    lucro_mensal: float | None = None
    regime: RegimePayload = RegimePayload()


@app.post("/api/tributos")
def analisar_tributos(payload: TributosPayload) -> dict:
    params = ParametrosTributarios(**payload.regime.model_dump())
    return calcular_tributos(
        receita_mensal=payload.receita_mensal,
        folha_bruta_mensal=payload.folha_bruta_mensal,
        params=params,
        lucro_mensal=payload.lucro_mensal,
    ).as_dict()


class LinhaCustoPayload(BaseModel):
    nome: str
    valor: float = Field(ge=0)
    classe: str                               # "direto" | "indireto"
    grupo: str = ""
    variavel: bool = False
    por_nivel: dict[str, float] | None = None


class DREPayload(BaseModel):
    escola: str
    ano: int
    niveis: List[str]
    receita_liquida_total: float = Field(ge=0)
    receita_por_nivel: dict[str, float]
    alunos_por_nivel: dict[str, int]
    custos: List[LinhaCustoPayload]
    depreciacao: float = 0.0
    juros: float = 0.0
    irpj: float = 0.0
    csll: float = 0.0


@app.post("/api/dre")
def analisar_dre(payload: DREPayload) -> dict:
    dados = DREInput(
        escola=payload.escola,
        ano=payload.ano,
        niveis=payload.niveis,
        receita_liquida_total=payload.receita_liquida_total,
        receita_por_nivel=payload.receita_por_nivel,
        alunos_por_nivel=payload.alunos_por_nivel,
        custos=[LinhaCusto(**c.model_dump()) for c in payload.custos],
        depreciacao=payload.depreciacao,
        juros=payload.juros,
        irpj=payload.irpj,
        csll=payload.csll,
    )
    return calcular_dre(dados).as_dict()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(os.path.join(WEB_DIR, "index.html"))


# Arquivos estáticos (css/js/imagens), se houver
app.mount("/web", StaticFiles(directory=WEB_DIR), name="web")
