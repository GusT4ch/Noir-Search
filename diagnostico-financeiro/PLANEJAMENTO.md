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
| 2b | **Regime tributário** (Simples / Presumido / Real) com botão de escolha | ✅ motor + testes + tela do botão |
| 3 | **Custos** diretos/indiretos + sistema de rateio | ✅ motor + testes (reproduz o DRE da planilha) |
| 4 | **DRE**, ponto de equilíbrio e **custo por aluno** | ✅ incluído no módulo de Custos/DRE |
| 4b | **Análise SWOT interativa** (bolinha que se move pelos quadrantes) | ✅ motor + testes + tela interativa |
| 5 | **Saídas**: relatório em `.docx`, `.pptx` (PowerPoint) e `.pdf` | ✅ consolidador + geradores + testes |
| 6 | **Publicação**: login, banco de dados, multi-escola | ✅ backend (auth + multi-escola + BD) + testes + tela de login |
| 6b | **Hospedagem**: subir em servidor (São Paulo/PostgreSQL) | ⏳ quando você decidir publicar |

## Pontos a confirmar com o cliente

- **Regime tributário** das escolas — ✅ resolvido: a própria escola escolhe
  (Simples / Presumido / Real) e os cálculos se ajustam, inclusive o INSS
  patronal da folha (zero no Simples, pois o CPP já está no DAS). A alíquota
  de **ISS** (municipal, 2%–5%) e o **RAT** continuam ajustáveis por escola.
- Critério de **rateio** dos custos administrativos e indiretos por nível
  (por nº de alunos, por receita, por área, etc.) — será definido no módulo 3.
