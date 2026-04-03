# Noir Search Studio

Projeto desktop em Python para automatizar pesquisas no Bing com interface grafica, configuracao externa e logs.

## O que faz

- Executa sequencias de buscas usando Selenium e Microsoft Edge
- Carrega consultas a partir de `queries.txt`
- Embaralha e organiza a lista local antes da execucao
- Oferece interface desktop para iniciar, validar e acompanhar a automacao
- Gera logs para facilitar diagnostico

## Arquivos principais

- `noir_search.py`: nucleo da automacao
- `noir_search_gui.py`: interface desktop
- `queries.txt`: lista local de pesquisas
- `config.example.json`: exemplo de configuracao
- `build.ps1`: gera os executaveis

## Como executar

Interface:

```bash
python noir_search_gui.py
```

CLI:

```bash
python noir_search.py
```

Dry run:

```bash
python noir_search.py --dry-run
```

## Testes

```bash
python -m unittest discover -s tests -v
```

## Build

```powershell
.\build.ps1 -Target Both
```
