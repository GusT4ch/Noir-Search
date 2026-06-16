# Planejamento do Produto — Diagnóstico Econômico/Financeiro para Escolas

Documento vivo com as decisões e o roteiro do projeto. Atualizado conforme
avançamos.

## Visão

Substituir o processo manual (planilha Excel + relatório no PowerPoint) por um
sistema web onde:

1. a escola (ou o consultor) informa os dados;
2. o sistema calcula automaticamente o diagnóstico (a lógica da planilha);
3. o resultado fica disponível online, com acesso seguro e por escola.

## Decisões tomadas

| Tema | Decisão |
|------|---------|
| **Acesso** | Multi-escola, com login. O **consultor** e as **escolas** acessam (papéis diferentes). |
| **Prioridade atual** | Concluir primeiro os **módulos de cálculo** (Receitas → Folha → Custos → DRE) e só depois publicar online. |
| **LGPD** | Trabalhar **somente com dados agregados** (nº de alunos, mensalidade média, salários por cargo). **Sem dados pessoais de alunos** (nada de nome/CPF). Isso reduz drasticamente o risco. |
| **Hospedagem (recomendação)** | Quando publicar: servidor em **São Paulo (dados no Brasil)**, banco PostgreSQL, **backup diário criptografado**, HTTPS e senhas com hash. Custo inicial estimado: ~R$ 40–80/mês. |

## Arquitetura planejada (para quando formos publicar)

```
Navegador (escola/consultor)
        │  HTTPS
        ▼
  Aplicação web (FastAPI)  ──►  Banco de dados (PostgreSQL)
        │                          - escolas (identificação)
        │                          - usuários (consultor/escola, senha com hash)
        │                          - diagnósticos salvos por escola/ano
        ▼
  Motor de cálculo (engine/)  ← já pronto e testado
```

- **Multi-escola:** cada escola tem um identificador; cada diagnóstico fica
  vinculado à escola e ao ano. O consultor vê todas; cada escola vê só a sua.
- **Segurança:** login com senha protegida (hash), HTTPS, separação dos dados
  por escola, backup criptografado.
- **Saídas:** painel na tela, exportação em PDF (no formato do PowerPoint) e
  documento `.docx` editável.

## Roteiro (status)

| # | Módulo / etapa | Status |
|---|----------------|--------|
| 1 | **Receitas** (alunos, mensalidades, descontos, outras receitas) | ✅ pronto e validado |
| 2 | **Folha de pagamento** (docentes/coordenação/admin, alocação por nível, encargos) | ✅ motor + testes prontos |
| 3 | **Custos** diretos/indiretos + sistema de rateio | ⏳ próximo |
| 4 | **DRE**, ponto de equilíbrio e **custo por aluno** | ⏳ |
| 5 | **Saídas**: PDF (modelo do PowerPoint) e `.docx` editável | ⏳ |
| 6 | **Publicação**: login, banco de dados, multi-escola, hospedagem segura | ⏳ |

## Pontos a confirmar com o cliente

- **Regime tributário** das escolas (Simples Nacional × Lucro Presumido/Real).
  Isso muda a alíquota de **encargos** da folha (principalmente o INSS
  patronal). Hoje o sistema usa alíquotas configuráveis com um padrão
  conservador; basta ajustar por escola.
- Critério de **rateio** dos custos administrativos e indiretos por nível
  (por nº de alunos, por receita, por área, etc.) — será definido no módulo 3.
