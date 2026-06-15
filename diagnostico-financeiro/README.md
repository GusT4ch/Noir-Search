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

## Próximos passos (roadmap)

1. **Receitas** — ✅ concluído (este módulo)
2. **Folha de pagamento** — docentes/coordenação/administrativo, com alocação por nível
3. **Custos diretos e indiretos** + sistema de rateio
4. **DRE, ponto de equilíbrio e custo por aluno**
5. **Saídas**: PDF (modelo do PowerPoint), painel completo e documento `.docx` editável
6. **Publicação**: link por escola e histórico
