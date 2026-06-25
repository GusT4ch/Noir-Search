#!/usr/bin/env bash
# Sobe o sistema localmente para teste.
# Uso:  bash rodar.sh
set -e

cd "$(dirname "$0")"

echo ">> Instalando dependências (primeira vez pode demorar um pouco)..."
pip install -r requirements.txt >/dev/null

# Consultor administrador para o primeiro acesso (troque se quiser)
export ADMIN_EMAIL="${ADMIN_EMAIL:-consultor@exemplo.com}"
export ADMIN_SENHA="${ADMIN_SENHA:-teste123}"

echo
echo "==================================================================="
echo " Sistema no ar!  Abra no navegador:  http://127.0.0.1:8000"
echo " Login do consultor:"
echo "   e-mail: $ADMIN_EMAIL"
echo "   senha : $ADMIN_SENHA"
echo "==================================================================="
echo

uvicorn api.main:app --host 127.0.0.1 --port 8000
