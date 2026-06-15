"""Motor de cálculo do Diagnóstico Econômico/Financeiro."""

from .receitas import (
    SegmentoInput,
    OutraReceita,
    ReceitasInput,
    calcular_receitas,
)

__all__ = [
    "SegmentoInput",
    "OutraReceita",
    "ReceitasInput",
    "calcular_receitas",
]
