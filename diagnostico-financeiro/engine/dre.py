"""
Módulo de Custos + DRE (Demonstrativo de Resultado) do diagnóstico.

Reproduz a cascata da aba `DRE` da planilha Ágora e o rateio por nível de
ensino da aba `RAT`:

    RECEITA LÍQUIDA
    (-) Custos Diretos            (docentes, material didático, impostos s/
                                   faturamento, evasão, inadimplência,
                                   reequipamento)
    (=) MARGEM DE CONTRIBUIÇÃO
    (-) Custos Indiretos          (coordenação, administrativo, pró-labore,
                                   serviços, aluguéis, despesas etc.)
    (=) EBITDA
    (-) Depreciação / Amortização
    (-) Juros
    (=) EBIT
    (-) IRPJ / CSLL               (zero no Simples — já está no DAS)
    (=) LUCRO OPERACIONAL

Além da cascata, calcula:
  * indicadores (margens, carga de custos);
  * ponto de equilíbrio (break-even) com base nos custos fixos e variáveis;
  * rateio dos custos por nível de ensino (direcionador: participação de cada
    nível na receita líquida) e o custo por aluno (mensal e anual).

Itens marcados como `variavel=True` (impostos sobre faturamento e provisões de
evasão/inadimplência/reequipamento) variam com a receita e por isso entram no
cálculo do ponto de equilíbrio como custo variável.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


def _r(v: float) -> float:
    return round(v + 1e-9, 2)


@dataclass
class LinhaCusto:
    nome: str
    valor: float                              # valor mensal
    classe: str                               # "direto" | "indireto"
    grupo: str = ""                           # rótulo do grupo (p/ agrupar no relatório)
    variavel: bool = False                    # varia com a receita (entra no break-even)
    por_nivel: Optional[Dict[str, float]] = None  # alocação pronta por nível; senão rateia por receita


@dataclass
class DREInput:
    escola: str
    ano: int
    niveis: List[str]
    receita_liquida_total: float              # mensalidades líquidas + outras receitas
    receita_por_nivel: Dict[str, float]       # direcionador de rateio (receita líquida por nível)
    alunos_por_nivel: Dict[str, int]
    custos: List[LinhaCusto] = field(default_factory=list)
    depreciacao: float = 0.0
    juros: float = 0.0
    irpj: float = 0.0
    csll: float = 0.0


@dataclass
class DREResultado:
    escola: str
    ano: int
    niveis: List[str]

    receita_liquida: float
    custos_diretos: float
    margem_contribuicao: float
    custos_indiretos: float
    ebitda: float
    depreciacao: float
    juros: float
    ebit: float
    irpj: float
    csll: float
    lucro_operacional: float

    # indicadores
    margem_contribuicao_pct: float
    margem_ebitda_pct: float
    margem_liquida_pct: float
    ponto_equilibrio_receita: float

    # agrupamentos e rateio
    grupos: Dict[str, float]
    por_nivel: Dict[str, dict]                # receita, custo, resultado, custo/aluno

    def as_dict(self) -> dict:
        return {
            "escola": self.escola,
            "ano": self.ano,
            "niveis": self.niveis,
            "dre": {
                "receita_liquida": self.receita_liquida,
                "custos_diretos": self.custos_diretos,
                "margem_contribuicao": self.margem_contribuicao,
                "custos_indiretos": self.custos_indiretos,
                "ebitda": self.ebitda,
                "depreciacao": self.depreciacao,
                "juros": self.juros,
                "ebit": self.ebit,
                "irpj": self.irpj,
                "csll": self.csll,
                "lucro_operacional": self.lucro_operacional,
            },
            "indicadores": {
                "margem_contribuicao_pct": self.margem_contribuicao_pct,
                "margem_ebitda_pct": self.margem_ebitda_pct,
                "margem_liquida_pct": self.margem_liquida_pct,
                "ponto_equilibrio_receita": self.ponto_equilibrio_receita,
            },
            "grupos": self.grupos,
            "por_nivel": self.por_nivel,
        }


def _pct(parte: float, todo: float) -> float:
    return round(parte / todo, 4) if todo else 0.0


def calcular_dre(dados: DREInput) -> DREResultado:
    receita = dados.receita_liquida_total

    diretos = sum(c.valor for c in dados.custos if c.classe == "direto")
    indiretos = sum(c.valor for c in dados.custos if c.classe == "indireto")
    variaveis = sum(c.valor for c in dados.custos if c.variavel)

    diretos = _r(diretos)
    indiretos = _r(indiretos)

    margem_contribuicao = _r(receita - diretos)
    ebitda = _r(margem_contribuicao - indiretos)
    ebit = _r(ebitda - dados.depreciacao - dados.juros)
    lucro = _r(ebit - dados.irpj - dados.csll)

    # --- Ponto de equilíbrio (break-even) ---
    # Custos fixos = todos os custos não proporcionais à receita + depr + juros.
    custos_totais = diretos + indiretos
    fixos = _r(custos_totais - variaveis + dados.depreciacao + dados.juros)
    razao_mc = (receita - variaveis) / receita if receita else 0.0
    ponto_equilibrio = _r(fixos / razao_mc) if razao_mc > 0 else 0.0

    # --- Agrupamentos para o relatório ---
    grupos: Dict[str, float] = {}
    for c in dados.custos:
        chave = c.grupo or c.nome
        grupos[chave] = _r(grupos.get(chave, 0.0) + c.valor)

    # --- Rateio por nível de ensino ---
    total_driver = sum(dados.receita_por_nivel.values()) or 1.0
    share = {n: dados.receita_por_nivel.get(n, 0.0) / total_driver for n in dados.niveis}

    custo_por_nivel = {n: 0.0 for n in dados.niveis}
    for c in dados.custos:
        if c.por_nivel:
            for n in dados.niveis:
                custo_por_nivel[n] += c.por_nivel.get(n, 0.0)
        else:
            for n in dados.niveis:
                custo_por_nivel[n] += c.valor * share[n]
    # depreciação, juros e impostos sobre o lucro rateados por receita
    extra = dados.depreciacao + dados.juros + dados.irpj + dados.csll
    for n in dados.niveis:
        custo_por_nivel[n] += extra * share[n]

    por_nivel: Dict[str, dict] = {}
    for n in dados.niveis:
        receita_n = dados.receita_por_nivel.get(n, 0.0)
        custo_n = _r(custo_por_nivel[n])
        alunos_n = dados.alunos_por_nivel.get(n, 0)
        cpa_mes = _r(custo_n / alunos_n) if alunos_n else 0.0
        por_nivel[n] = {
            "receita_liquida": _r(receita_n),
            "custo_total": custo_n,
            "resultado": _r(receita_n - custo_n),
            "alunos": alunos_n,
            "custo_por_aluno_mes": cpa_mes,
            "custo_por_aluno_ano": _r(cpa_mes * 12),
            "participacao_receita": _pct(receita_n, total_driver),
        }

    return DREResultado(
        escola=dados.escola,
        ano=dados.ano,
        niveis=dados.niveis,
        receita_liquida=_r(receita),
        custos_diretos=diretos,
        margem_contribuicao=margem_contribuicao,
        custos_indiretos=indiretos,
        ebitda=ebitda,
        depreciacao=_r(dados.depreciacao),
        juros=_r(dados.juros),
        ebit=ebit,
        irpj=_r(dados.irpj),
        csll=_r(dados.csll),
        lucro_operacional=lucro,
        margem_contribuicao_pct=_pct(margem_contribuicao, receita),
        margem_ebitda_pct=_pct(ebitda, receita),
        margem_liquida_pct=_pct(lucro, receita),
        ponto_equilibrio_receita=ponto_equilibrio,
        grupos=grupos,
        por_nivel=por_nivel,
    )
