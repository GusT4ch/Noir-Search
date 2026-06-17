"""
Valida o motor de SWOT: médias ponderadas por grupo, eixos e quadrante
(posição da "bolinha").
"""

import json
import os
import unittest

from engine import FatorSWOT, SWOTInput, calcular_swot

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "escola_modelo_swot.json")


def carregar() -> SWOTInput:
    with open(DATA, encoding="utf-8") as fh:
        raw = json.load(fh)
    return SWOTInput(
        escola=raw["escola"],
        ano=raw["ano"],
        fatores=[FatorSWOT(**f) for f in raw["fatores"]],
    )


class TestSWOT(unittest.TestCase):
    def test_scores_no_intervalo(self):
        r = calcular_swot(carregar())
        for cat, v in r.scores.items():
            self.assertGreaterEqual(v, 0.0)
            self.assertLessEqual(v, 10.0)

    def test_eixos_consistentes(self):
        r = calcular_swot(carregar())
        self.assertAlmostEqual(
            r.eixo_interno, r.scores["forca"] - r.scores["fraqueza"], delta=0.01
        )
        self.assertAlmostEqual(
            r.eixo_externo, r.scores["oportunidade"] - r.scores["ameaca"], delta=0.01
        )

    def test_media_ponderada(self):
        # Dois fatores de força: notas 10 (peso 3) e 0 (peso 1) => média 7.5
        dados = SWOTInput("t", 2025, [
            FatorSWOT("a", "forca", 10, 3),
            FatorSWOT("b", "forca", 0, 1),
        ])
        r = calcular_swot(dados)
        self.assertAlmostEqual(r.scores["forca"], 7.5, delta=0.01)

    def test_quadrante_ofensiva(self):
        dados = SWOTInput("t", 2025, [
            FatorSWOT("f", "forca", 9, 1),
            FatorSWOT("w", "fraqueza", 2, 1),
            FatorSWOT("o", "oportunidade", 8, 1),
            FatorSWOT("a", "ameaca", 3, 1),
        ])
        r = calcular_swot(dados)
        self.assertEqual(r.quadrante, "ofensiva")
        self.assertGreater(r.eixo_interno, 0)
        self.assertGreater(r.eixo_externo, 0)

    def test_quadrante_sobrevivencia(self):
        dados = SWOTInput("t", 2025, [
            FatorSWOT("f", "forca", 2, 1),
            FatorSWOT("w", "fraqueza", 9, 1),
            FatorSWOT("o", "oportunidade", 2, 1),
            FatorSWOT("a", "ameaca", 8, 1),
        ])
        r = calcular_swot(dados)
        self.assertEqual(r.quadrante, "sobrevivencia")

    def test_grupo_vazio_nao_quebra(self):
        dados = SWOTInput("t", 2025, [FatorSWOT("f", "forca", 5, 1)])
        r = calcular_swot(dados)
        self.assertEqual(r.scores["ameaca"], 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
