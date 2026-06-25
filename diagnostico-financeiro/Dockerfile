FROM python:3.11-slim

# Evita .pyc e usa saída sem buffer (logs imediatos)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependências primeiro (cache de build)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir "psycopg[binary]>=3.1" gunicorn

# Código da aplicação
COPY . .

# Usuário sem privilégios
RUN useradd -m app && chown -R app:app /app
USER app

EXPOSE 8000

# 2 workers Uvicorn sob Gunicorn (ajuste -w conforme as CPUs do servidor)
CMD ["gunicorn", "api.main:app", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "-b", "0.0.0.0:8000", "-w", "2", \
     "--access-logfile", "-", "--error-logfile", "-"]
