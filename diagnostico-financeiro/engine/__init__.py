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
from .tributos import (
    ParametrosTributarios,
    TributosResultado,
    aliquota_efetiva_simples,
    calcular_tributos,
    encargos_inss_para_regime,
    inss_patronal_pct,
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
    "ParametrosTributarios",
    "TributosResultado",
    "aliquota_efetiva_simples",
    "calcular_tributos",
    "encargos_inss_para_regime",
    "inss_patronal_pct",
]
