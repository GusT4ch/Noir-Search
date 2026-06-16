"""
Valida o motor de Folha de Pagamento.

A planilha Ágora distribui a folha em vários blocos (registrados, sem
registro, extra-curriculares), então o número de telas de origem é grande.
Aqui validamos a CORREÇÃO do motor de forma rigorosa: recalculamos os
agregados de forma independente a partir do mesmo conjunto de dados e
conferimos contra a saída do motor. Também conferimos as regras de negócio
(encargos, alocação por nível, administrativos como "geral").
"""

import json
import os
import unittest

from engine import Colaborador, Encargos, FolhaInput, calcular_folha

DATA = os.path.join(
    os.path.dirname(__file__), "..", "data", "escola_modelo_folha.json"
)


def carregar() -> FolhaInput:
    with open(DATA, encoding="utf-8") as fh:
        raw = json.load(fh)
    return FolhaInput(
        escola=raw["escola"],
        ano_referencia=raw["ano_referencia"],
        niveis=raw["niveis"],
        colaboradores=[Colaborador(**c) for c in raw["colaboradores"]],
        encargos=Encargos(**raw["encargos"]),
    )


class TestFolha(unittest.TestCase):
    def setUp(self):
        self.dados = carregar()
        self.res = calcular_folha(self.dados)

    def test_salario_bruto_total(self):
        esperado = round(sum(c.salario_base for c in self.dados.colaboradores), 2)
        self.assertAlmostEqual(self.res.salario_bruto_mensal, esperado, delta=0.05)

    def test_categorias_somam_o_total(self):
        soma = sum(d["salario_bruto"] for d in self.res.por_categoria.values())
        self.assertAlmostEqual(soma, self.res.salario_bruto_mensal, delta=0.05)

    def test_encargos_aplicados(self):
        enc = self.dados.encargos.total_pct
        self.assertAlmostEqual(
            self.res.encargos_mensal,
            round(self.res.salario_bruto_mensal * enc, 2),
            delta=0.05,
        )
        self.assertAlmostEqual(
            self.res.custo_total_mensal,
            self.res.salario_bruto_mensal + self.res.encargos_mensal,
            delta=0.05,
        )

    def test_custo_anual(self):
        self.assertAlmostEqual(
            self.res.custo_total_anual, self.res.custo_total_mensal * 12, delta=0.05
        )

    def test_alocacao_por_nivel_confere(self):
        # Recalcula a alocação por nível de forma independente.
        esperado = {n: 0.0 for n in self.dados.niveis}
        geral = 0.0
        for c in self.dados.colaboradores:
            if c.alocacao:
                for n, f in c.alocacao.items():
                    esperado[n] = esperado.get(n, 0) + c.salario_base * f
            else:
                geral += c.salario_base
        for n in self.dados.niveis:
            self.assertAlmostEqual(self.res.por_nivel[n], round(esperado[n], 2), delta=0.05)
        self.assertAlmostEqual(self.res.geral_nao_alocado, round(geral, 2), delta=0.05)

    def test_administrativos_sao_gerais(self):
        # Administrativos não devem entrar na alocação por nível.
        admin = sum(
            c.salario_base
            for c in self.dados.colaboradores
            if c.categoria == "administrativo"
        )
        self.assertGreater(admin, 0)
        self.assertGreaterEqual(self.res.geral_nao_alocado, round(admin, 2) - 0.05)

    def test_docentes_alocados_integralmente(self):
        # Cada docente do modelo aloca 100% entre os níveis.
        for c in self.dados.colaboradores:
            if c.categoria == "docente":
                self.assertAlmostEqual(sum(c.alocacao.values()), 1.0, delta=0.001)


if __name__ == "__main__":
    unittest.main(verbosity=2)
