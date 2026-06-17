"""
Valida o motor de Custos + DRE contra a aba `DRE` da planilha Ágora
(coluna mensal projetada 2025) e confere o rateio por nível.
"""

import json
import os
import unittest

from engine import DREInput, LinhaCusto, calcular_dre

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "escola_modelo_dre.json")


def carregar() -> DREInput:
    with open(DATA, encoding="utf-8") as fh:
        raw = json.load(fh)
    return DREInput(
        escola=raw["escola"],
        ano=raw["ano"],
        niveis=raw["niveis"],
        receita_liquida_total=raw["receita_liquida_total"],
        receita_por_nivel=raw["receita_por_nivel"],
        alunos_por_nivel=raw["alunos_por_nivel"],
        custos=[LinhaCusto(**c) for c in raw["custos"]],
        depreciacao=raw["depreciacao"],
        juros=raw["juros"],
        irpj=raw.get("irpj", 0.0),
        csll=raw.get("csll", 0.0),
    )


class TestDRE(unittest.TestCase):
    def setUp(self):
        self.res = calcular_dre(carregar())

    # --- cascata do DRE (valores da planilha) ---
    def test_receita_liquida(self):
        self.assertAlmostEqual(self.res.receita_liquida, 842055.80, delta=0.05)

    def test_custos_diretos(self):
        self.assertAlmostEqual(self.res.custos_diretos, 423326.57, delta=0.05)

    def test_margem_contribuicao(self):
        self.assertAlmostEqual(self.res.margem_contribuicao, 418729.23, delta=0.05)

    def test_custos_indiretos(self):
        self.assertAlmostEqual(self.res.custos_indiretos, 383997.29, delta=0.05)

    def test_ebitda(self):
        self.assertAlmostEqual(self.res.ebitda, 34731.94, delta=0.05)

    def test_ebit(self):
        self.assertAlmostEqual(self.res.ebit, 27095.49, delta=0.05)

    def test_lucro_operacional(self):
        self.assertAlmostEqual(self.res.lucro_operacional, 27095.49, delta=0.05)

    # --- indicadores ---
    def test_margens(self):
        self.assertAlmostEqual(self.res.margem_contribuicao_pct, 0.4973, places=3)
        self.assertAlmostEqual(self.res.margem_ebitda_pct, 0.0412, places=3)
        self.assertGreater(self.res.ponto_equilibrio_receita, 0)

    # --- rateio por nível ---
    def test_rateio_soma_receita(self):
        soma = sum(d["receita_liquida"] for d in self.res.por_nivel.values())
        self.assertAlmostEqual(soma, sum(carregar().receita_por_nivel.values()), delta=0.05)

    def test_rateio_custos_reconciliam(self):
        # A soma dos custos rateados por nível = custos totais + depr + juros.
        soma_custos = sum(d["custo_total"] for d in self.res.por_nivel.values())
        esperado = (
            self.res.custos_diretos
            + self.res.custos_indiretos
            + self.res.depreciacao
            + self.res.juros
        )
        self.assertAlmostEqual(soma_custos, esperado, delta=0.1)

    def test_custo_por_aluno_positivo(self):
        for d in self.res.por_nivel.values():
            self.assertGreater(d["custo_por_aluno_mes"], 0)


class TestRateioPorNivelExplicito(unittest.TestCase):
    def test_por_nivel_tem_prioridade(self):
        # Um custo com alocação explícita por nível não deve ser rateado por receita.
        dados = DREInput(
            escola="t", ano=2025, niveis=["A", "B"],
            receita_liquida_total=1000.0,
            receita_por_nivel={"A": 900.0, "B": 100.0},
            alunos_por_nivel={"A": 10, "B": 10},
            custos=[
                LinhaCusto("docentes", 200.0, "direto", por_nivel={"A": 50.0, "B": 150.0}),
            ],
        )
        r = calcular_dre(dados)
        self.assertAlmostEqual(r.por_nivel["A"]["custo_total"], 50.0, delta=0.01)
        self.assertAlmostEqual(r.por_nivel["B"]["custo_total"], 150.0, delta=0.01)


if __name__ == "__main__":
    unittest.main(verbosity=2)
