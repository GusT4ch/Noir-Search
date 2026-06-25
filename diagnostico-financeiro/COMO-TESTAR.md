# Como testar com uma escola real

Dá para testar de duas formas. Comece pela que for mais confortável.

> **Importante (LGPD):** o sistema só usa **números agregados** (quantidades,
> médias, totais). **Não** informe nome, CPF ou qualquer dado pessoal de aluno.

---

## Opção 1 — Olhada rápida, sem instalar nada

As telas de cálculo funcionam **sozinhas no navegador**. Basta abrir o arquivo
(duplo clique) e preencher com os números da escola:

- `web/index.html` — **Receitas**
- `web/Diagnostico-Folha.html` — **Folha de pagamento**
- `web/Regime-Tributario.html` — **Regime tributário** (Simples/Presumido/Real)
- `web/Analise-SWOT.html` — **Análise SWOT** (a bolinha)

Bom para sentir cada módulo. Para o **painel consolidado**, os **relatórios**
(PDF/Word/PPTX) e o **login por escola**, use a Opção 2.

---

## Opção 2 — Sistema completo no seu computador

Precisa de **Python 3.11+** instalado. Depois:

1. Baixe o projeto (pasta `diagnostico-financeiro`).
2. No terminal, dentro da pasta, rode:
   ```bash
   bash rodar.sh
   ```
3. Abra no navegador: **http://127.0.0.1:8000**
4. Faça login como consultor:
   - e-mail: `consultor@exemplo.com`
   - senha: `teste123`

A partir daí:
- Em **Acesso / Portal**, cadastre a escola (e, se quiser, um usuário para ela).
- Use os módulos para preencher os números.
- Veja o **Painel consolidado**.
- Baixe o **relatório** em PDF, Word ou PowerPoint.

---

## O que coletar com a escola (checklist)

### Receitas (por nível: Infantil, Fund. I, Fund. II, Médio)
- Nº de alunos matriculados
- Mensalidade média
- % médio de desconto/bolsa concedido
- % de inadimplência
- Outras receitas mensais (período integral, material, cantina, etc.)

### Folha de pagamento
- **Professores e auxiliares**: salário e em quais níveis atuam (em %)
- **Coordenação/supervisão de ensino**: salário e níveis (em %)
- **Administrativo** (diretores, secretaria, limpeza, segurança, etc.): salário

### Regime tributário
- Regime: Simples, Lucro Presumido ou Lucro Real
- Faturamento dos últimos 12 meses (define a faixa do Simples)
- Alíquota de ISS do município (geralmente 2% a 5%)

### Custos e despesas (para o DRE)
- Aluguel, contabilidade, marketing, água/luz/telefone, material, despesas
  administrativas e financeiras, pró-labore
- Depreciação e juros (se houver)
- Provisões: % de evasão, % de inadimplência, % de reequipamento

### SWOT
- Notas de 0 a 10 para cada fator (forças, fraquezas, oportunidades, ameaças)

---

## Para a escola acessar pela internet

Quando quiser que a própria escola entre de qualquer lugar, publicamos o
sistema num servidor (em São Paulo, com HTTPS e backup). O passo a passo está
em **[DEPLOY.md](DEPLOY.md)**.
