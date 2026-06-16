"""
Módulo Tributário — calcula a carga de impostos conforme o **regime
tributário** escolhido pela escola.

O regime impacta o diagnóstico em DOIS lugares:

  1. Impostos sobre a receita / sobre o resultado (deduções no DRE):
       - Simples Nacional: um único DAS (alíquota efetiva sobre a receita),
         que já embute IRPJ, CSLL, PIS, COFINS, CPP (INSS patronal) e ISS.
       - Lucro Presumido / Real: IRPJ, CSLL, PIS, COFINS e ISS calculados
         separadamente.
  2. INSS patronal (CPP) sobre a FOLHA:
       - Simples (Anexo III): CPP está dentro do DAS  => 0% sobre a folha.
       - Presumido / Real: ~28,8% sobre a folha (20% CPP + RAT + terceiros).

Percentuais legais vigentes (2025/2026). As alíquotas municipais (ISS) e o
RAT/terceiros são configuráveis por escola.

Atenção: este é um motor de DIAGNÓSTICO. O Lucro Real (PIS/COFINS não
cumulativos) admite créditos que dependem da escrituração; aqui usamos a
incidência cheia sobre a receita, sinalizada como aproximação.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

REGIMES = ("simples", "presumido", "real")

# --- Simples Nacional - Anexo III (estabelecimentos de ensino) --------------
# (limite_superior_RBT12, aliquota_nominal, parcela_a_deduzir)
ANEXO_III_FAIXAS: List[Tuple[float, float, float]] = [
    (180_000.0, 0.060, 0.0),
    (360_000.0, 0.1120, 9_360.0),
    (720_000.0, 0.1350, 17_640.0),
    (1_800_000.0, 0.1600, 35_640.0),
    (3_600_000.0, 0.2100, 125_640.0),
    (4_800_000.0, 0.3300, 648_000.0),
]

# Repartição do DAS no Anexo III por faixa: (IRPJ, CSLL, COFINS, PIS, CPP, ISS)
ANEXO_III_REPARTICAO: List[Tuple[float, float, float, float, float, float]] = [
    (0.04, 0.035, 0.1282, 0.0278, 0.434, 0.335),
    (0.04, 0.035, 0.1405, 0.0305, 0.434, 0.320),
    (0.04, 0.035, 0.1364, 0.0296, 0.434, 0.325),
    (0.04, 0.035, 0.1364, 0.0296, 0.434, 0.325),
    (0.04, 0.035, 0.1282, 0.0278, 0.434, 0.335),
    (0.35, 0.15, 0.1603, 0.0347, 0.305, 0.0),  # 6ª faixa: ISS recolhido à parte
]


def _r(v: float) -> float:
    return round(v + 1e-9, 2)


@dataclass
class ParametrosTributarios:
    regime: str = "simples"                 # simples | presumido | real
    # --- Simples ---
    anexo: str = "III"
    rbt12: float = 0.0                       # receita bruta dos últimos 12 meses
    # --- ISS municipal (presumido/real) ---
    iss_pct: float = 0.05                    # 2% a 5% conforme município
    # --- INSS patronal (presumido/real) ---
    inss_cpp: float = 0.20                   # contribuição previdenciária patronal
    inss_rat: float = 0.03                   # RAT x FAP (1% a 3%)
    inss_terceiros: float = 0.058            # Sistema S + salário-educação (ensino)
    # --- adicional de IRPJ (presumido/real) ---
    irpj_adicional_limite_mensal: float = 20_000.0


def faixa_simples(rbt12: float) -> int:
    for i, (lim, _, _) in enumerate(ANEXO_III_FAIXAS):
        if rbt12 <= lim:
            return i
    return len(ANEXO_III_FAIXAS) - 1


def aliquota_efetiva_simples(rbt12: float) -> float:
    """Alíquota efetiva do Anexo III: (RBT12*aliq - PD) / RBT12."""
    if rbt12 <= 0:
        # Início de atividade: usa a 1ª faixa (alíquota nominal).
        return ANEXO_III_FAIXAS[0][1]
    _, aliq, pd = ANEXO_III_FAIXAS[faixa_simples(rbt12)]
    return max(0.0, (rbt12 * aliq - pd) / rbt12)


def inss_patronal_pct(p: ParametrosTributarios) -> float:
    """INSS patronal sobre a folha. Zero no Simples (CPP já está no DAS)."""
    if p.regime == "simples":
        return 0.0
    return _r4(p.inss_cpp + p.inss_rat + p.inss_terceiros)


def _r4(v: float) -> float:
    return round(v + 1e-12, 4)


@dataclass
class TributosResultado:
    regime: str
    # tributos sobre a receita/resultado (valores mensais)
    detalhe: Dict[str, float]               # ir, csll, pis, cofins, iss, das...
    total_sobre_receita: float
    carga_efetiva_sobre_receita: float      # fração da receita
    # encargo de INSS patronal sobre a folha
    inss_patronal_pct: float
    inss_patronal_valor: float
    observacoes: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "regime": self.regime,
            "detalhe": self.detalhe,
            "total_sobre_receita": self.total_sobre_receita,
            "carga_efetiva_sobre_receita": self.carga_efetiva_sobre_receita,
            "inss_patronal_pct": self.inss_patronal_pct,
            "inss_patronal_valor": self.inss_patronal_valor,
            "observacoes": self.observacoes,
        }


def calcular_tributos(
    receita_mensal: float,
    folha_bruta_mensal: float,
    params: ParametrosTributarios,
    lucro_mensal: Optional[float] = None,
) -> TributosResultado:
    """
    Calcula os tributos conforme o regime.

    receita_mensal     receita bruta do mês
    folha_bruta_mensal salário bruto do mês (base do INSS patronal)
    lucro_mensal       resultado do mês (necessário só no Lucro Real)
    """
    regime = params.regime
    obs: List[str] = []
    inss_pct = inss_patronal_pct(params)
    inss_valor = _r(folha_bruta_mensal * inss_pct)

    if regime == "simples":
        efetiva = aliquota_efetiva_simples(params.rbt12)
        das = _r(receita_mensal * efetiva)
        faixa = faixa_simples(params.rbt12)
        rep = ANEXO_III_REPARTICAO[faixa]
        nomes = ("ir", "csll", "cofins", "pis", "cpp_inss", "iss")
        detalhe = {n: _r(das * frac) for n, frac in zip(nomes, rep)}
        detalhe["das_total"] = das
        obs.append(
            f"Simples Nacional Anexo III, faixa {faixa + 1} "
            f"(RBT12 = R$ {params.rbt12:,.2f}); alíquota efetiva "
            f"{efetiva * 100:.2f}%. IRPJ, CSLL, PIS, COFINS, INSS patronal "
            f"(CPP) e ISS já estão embutidos no DAS."
        )
        if faixa == 5:
            obs.append(
                "6ª faixa: o ISS é recolhido fora do DAS quando há "
                "ultrapassagem do sublimite estadual."
            )
        return TributosResultado(
            regime=regime,
            detalhe=detalhe,
            total_sobre_receita=das,
            carga_efetiva_sobre_receita=_r4(efetiva),
            inss_patronal_pct=inss_pct,
            inss_patronal_valor=inss_valor,
            observacoes=obs,
        )

    # --- Lucro Presumido ---
    if regime == "presumido":
        base = receita_mensal * 0.32                      # presunção serviços
        irpj = base * 0.15
        adicional = max(0.0, base - params.irpj_adicional_limite_mensal) * 0.10
        csll = base * 0.09
        pis = receita_mensal * 0.0065
        cofins = receita_mensal * 0.03
        iss = receita_mensal * params.iss_pct
        detalhe = {
            "ir": _r(irpj + adicional),
            "ir_adicional": _r(adicional),
            "csll": _r(csll),
            "pis": _r(pis),
            "cofins": _r(cofins),
            "iss": _r(iss),
        }
        total = _r(irpj + adicional + csll + pis + cofins + iss)
        obs.append(
            "Lucro Presumido (serviços, presunção 32%): IRPJ 15% + adicional "
            "10%, CSLL 9% sobre a base; PIS 0,65% e COFINS 3% sobre a receita; "
            f"ISS {params.iss_pct * 100:.1f}% (municipal)."
        )
        obs.append(
            f"INSS patronal sobre a folha: {inss_pct * 100:.1f}% "
            "(CPP 20% + RAT + terceiros)."
        )
        return TributosResultado(
            regime=regime,
            detalhe=detalhe,
            total_sobre_receita=total,
            carga_efetiva_sobre_receita=_r4(total / receita_mensal) if receita_mensal else 0.0,
            inss_patronal_pct=inss_pct,
            inss_patronal_valor=inss_valor,
            observacoes=obs,
        )

    # --- Lucro Real ---
    if regime == "real":
        lucro = lucro_mensal if lucro_mensal is not None else 0.0
        if lucro_mensal is None:
            obs.append(
                "Lucro Real: IRPJ e CSLL dependem do lucro do período. "
                "Informe o lucro mensal para o cálculo completo."
            )
        irpj = max(0.0, lucro) * 0.15
        adicional = max(0.0, lucro - params.irpj_adicional_limite_mensal) * 0.10
        csll = max(0.0, lucro) * 0.09
        pis = receita_mensal * 0.0165
        cofins = receita_mensal * 0.076
        iss = receita_mensal * params.iss_pct
        detalhe = {
            "ir": _r(irpj + adicional),
            "ir_adicional": _r(adicional),
            "csll": _r(csll),
            "pis": _r(pis),
            "cofins": _r(cofins),
            "iss": _r(iss),
        }
        total = _r(irpj + adicional + csll + pis + cofins + iss)
        obs.append(
            "Lucro Real: IRPJ 15% + adicional 10% e CSLL 9% sobre o lucro; "
            "PIS 1,65% e COFINS 7,6% sobre a receita (sem considerar créditos "
            "— aproximação de diagnóstico); ISS municipal."
        )
        obs.append(
            f"INSS patronal sobre a folha: {inss_pct * 100:.1f}%."
        )
        return TributosResultado(
            regime=regime,
            detalhe=detalhe,
            total_sobre_receita=total,
            carga_efetiva_sobre_receita=_r4(total / receita_mensal) if receita_mensal else 0.0,
            inss_patronal_pct=inss_pct,
            inss_patronal_valor=inss_valor,
            observacoes=obs,
        )

    raise ValueError(f"Regime tributário desconhecido: {regime!r}")


def encargos_inss_para_regime(params: ParametrosTributarios) -> float:
    """Atalho usado pela Folha: alíquota de INSS patronal conforme o regime."""
    return inss_patronal_pct(params)
