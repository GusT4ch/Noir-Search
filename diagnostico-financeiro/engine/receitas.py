"""
Módulo de Receitas do diagnóstico financeiro.

Reproduz a lógica das abas RECEITAS / DRE da planilha "Ágora":

    Receita bruta mensal  = soma(alunos x mensalidade média) por segmento
    (-) Descontos         = receita bruta x % de desconto médio
    (=) Receita líq. mens.= receita bruta - descontos
    (+) Outras receitas   = integral, esportes, livros, cantina, etc.
    (=) Receita líquida    = receita líquida de mensalidades + outras receitas

A inadimplência NÃO é deduzida da receita líquida aqui: ela é tratada como
provisão (custo) no DRE, então é apresentada apenas como valor informativo,
seguindo a mesma lógica da planilha original.

Todos os valores monetários são mensais, salvo indicação contrária.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


def _r(valor: float) -> float:
    """Arredonda para 2 casas (centavos)."""
    return round(valor + 1e-9, 2)


@dataclass
class SegmentoInput:
    """Um nível de ensino informado pela escola."""

    nome: str
    alunos: int
    mensalidade_media: float
    desconto_pct: float = 0.0       # ex.: 0.11 para 11%
    inadimplencia_pct: float = 0.0  # ex.: 0.08 para 8%


@dataclass
class OutraReceita:
    """Receita que não vem de mensalidade (integral, esportes, livros...)."""

    nome: str
    valor_mensal: float


@dataclass
class ReceitasInput:
    """Conjunto de dados de receita de uma escola."""

    escola: str
    ano_referencia: int
    segmentos: List[SegmentoInput] = field(default_factory=list)
    outras_receitas: List[OutraReceita] = field(default_factory=list)


@dataclass
class SegmentoResultado:
    nome: str
    alunos: int
    mensalidade_media: float
    receita_bruta: float
    valor_desconto: float
    receita_liquida_mensalidade: float
    provisao_inadimplencia: float
    participacao_pct: float  # participação na receita bruta total

    def as_dict(self) -> dict:
        return {
            "nome": self.nome,
            "alunos": self.alunos,
            "mensalidade_media": self.mensalidade_media,
            "receita_bruta": self.receita_bruta,
            "valor_desconto": self.valor_desconto,
            "receita_liquida_mensalidade": self.receita_liquida_mensalidade,
            "provisao_inadimplencia": self.provisao_inadimplencia,
            "participacao_pct": self.participacao_pct,
        }


@dataclass
class ReceitasResultado:
    escola: str
    ano_referencia: int
    segmentos: List[SegmentoResultado]

    total_alunos: int
    ticket_medio: float

    receita_bruta_mensal: float
    descontos_mensal: float
    receita_liquida_mensalidade_mensal: float
    outras_receitas_mensal: float
    receita_liquida_mensal: float
    provisao_inadimplencia_mensal: float

    # Projeções anuais (x12)
    receita_liquida_anual: float

    def as_dict(self) -> dict:
        return {
            "escola": self.escola,
            "ano_referencia": self.ano_referencia,
            "segmentos": [s.as_dict() for s in self.segmentos],
            "totais": {
                "total_alunos": self.total_alunos,
                "ticket_medio": self.ticket_medio,
                "receita_bruta_mensal": self.receita_bruta_mensal,
                "descontos_mensal": self.descontos_mensal,
                "receita_liquida_mensalidade_mensal": self.receita_liquida_mensalidade_mensal,
                "outras_receitas_mensal": self.outras_receitas_mensal,
                "receita_liquida_mensal": self.receita_liquida_mensal,
                "provisao_inadimplencia_mensal": self.provisao_inadimplencia_mensal,
                "receita_liquida_anual": self.receita_liquida_anual,
            },
        }


def calcular_receitas(dados: ReceitasInput) -> ReceitasResultado:
    """Aplica a lógica das abas RECEITAS/DRE sobre os dados informados."""

    receita_bruta_total = sum(
        s.alunos * s.mensalidade_media for s in dados.segmentos
    )

    resultados: List[SegmentoResultado] = []
    descontos_total = 0.0
    inadimplencia_total = 0.0

    for s in dados.segmentos:
        bruta = _r(s.alunos * s.mensalidade_media)
        desconto = _r(bruta * s.desconto_pct)
        liquida_mens = _r(bruta - desconto)
        inadimplencia = _r(liquida_mens * s.inadimplencia_pct)
        participacao = _r(
            (bruta / receita_bruta_total * 100) if receita_bruta_total else 0.0
        )

        descontos_total += desconto
        inadimplencia_total += inadimplencia

        resultados.append(
            SegmentoResultado(
                nome=s.nome,
                alunos=s.alunos,
                mensalidade_media=_r(s.mensalidade_media),
                receita_bruta=bruta,
                valor_desconto=desconto,
                receita_liquida_mensalidade=liquida_mens,
                provisao_inadimplencia=inadimplencia,
                participacao_pct=participacao,
            )
        )

    receita_bruta_total = _r(receita_bruta_total)
    descontos_total = _r(descontos_total)
    receita_liquida_mens = _r(receita_bruta_total - descontos_total)
    outras_total = _r(sum(o.valor_mensal for o in dados.outras_receitas))
    receita_liquida = _r(receita_liquida_mens + outras_total)
    inadimplencia_total = _r(inadimplencia_total)

    total_alunos = sum(s.alunos for s in dados.segmentos)
    ticket_medio = _r(receita_bruta_total / total_alunos) if total_alunos else 0.0

    return ReceitasResultado(
        escola=dados.escola,
        ano_referencia=dados.ano_referencia,
        segmentos=resultados,
        total_alunos=total_alunos,
        ticket_medio=ticket_medio,
        receita_bruta_mensal=receita_bruta_total,
        descontos_mensal=descontos_total,
        receita_liquida_mensalidade_mensal=receita_liquida_mens,
        outras_receitas_mensal=outras_total,
        receita_liquida_mensal=receita_liquida,
        provisao_inadimplencia_mensal=inadimplencia_total,
        receita_liquida_anual=_r(receita_liquida * 12),
    )
