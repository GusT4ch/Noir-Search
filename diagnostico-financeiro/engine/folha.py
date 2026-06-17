"""
Módulo de Folha de Pagamento do diagnóstico financeiro.

Reproduz a lógica das abas `folha` / `TAB FOLHA` / `ENC` da planilha Ágora:

  * Cada colaborador tem um salário-base e uma alocação (%) por nível de
    ensino (docentes e coordenação). Administrativos não são alocados por
    nível — entram como "geral" e são rateados depois (módulo de Custos).
  * Sobre o salário bruto incidem encargos (FGTS, 13º, férias + 1/3 e,
    conforme o regime tributário, INSS patronal). As alíquotas são
    configuráveis para refletir o regime de cada escola.

Saídas:
  * folha bruta, encargos e custo total (mensal e anual)
  * abertura por categoria (docente / coordenação / administrativo)
  * distribuição do custo de pessoal por nível de ensino (alimenta o rateio
    do DRE e o custo por aluno)

Princípio LGPD: trabalhamos com cargos e valores agregados, sem dados
pessoais identificáveis dos colaboradores.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

CATEGORIAS = ("docente", "coordenacao", "administrativo")

# Definições das categorias da folha — fonte única usada pela interface para
# orientar a escola no preenchimento. O critério é a FUNÇÃO da pessoa:
#
#   * docente        -> professores e auxiliares (Infantil, Fundamental, Médio)
#   * coordenacao    -> coordenadores e supervisores de ENSINO
#   * administrativo -> TODO o restante (quem não é professor/auxiliar nem
#                       coordenador/supervisor de ensino)
CATEGORIAS_INFO = {
    "docente": {
        "label": "Professores e Auxiliares",
        "descricao": (
            "Professores e auxiliares de sala do Ensino Infantil, Fundamental "
            "e Médio. Informe o salário e a alocação por nível de ensino "
            "(quando o profissional atua em mais de um nível, distribua em %)."
        ),
        "exemplos": ["professores", "auxiliares de sala / de classe"],
        "aloca_por_nivel": True,
    },
    "coordenacao": {
        "label": "Coordenação e Supervisão de Ensino",
        "descricao": (
            "Coordenadores pedagógicos e supervisores de ensino. Também podem "
            "ser alocados por nível de ensino."
        ),
        "exemplos": ["coordenador pedagógico", "supervisor de ensino"],
        "aloca_por_nivel": True,
    },
    "administrativo": {
        "label": "Administrativo (demais funcionários)",
        "descricao": (
            "Todas as pessoas que NÃO são professores/auxiliares nem "
            "coordenadores/supervisores de ensino. Não é alocado por nível — "
            "é rateado entre os níveis no cálculo dos custos."
        ),
        "exemplos": [
            "diretores",
            "secretaria",
            "limpeza",
            "segurança / portaria",
            "zeladoria",
            "almoxarifado",
            "recepção",
        ],
        "aloca_por_nivel": False,
    },
}


def _r(v: float) -> float:
    return round(v + 1e-9, 2)


@dataclass
class Encargos:
    """Alíquotas de encargos sobre o salário bruto (frações, ex.: 0.08)."""

    fgts: float = 0.08
    decimo_terceiro: float = 0.0833        # 1/12
    ferias_um_terco: float = 0.0278        # (1/12) * (1/3)
    inss_patronal: float = 0.0             # 0 no Simples; ~0.268 fora dele
    outros: float = 0.0                    # RAT, terceiros, etc.

    @property
    def total_pct(self) -> float:
        return _r(
            self.fgts
            + self.decimo_terceiro
            + self.ferias_um_terco
            + self.inss_patronal
            + self.outros
        )


@dataclass
class Colaborador:
    nome: str
    categoria: str                          # docente | coordenacao | administrativo
    salario_base: float
    # alocação por nível (frações que somam 1.0). Vazio => "geral" (rateável).
    alocacao: Dict[str, float] = field(default_factory=dict)


@dataclass
class FolhaInput:
    escola: str
    ano_referencia: int
    niveis: List[str]
    colaboradores: List[Colaborador] = field(default_factory=list)
    encargos: Encargos = field(default_factory=Encargos)


@dataclass
class FolhaResultado:
    escola: str
    ano_referencia: int
    niveis: List[str]
    encargos_total_pct: float

    salario_bruto_mensal: float
    encargos_mensal: float
    custo_total_mensal: float
    custo_total_anual: float

    por_categoria: Dict[str, dict]
    por_nivel: Dict[str, float]            # salário bruto alocado por nível
    geral_nao_alocado: float               # administrativos/sem alocação

    def as_dict(self) -> dict:
        return {
            "escola": self.escola,
            "ano_referencia": self.ano_referencia,
            "niveis": self.niveis,
            "encargos_total_pct": self.encargos_total_pct,
            "por_categoria": self.por_categoria,
            "por_nivel": self.por_nivel,
            "geral_nao_alocado": self.geral_nao_alocado,
            "totais": {
                "salario_bruto_mensal": self.salario_bruto_mensal,
                "encargos_mensal": self.encargos_mensal,
                "custo_total_mensal": self.custo_total_mensal,
                "custo_total_anual": self.custo_total_anual,
            },
        }


def calcular_folha(dados: FolhaInput) -> FolhaResultado:
    enc_pct = dados.encargos.total_pct

    por_categoria = {
        c: {"salario_bruto": 0.0, "encargos": 0.0, "custo_total": 0.0}
        for c in CATEGORIAS
    }
    por_nivel = {n: 0.0 for n in dados.niveis}
    geral = 0.0
    bruto_total = 0.0

    for col in dados.colaboradores:
        sal = col.salario_base
        if not sal:
            continue
        bruto_total += sal
        cat = col.categoria if col.categoria in por_categoria else "administrativo"
        por_categoria[cat]["salario_bruto"] += sal

        if col.alocacao:
            for nivel, frac in col.alocacao.items():
                if nivel in por_nivel:
                    por_nivel[nivel] += sal * frac
                else:
                    geral += sal * frac
        else:
            geral += sal

    # arredondamentos e encargos
    for cat, d in por_categoria.items():
        d["salario_bruto"] = _r(d["salario_bruto"])
        d["encargos"] = _r(d["salario_bruto"] * enc_pct)
        d["custo_total"] = _r(d["salario_bruto"] + d["encargos"])

    por_nivel = {n: _r(v) for n, v in por_nivel.items()}
    bruto_total = _r(bruto_total)
    encargos_total = _r(bruto_total * enc_pct)
    custo_total = _r(bruto_total + encargos_total)

    return FolhaResultado(
        escola=dados.escola,
        ano_referencia=dados.ano_referencia,
        niveis=dados.niveis,
        encargos_total_pct=enc_pct,
        salario_bruto_mensal=bruto_total,
        encargos_mensal=encargos_total,
        custo_total_mensal=custo_total,
        custo_total_anual=_r(custo_total * 12),
        por_categoria=por_categoria,
        por_nivel=por_nivel,
        geral_nao_alocado=_r(geral),
    )
