# Diagnóstico Econômico/Financeiro — Escolas

Transforma o diagnóstico financeiro (hoje feito numa planilha Excel + relatório
manual) em um fluxo automatizado:

```
Escola preenche o formulário  →  Motor de cálculo (a sua lógica)  →  Relatório/painel
```

Este é o **primeiro módulo: Receitas** (alunos + mensalidades + descontos +
inadimplência + outras receitas). Ele já funciona de ponta a ponta e serve de
modelo para os próximos módulos (Folha de Pagamento, Custos, DRE, etc.).

## Estrutura

```
diagnostico-financeiro/
├── engine/          # Motor de cálculo (a lógica da planilha em código)
│   └── receitas.py
├── api/             # Servidor web (FastAPI) que recebe os dados e calcula
│   └── main.py
├── web/             # Formulário + painel de resultados (a "LP")
│   └── index.html
├── data/            # Dados de exemplo (a "Escola Modelo" da planilha)
│   └── escola_modelo.json
└── tests/           # Validação: confere os números contra a planilha Ágora
    └── test_receitas.py
```

## Como rodar

```bash
cd diagnostico-financeiro
pip install -r requirements.txt
uvicorn api.main:app --reload
```

Abra http://127.0.0.1:8000 no navegador. Clique em **"Preencher com a Escola
Modelo"** para ver o painel com os dados reais da planilha, ou preencha os
campos de uma escola nova.

## Validação contra a planilha

O motor foi conferido número a número com a "Escola Modelo" das abas
`RECEITAS` / `DRE` da planilha Ágora:

| Indicador (mensal)              | Planilha       | Sistema        |
|---------------------------------|----------------|----------------|
| Receita bruta de mensalidades   | R$ 819.094,00  | R$ 819.092,68  |
| (−) Descontos                   | R$  89.241,17  | R$  89.240,66  |
| (=) Receita líquida mensalidade | R$ 729.852,83  | R$ 729.852,02  |
| (+) Outras receitas             | R$ 112.202,97  | R$ 112.202,97  |
| (=) Receita líquida total       | R$ 842.055,80  | R$ 842.054,99  |
| Ticket médio                    | R$   1.192,28  | R$   1.192,27  |

(As diferenças de centavos vêm do arredondamento da mensalidade média.)

Rodar os testes:

```bash
cd diagnostico-financeiro
python -m unittest discover -s tests -v
```

## Módulos prontos

- **Receitas** (`engine/receitas.py`) — alunos, mensalidades, descontos, outras receitas.
- **Folha de pagamento** (`engine/folha.py`) — docentes, coordenação e
  administrativos, com **alocação por nível de ensino** e **encargos
  configuráveis** (FGTS, 13º, férias + 1/3 e INSS patronal conforme o regime
  tributário). Endpoint: `POST /api/folha`.

> Observação sobre a folha: a planilha original distribui o pessoal em vários
> blocos (registrados, sem registro, extra-curriculares). O módulo reproduz
> exatamente os colaboradores informados; o arquivo de exemplo
> (`data/escola_modelo_folha.json`) usa o quadro de pessoal registrado extraído
> da planilha.

- **Regime tributário** (`engine/tributos.py`) — a escola escolhe o regime e
  todos os cálculos passam a respeitar essa escolha:
  - **Simples Nacional (Anexo III, ensino)** — alíquota efetiva sobre a
    receita, com o DAS aberto em IRPJ, CSLL, PIS, COFINS, **INSS patronal
    (CPP)** e ISS. Como o CPP já está no DAS, **não há INSS patronal sobre a
    folha**.
  - **Lucro Presumido** — presunção de 32%; IRPJ 15% (+10% adicional),
    CSLL 9%, PIS 0,65%, COFINS 3%, ISS municipal; **INSS patronal ≈ 28,8%**
    sobre a folha.
  - **Lucro Real** — IRPJ/CSLL sobre o lucro; PIS 1,65% e COFINS 7,6%; ISS;
    INSS patronal sobre a folha.
  - Endpoints: `POST /api/tributos`; e o `POST /api/folha` aceita o campo
    `regime`, que define automaticamente o INSS patronal da folha.
  - **Botão de regime** (interface): `web/Regime-Tributario.html` — página
    autônoma onde a escola clica no regime e vê o impacto na hora.

## Próximos passos (roadmap)

Ver **[PLANEJAMENTO.md](PLANEJAMENTO.md)** para o roteiro completo e as decisões
de produto (acesso multi-escola, LGPD, hospedagem).

1. **Receitas** — ✅ concluído
2. **Folha de pagamento** — ✅ motor + testes
3. **Custos diretos e indiretos** + sistema de rateio — ⏳ próximo
4. **DRE, ponto de equilíbrio e custo por aluno**
5. **Saídas**: PDF (modelo do PowerPoint) e documento `.docx` editável
6. **Publicação**: login, multi-escola e hospedagem segura
