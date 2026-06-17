"""
Módulo de Análise SWOT (matriz estratégica) do diagnóstico.

Reproduz a lógica da aba `Análise SWOT` da planilha Ágora de forma quantitativa
e interativa: cada fator recebe uma NOTA (0 a 10) e um PESO. A partir disso
calculamos a média ponderada de cada um dos quatro grupos e posicionamos a
"bolinha" num plano cartesiano:

        Ambiente Externo (Oportunidades +)
                       ▲
        Reorientação   │   Ofensiva
        (Fraquezas+Op) │   (Forças+Op)
    ───────────────────┼───────────────────►  Ambiente Interno (Forças +)
        Sobrevivência  │   Defensiva
        (Fraquezas+Am) │   (Forças+Am)
                       │

  * Eixo X (ambiente interno) = Forças − Fraquezas      (−10 a +10)
  * Eixo Y (ambiente externo) = Oportunidades − Ameaças (−10 a +10)

O quadrante onde a bolinha cai indica a postura estratégica recomendada.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

CATEGORIAS_SWOT = ("forca", "fraqueza", "oportunidade", "ameaca")

CATEGORIAS_SWOT_INFO = {
    "forca": {"label": "Forças", "eixo": "interno", "sinal": +1},
    "fraqueza": {"label": "Fraquezas", "eixo": "interno", "sinal": -1},
    "oportunidade": {"label": "Oportunidades", "eixo": "externo", "sinal": +1},
    "ameaca": {"label": "Ameaças", "eixo": "externo", "sinal": -1},
}


def _r(v: float, casas: int = 2) -> float:
    return round(v + 1e-9, casas)


@dataclass
class FatorSWOT:
    nome: str
    categoria: str            # forca | fraqueza | oportunidade | ameaca
    nota: float = 5.0         # 0 a 10 (intensidade/relevância do fator)
    peso: float = 1.0         # peso relativo dentro do grupo


@dataclass
class SWOTInput:
    escola: str
    ano: int
    fatores: List[FatorSWOT] = field(default_factory=list)


@dataclass
class SWOTResultado:
    escola: str
    ano: int
    scores: Dict[str, float]      # média ponderada por grupo (0..10)
    eixo_interno: float           # X = forças - fraquezas
    eixo_externo: float           # Y = oportunidades - ameaças
    intensidade: float            # distância da origem
    quadrante: str
    postura: str
    recomendacao: str

    def as_dict(self) -> dict:
        return {
            "escola": self.escola,
            "ano": self.ano,
            "scores": self.scores,
            "eixo_interno": self.eixo_interno,
            "eixo_externo": self.eixo_externo,
            "intensidade": self.intensidade,
            "quadrante": self.quadrante,
            "postura": self.postura,
            "recomendacao": self.recomendacao,
        }


def _classificar(x: float, y: float) -> tuple[str, str, str]:
    if x >= 0 and y >= 0:
        return (
            "ofensiva",
            "Ofensiva / Crescimento",
            "Ambiente favorável: use as forças da escola para aproveitar as "
            "oportunidades. Momento de investir e crescer.",
        )
    if x < 0 <= y:
        return (
            "reorientacao",
            "Reorientação / Crescimento",
            "Há boas oportunidades, mas fraquezas internas atrapalham. "
            "Priorize corrigir as fraquezas para capturar as oportunidades.",
        )
    if x >= 0 > y:
        return (
            "defensiva",
            "Defensiva / Manutenção",
            "A escola é forte, mas o ambiente externo traz ameaças. Use as "
            "forças para se proteger e manter a posição.",
        )
    return (
        "sobrevivencia",
        "Sobrevivência",
        "Cenário de atenção: fraquezas internas somadas a ameaças externas. "
        "Foque em reduzir riscos, cortar o que não é essencial e reforçar o caixa.",
    )


def calcular_swot(dados: SWOTInput) -> SWOTResultado:
    scores: Dict[str, float] = {}
    for cat in CATEGORIAS_SWOT:
        itens = [f for f in dados.fatores if f.categoria == cat]
        peso_total = sum(max(0.0, f.peso) for f in itens)
        if peso_total > 0:
            media = sum(f.nota * max(0.0, f.peso) for f in itens) / peso_total
        else:
            media = 0.0
        scores[cat] = _r(media)

    x = _r(scores["forca"] - scores["fraqueza"])
    y = _r(scores["oportunidade"] - scores["ameaca"])
    intensidade = _r((x * x + y * y) ** 0.5)
    quadrante, postura, recomendacao = _classificar(x, y)

    return SWOTResultado(
        escola=dados.escola,
        ano=dados.ano,
        scores=scores,
        eixo_interno=x,
        eixo_externo=y,
        intensidade=intensidade,
        quadrante=quadrante,
        postura=postura,
        recomendacao=recomendacao,
    )
