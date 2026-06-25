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
    CATEGORIAS_INFO,
    Colaborador,
    DREInput,
    Encargos,
    FatorSWOT,
    FolhaInput,
    LinhaCusto,
    SWOTInput,
    calcular_swot,
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

app = FastAPI(title="Diagnóstico Financeiro", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Publicação: banco de dados, login e multi-escola ---
from db.bootstrap import init_db  # noqa: E402
from .auth import router as auth_router  # noqa: E402
from .publicacao import router as publicacao_router  # noqa: E402


@app.on_event("startup")
def _startup() -> None:
    init_db()


app.include_router(auth_router)
app.include_router(publicacao_router)


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


@app.get("/api/folha/categorias")
def folha_categorias() -> dict:
    """Definições das categorias da folha — orientação para o preenchimento."""
    return CATEGORIAS_INFO


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


class FatorSWOTPayload(BaseModel):
    nome: str
    categoria: str            # forca | fraqueza | oportunidade | ameaca
    nota: float = Field(default=5.0, ge=0, le=10)
    peso: float = Field(default=1.0, ge=0)


class SWOTPayload(BaseModel):
    escola: str
    ano: int
    fatores: List[FatorSWOTPayload]


@app.post("/api/swot")
def analisar_swot(payload: SWOTPayload) -> dict:
    dados = SWOTInput(
        escola=payload.escola,
        ano=payload.ano,
        fatores=[FatorSWOT(**f.model_dump()) for f in payload.fatores],
    )
    return calcular_swot(dados).as_dict()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/relatorio/{formato}")
def baixar_relatorio(formato: str, regime: str = "simples"):
    """Gera o diagnóstico consolidado (exemplo) em docx, pptx ou pdf."""
    import tempfile

    from report.consolidado import montar_diagnostico_exemplo
    from report.gerar import gerar_docx, gerar_pdf, gerar_pptx

    formato = formato.lower()
    geradores = {
        "docx": (gerar_docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        "pptx": (gerar_pptx, "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
        "pdf": (gerar_pdf, "application/pdf"),
    }
    if formato not in geradores:
        return {"erro": "Formato inválido. Use docx, pptx ou pdf."}

    gerar, media_type = geradores[formato]
    diag = montar_diagnostico_exemplo(regime)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{formato}")
    tmp.close()
    gerar(diag, tmp.name)
    return FileResponse(tmp.name, media_type=media_type, filename=f"Diagnostico.{formato}")


@app.get("/api/diagnostico-exemplo")
def diagnostico_exemplo(regime: str = "simples") -> dict:
    """Diagnóstico consolidado (todos os módulos) a partir dos dados de exemplo."""
    from report.consolidado import montar_diagnostico_exemplo

    return montar_diagnostico_exemplo(regime)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(os.path.join(WEB_DIR, "Home.html"))


# Arquivos estáticos (css/js/imagens), se houver
app.mount("/web", StaticFiles(directory=WEB_DIR), name="web")
