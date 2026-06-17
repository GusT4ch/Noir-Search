"""Motor de cálculo do Diagnóstico Econômico/Financeiro."""

from .receitas import (
    SegmentoInput,
    OutraReceita,
    ReceitasInput,
    calcular_receitas,
)
from .folha import (
    CATEGORIAS,
    CATEGORIAS_INFO,
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
from .dre import (
    DREInput,
    DREResultado,
    LinhaCusto,
    calcular_dre,
)
from .swot import (
    CATEGORIAS_SWOT_INFO,
    FatorSWOT,
    SWOTInput,
    SWOTResultado,
    calcular_swot,
)

__all__ = [
    "SegmentoInput",
    "OutraReceita",
    "ReceitasInput",
    "calcular_receitas",
    "CATEGORIAS",
    "CATEGORIAS_INFO",
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
    "DREInput",
    "DREResultado",
    "LinhaCusto",
    "calcular_dre",
    "CATEGORIAS_SWOT_INFO",
    "FatorSWOT",
    "SWOTInput",
    "SWOTResultado",
    "calcular_swot",
]
