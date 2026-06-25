# Guia de Publicação (Hospedagem)

Como colocar o sistema no ar com **segurança**, **baixo custo** e **dados no
Brasil** (LGPD). O projeto já vem com tudo pronto para subir via Docker.

## Recomendação de servidor

- **VPS em São Paulo** (dados no Brasil) — ex.: Magalu Cloud, ou outra VPS BR.
- Configuração inicial sugerida: **2 vCPU / 4 GB RAM / 40 GB SSD** (~R$40–80/mês).
- Sistema: Ubuntu 22.04 LTS.

## O que já está incluído

| Arquivo | Função |
|---|---|
| `Dockerfile` | Empacota a aplicação (FastAPI + Gunicorn/Uvicorn). |
| `docker-compose.yml` | Sobe **PostgreSQL + aplicação + Caddy (HTTPS)**. |
| `Caddyfile` | HTTPS automático (Let's Encrypt), com renovação sozinha. |
| `.env.example` | Modelo das variáveis de ambiente. |

## Passo a passo

1. **Aponte o domínio** (ex.: `diagnostico.suaescola.com.br`) para o IP do
   servidor (registro DNS tipo A).

2. **No servidor**, instale o Docker:
   ```bash
   curl -fsSL https://get.docker.com | sh
   ```

3. **Envie o projeto** para o servidor (git clone ou scp) e entre na pasta
   `diagnostico-financeiro`.

4. **Configure as variáveis**:
   ```bash
   cp .env.example .env
   nano .env   # defina DB_PASSWORD, ADMIN_EMAIL, ADMIN_SENHA e DOMINIO
   ```

5. **Suba tudo**:
   ```bash
   docker compose up -d --build
   ```
   Pronto: a aplicação responde em `https://SEU_DOMINIO` com cadeado válido.
   O consultor admin é criado automaticamente com o e-mail/senha do `.env`.

6. **Primeiro acesso**: entre em `https://SEU_DOMINIO/` (tela de login),
   cadastre as escolas e os usuários de cada escola.

## Segurança

- **HTTPS** automático (Caddy + Let's Encrypt).
- **Senhas** com PBKDF2-HMAC-SHA256; tokens de sessão guardados só como hash.
- **Dados no Brasil** (servidor em SP) — atende à LGPD sem transferência
  internacional.
- **Sem dados pessoais de aluno** — só números agregados.
- Mantenha o `.env` fora do versionamento (já está no `.gitignore`).

## Backup do banco (diário, recomendado)

Crie um cron no servidor para exportar o banco e guardar criptografado:

```bash
# /etc/cron.daily/backup-diagnostico  (chmod +x)
docker compose -f /caminho/docker-compose.yml exec -T db \
  pg_dump -U diagnostico diagnostico | gzip > /backups/diag_$(date +%F).sql.gz
# Envie /backups para um storage externo (object storage BR) e mantenha 30 dias.
```

## Atualizações

```bash
git pull
docker compose up -d --build
```

As tabelas do banco são criadas/garantidas automaticamente no start. Para
mudanças de estrutura mais complexas no futuro, adotaremos migrações (Alembic).

## Custo aproximado

- VPS São Paulo: **R$ 40–80/mês** (no início).
- Domínio: ~R$ 40/ano.
- Certificado HTTPS: **grátis** (Let's Encrypt).
