"""
Segurança sem dependências externas (evita libs nativas frágeis):

  * Senhas: PBKDF2-HMAC-SHA256 com salt aleatório (formato
    pbkdf2_sha256$iteracoes$salt$hash). Comparação em tempo constante.
  * Tokens de sessão: aleatórios (secrets). No banco guardamos apenas o
    hash SHA-256 do token — se o banco vazar, os tokens não são reutilizáveis.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

_ITERACOES = 240_000


def hash_senha(senha: str, iteracoes: int = _ITERACOES) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, iteracoes)
    return "pbkdf2_sha256${}${}${}".format(
        iteracoes,
        base64.b64encode(salt).decode(),
        base64.b64encode(dk).decode(),
    )


def verificar_senha(senha: str, armazenado: str) -> bool:
    try:
        algo, iteracoes, salt_b64, hash_b64 = armazenado.split("$")
        if algo != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64)
        esperado = base64.b64decode(hash_b64)
        dk = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, int(iteracoes))
        return hmac.compare_digest(dk, esperado)
    except Exception:
        return False


def gerar_token() -> str:
    """Token entregue ao cliente (não é guardado em texto no banco)."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
