"""
Testa a camada de publicação: segurança de senha, login, controle de acesso
(consultor x escola) e diagnósticos salvos por escola.

Usa um banco SQLite temporário e isolado por execução.
"""

import os
import tempfile
import unittest

# Banco isolado ANTES de importar qualquer módulo que toque no engine do BD.
_TMPDB = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
_TMPDB.close()
os.environ["DATABASE_URL"] = "sqlite:///" + _TMPDB.name
os.environ["ADMIN_EMAIL"] = "consultor@teste.com"
os.environ["ADMIN_SENHA"] = "senha-consultor"

from fastapi.testclient import TestClient  # noqa: E402

from api.main import app  # noqa: E402
from db.bootstrap import init_db  # noqa: E402
from db.security import hash_senha, verificar_senha  # noqa: E402

init_db()  # cria tabelas + consultor admin no banco de teste


class TestSeguranca(unittest.TestCase):
    def test_hash_verifica(self):
        h = hash_senha("minha-senha")
        self.assertTrue(verificar_senha("minha-senha", h))
        self.assertFalse(verificar_senha("errada", h))

    def test_hash_nao_guarda_texto(self):
        h = hash_senha("segredo")
        self.assertNotIn("segredo", h)
        self.assertTrue(h.startswith("pbkdf2_sha256$"))


class TestFluxoMultiEscola(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = TestClient(app)

    def _login(self, email, senha):
        r = self.c.post("/api/auth/login", json={"email": email, "senha": senha})
        self.assertEqual(r.status_code, 200, r.text)
        return {"Authorization": "Bearer " + r.json()["token"]}

    def test_01_login_consultor(self):
        h = self._login("consultor@teste.com", "senha-consultor")
        me = self.c.get("/api/auth/me", headers=h).json()
        self.assertEqual(me["papel"], "consultor")

    def test_02_login_invalido(self):
        r = self.c.post("/api/auth/login", json={"email": "x@x.com", "senha": "z"})
        self.assertEqual(r.status_code, 401)

    def test_03_consultor_cria_escola_e_usuario(self):
        h = self._login("consultor@teste.com", "senha-consultor")
        esc = self.c.post("/api/escolas", json={"nome": "Colégio A"}, headers=h)
        self.assertEqual(esc.status_code, 200, esc.text)
        eid = esc.json()["id"]
        u = self.c.post("/api/usuarios", json={
            "email": "escolaA@teste.com", "nome": "Escola A",
            "senha": "senha-escola", "papel": "escola", "escola_id": eid,
        }, headers=h)
        self.assertEqual(u.status_code, 200, u.text)

    def test_04_escola_nao_cria_escola(self):
        h = self._login("escolaA@teste.com", "senha-escola")
        r = self.c.post("/api/escolas", json={"nome": "Pirata"}, headers=h)
        self.assertEqual(r.status_code, 403)

    def test_05_isolamento_entre_escolas(self):
        hcons = self._login("consultor@teste.com", "senha-consultor")
        # segunda escola + usuário
        eid2 = self.c.post("/api/escolas", json={"nome": "Colégio B"}, headers=hcons).json()["id"]
        self.c.post("/api/usuarios", json={
            "email": "escolaB@teste.com", "nome": "Escola B",
            "senha": "senha-escola", "papel": "escola", "escola_id": eid2,
        }, headers=hcons)
        # escola A salva um diagnóstico
        ha = self._login("escolaA@teste.com", "senha-escola")
        eid_a = self.c.get("/api/escolas", headers=ha).json()[0]["id"]
        salvar = self.c.post("/api/diagnosticos", json={
            "escola_id": eid_a, "ano": 2025, "dados": {"receita": 100},
        }, headers=ha)
        self.assertEqual(salvar.status_code, 200, salvar.text)
        diag_id = salvar.json()["id"]
        # escola B NÃO pode ver o diagnóstico da escola A
        hb = self._login("escolaB@teste.com", "senha-escola")
        r = self.c.get(f"/api/diagnosticos/{diag_id}", headers=hb)
        self.assertEqual(r.status_code, 403)
        # consultor pode ver
        r2 = self.c.get(f"/api/diagnosticos/{diag_id}", headers=hcons)
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["dados"]["receita"], 100)

    def test_06_escola_so_ve_a_propria(self):
        ha = self._login("escolaA@teste.com", "senha-escola")
        escolas = self.c.get("/api/escolas", headers=ha).json()
        self.assertEqual(len(escolas), 1)
        self.assertEqual(escolas[0]["nome"], "Colégio A")

    def test_07_sem_token(self):
        self.assertEqual(self.c.get("/api/auth/me").status_code, 401)


if __name__ == "__main__":
    unittest.main(verbosity=2)
