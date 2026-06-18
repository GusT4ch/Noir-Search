"""
Consolida o diagnóstico: roda todos os módulos (Receitas, Folha, Tributos,
DRE, SWOT) e devolve uma única estrutura que alimenta os relatórios
(.docx / .pptx / .pdf).
"""

from __future__ import annotations

import json
import os
from datetime import date
from typing import Optional

from engine import (
    Colaborador,
    DREInput,
    Encargos,
    FatorSWOT,
    FolhaInput,
    LinhaCusto,
    OutraReceita,
    ParametrosTributarios,
    ReceitasInput,
    SegmentoInput,
    SWOTInput,
    calcular_dre,
    calcular_folha,
    calcular_receitas,
    calcular_swot,
    calcular_tributos,
    inss_patronal_pct,
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load(nome: str) -> dict:
    with open(os.path.join(DATA_DIR, nome), encoding="utf-8") as fh:
        return json.load(fh)


def montar_diagnostico_exemplo(regime: str = "simples") -> dict:
    """Monta o diagnóstico consolidado a partir dos dados de exemplo."""
    # --- Receitas ---
    r = _load("escola_modelo.json")
    receitas = calcular_receitas(ReceitasInput(
        escola=r["escola"], ano_referencia=r["ano_referencia"],
        segmentos=[SegmentoInput(**s) for s in r["segmentos"]],
        outras_receitas=[OutraReceita(**o) for o in r["outras_receitas"]],
    )).as_dict()

    receita_bruta_mensal = receitas["totais"]["receita_bruta_mensal"]
    receita_liquida_mensal = receitas["totais"]["receita_liquida_mensal"]
    receita_bruta_anual = receita_bruta_mensal * 12

    # --- Folha ---
    f = _load("escola_modelo_folha.json")
    params = ParametrosTributarios(regime=regime, rbt12=receita_bruta_anual)
    encargos = Encargos(**f["encargos"])
    encargos.inss_patronal = inss_patronal_pct(params)
    folha = calcular_folha(FolhaInput(
        escola=f["escola"], ano_referencia=f["ano_referencia"], niveis=f["niveis"],
        colaboradores=[Colaborador(**c) for c in f["colaboradores"]],
        encargos=encargos,
    )).as_dict()

    # --- Tributos ---
    tributos = calcular_tributos(
        receita_mensal=receita_bruta_mensal,
        folha_bruta_mensal=folha["totais"]["salario_bruto_mensal"],
        params=params,
    ).as_dict()

    # --- DRE ---
    d = _load("escola_modelo_dre.json")
    dre = calcular_dre(DREInput(
        escola=d["escola"], ano=d["ano"], niveis=d["niveis"],
        receita_liquida_total=d["receita_liquida_total"],
        receita_por_nivel=d["receita_por_nivel"],
        alunos_por_nivel=d["alunos_por_nivel"],
        custos=[LinhaCusto(**c) for c in d["custos"]],
        depreciacao=d["depreciacao"], juros=d["juros"],
        irpj=d.get("irpj", 0.0), csll=d.get("csll", 0.0),
    )).as_dict()

    # --- SWOT ---
    s = _load("escola_modelo_swot.json")
    swot = calcular_swot(SWOTInput(
        escola=s["escola"], ano=s["ano"],
        fatores=[FatorSWOT(**x) for x in s["fatores"]],
    )).as_dict()

    alunos_total = sum(seg["alunos"] for seg in receitas["segmentos"])

    return {
        "meta": {
            "escola": receitas["escola"],
            "ano": receitas["ano_referencia"],
            "regime": regime,
            "data_geracao": date.today().isoformat(),
        },
        "resumo": {
            "receita_liquida_mensal": receita_liquida_mensal,
            "custo_total_mensal": round(
                dre["dre"]["custos_diretos"] + dre["dre"]["custos_indiretos"]
                + dre["dre"]["depreciacao"] + dre["dre"]["juros"], 2),
            "lucro_operacional_mensal": dre["dre"]["lucro_operacional"],
            "margem_liquida_pct": dre["indicadores"]["margem_liquida_pct"],
            "ponto_equilibrio_receita": dre["indicadores"]["ponto_equilibrio_receita"],
            "alunos_total": alunos_total,
        },
        "receitas": receitas,
        "folha": folha,
        "tributos": tributos,
        "dre": dre,
        "swot": swot,
    }
