"""
Valida o motor tributário contra os percentuais legais (Simples Anexo III,
Lucro Presumido e Lucro Real) e a regra do INSS patronal por regime.
"""

import unittest

from engine import (
    ParametrosTributarios,
    aliquota_efetiva_simples,
    calcular_tributos,
    inss_patronal_pct,
)


class TestSimples(unittest.TestCase):
    def test_primeira_faixa_e_inicio_atividade(self):
        self.assertAlmostEqual(aliquota_efetiva_simples(0), 0.06, places=6)
        self.assertAlmostEqual(aliquota_efetiva_simples(100_000), 0.06, places=6)

    def test_faixa_3_efetiva(self):
        # (500000*0,135 - 17640)/500000
        self.assertAlmostEqual(aliquota_efetiva_simples(500_000), 0.09972, places=5)

    def test_inss_patronal_zero_no_simples(self):
        p = ParametrosTributarios(regime="simples", rbt12=1_000_000)
        self.assertEqual(inss_patronal_pct(p), 0.0)

    def test_das_e_reparticao(self):
        p = ParametrosTributarios(regime="simples", rbt12=1_000_000)
        r = calcular_tributos(receita_mensal=100_000, folha_bruta_mensal=50_000, params=p)
        # efetiva 4ª faixa = (1e6*0,16 - 35640)/1e6 = 0,12436
        self.assertAlmostEqual(r.carga_efetiva_sobre_receita, 0.1244, places=4)
        self.assertAlmostEqual(r.total_sobre_receita, 12436.0, delta=0.5)
        # a soma dos tributos repartidos = DAS
        soma = sum(
            v for k, v in r.detalhe.items() if k != "das_total"
        )
        self.assertAlmostEqual(soma, r.detalhe["das_total"], delta=0.05)
        self.assertEqual(r.inss_patronal_valor, 0.0)


class TestPresumido(unittest.TestCase):
    def setUp(self):
        self.p = ParametrosTributarios(regime="presumido", iss_pct=0.05)
        self.r = calcular_tributos(100_000, 50_000, self.p)

    def test_componentes(self):
        d = self.r.detalhe
        self.assertAlmostEqual(d["ir"], 4800 + 1200, delta=0.05)   # 15%*32k + 10%*(32k-20k)
        self.assertAlmostEqual(d["csll"], 2880, delta=0.05)        # 9%*32k
        self.assertAlmostEqual(d["pis"], 650, delta=0.05)          # 0,65%*100k
        self.assertAlmostEqual(d["cofins"], 3000, delta=0.05)      # 3%*100k
        self.assertAlmostEqual(d["iss"], 5000, delta=0.05)         # 5%*100k

    def test_total_e_inss(self):
        self.assertAlmostEqual(self.r.total_sobre_receita, 17530, delta=0.1)
        self.assertAlmostEqual(self.r.inss_patronal_pct, 0.288, places=4)
        self.assertAlmostEqual(self.r.inss_patronal_valor, 14400, delta=0.5)


class TestReal(unittest.TestCase):
    def test_real_com_lucro(self):
        p = ParametrosTributarios(regime="real", iss_pct=0.05)
        r = calcular_tributos(100_000, 50_000, p, lucro_mensal=10_000)
        d = r.detalhe
        self.assertAlmostEqual(d["ir"], 1500, delta=0.05)     # 15%*10k, sem adicional
        self.assertAlmostEqual(d["csll"], 900, delta=0.05)    # 9%*10k
        # Educação: PIS/COFINS cumulativos mesmo no Lucro Real (Lei 10.833/03)
        self.assertAlmostEqual(d["pis"], 650, delta=0.05)     # 0,65%*100k
        self.assertAlmostEqual(d["cofins"], 3000, delta=0.05) # 3%*100k
        self.assertAlmostEqual(r.total_sobre_receita, 11050, delta=0.1)
        self.assertAlmostEqual(r.inss_patronal_pct, 0.288, places=4)


class TestRegimeInvalido(unittest.TestCase):
    def test_erro(self):
        with self.assertRaises(ValueError):
            calcular_tributos(1000, 500, ParametrosTributarios(regime="xpto"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
