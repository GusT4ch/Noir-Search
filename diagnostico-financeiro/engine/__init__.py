"""Motor de cálculo do Diagnóstico Econômico/Financeiro."""

from .receitas import (
    SegmentoInput,
    OutraReceita,
    ReceitasInput,
    calcular_receitas,
)
from .folha import (
    Colaborador,
    Encargos,
    FolhaInput,
    calcular_folha,
)

__all__ = [
    "SegmentoInput",
    "OutraReceita",
    "ReceitasInput",
    "calcular_receitas",
    "Colaborador",
    "Encargos",
    "FolhaInput",
    "calcular_folha",
]
