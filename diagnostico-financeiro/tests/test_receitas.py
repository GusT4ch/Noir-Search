"""
Valida o motor de receitas contra os números da "Escola Modelo" que já
existem na planilha Ágora (abas RECEITAS / DRE).

Valores de referência da planilha (mensais):
    Receita bruta mensal ......... 819.094,00
    (-) Descontos ................  89.241,17
    (=) Receita líq. mensalidade . 729.852,83
    (+) Outras receitas .......... 112.202,97
    (=) Receita líquida .......... 842.055,80
"""

import json
import os
import unittest

from engine import (
    OutraReceita,
    ReceitasInput,
    SegmentoInput,
    calcular_receitas,
)

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "escola_modelo.json")


def carregar_modelo() -> ReceitasInput:
    with open(DATA, encoding="utf-8") as fh:
        raw = json.load(fh)
    return ReceitasInput(
        escola=raw["escola"],
        ano_referencia=raw["ano_referencia"],
        segmentos=[SegmentoInput(**s) for s in raw["segmentos"]],
        outras_receitas=[OutraReceita(**o) for o in raw["outras_receitas"]],
    )


class TestReceitasEscolaModelo(unittest.TestCase):
    def setUp(self):
        self.res = calcular_receitas(carregar_modelo())

    def test_total_alunos(self):
        self.assertEqual(self.res.total_alunos, 687)

    def test_receita_bruta(self):
        # Tolerância de R$5 por arredondamento da mensalidade média.
        self.assertAlmostEqual(self.res.receita_bruta_mensal, 819094.00, delta=5)

    def test_descontos(self):
        self.assertAlmostEqual(self.res.descontos_mensal, 89241.17, delta=5)

    def test_receita_liquida_mensalidade(self):
        self.assertAlmostEqual(
            self.res.receita_liquida_mensalidade_mensal, 729852.83, delta=10
        )

    def test_outras_receitas(self):
        self.assertAlmostEqual(self.res.outras_receitas_mensal, 112202.97, delta=0.01)

    def test_receita_liquida_total(self):
        self.assertAlmostEqual(self.res.receita_liquida_mensal, 842055.80, delta=10)

    def test_receita_anual(self):
        self.assertAlmostEqual(
            self.res.receita_liquida_anual,
            self.res.receita_liquida_mensal * 12,
            delta=0.01,
        )

    def test_participacao_soma_100(self):
        soma = sum(s.participacao_pct for s in self.res.segmentos)
        self.assertAlmostEqual(soma, 100.0, delta=0.5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
