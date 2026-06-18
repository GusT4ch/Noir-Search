"""
Valida a consolidação do diagnóstico e a geração dos três formatos de
relatório (.docx, .pptx, .pdf).
"""

import os
import tempfile
import unittest

from report.consolidado import montar_diagnostico_exemplo
from report.gerar import gerar_docx, gerar_pdf, gerar_pptx


class TestConsolidado(unittest.TestCase):
    def test_estrutura(self):
        diag = montar_diagnostico_exemplo("simples")
        for chave in ("meta", "resumo", "receitas", "folha", "tributos", "dre", "swot"):
            self.assertIn(chave, diag)
        # o resumo deve refletir o DRE
        self.assertAlmostEqual(
            diag["resumo"]["lucro_operacional_mensal"], 27095.49, delta=0.05
        )

    def test_regime_altera_inss(self):
        simples = montar_diagnostico_exemplo("simples")
        presumido = montar_diagnostico_exemplo("presumido")
        self.assertEqual(simples["tributos"]["inss_patronal_pct"], 0.0)
        self.assertGreater(presumido["tributos"]["inss_patronal_pct"], 0.0)


class TestGeradores(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.diag = montar_diagnostico_exemplo("simples")

    def _gera(self, func, suf):
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suf)
        tmp.close()
        func(self.diag, tmp.name)
        self.assertTrue(os.path.exists(tmp.name))
        self.assertGreater(os.path.getsize(tmp.name), 1000)
        os.unlink(tmp.name)

    def test_docx(self):
        self._gera(gerar_docx, ".docx")

    def test_pptx(self):
        self._gera(gerar_pptx, ".pptx")

    def test_pdf(self):
        self._gera(gerar_pdf, ".pdf")


if __name__ == "__main__":
    unittest.main(verbosity=2)
