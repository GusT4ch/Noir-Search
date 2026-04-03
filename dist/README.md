# Bing Automation Studio

Projeto desktop em Python para demonstrar automacao de navegador com Selenium e Microsoft Edge.

O foco agora e educacional: abrir o Bing, executar buscas de exemplo e oferecer uma base mais organizada, com interface grafica, logs e configuracao externa.

## Melhorias aplicadas

- Script refatorado em funcoes pequenas e reutilizaveis
- Tratamento de erro para configuracao, inicializacao do navegador e timeout
- Interface desktop com visual mais caprichado e painel de logs ao vivo
- Parametros de linha de comando para controlar arquivo de consultas e intervalos
- Suporte a `config.json` e modo `--dry-run`
- Logs em arquivo para facilitar diagnostico
- `queries.txt` separado do codigo para facilitar manutencao
- Testes unitarios para as funcoes principais de configuracao
- `build.ps1` pronto para gerar `.exe` da interface grafica e da CLI
- `requirements.txt` e `.gitignore` adicionados
- README reescrito em UTF-8 legivel

## Requisitos

- Python 3.10+
- Microsoft Edge instalado
- `msedgedriver.exe` opcional em `edgedriver_win64/`

Se o driver empacotado nao existir, o Selenium tentara iniciar o Edge com a configuracao padrao do ambiente.

## Instalacao

```bash
pip install -r requirements.txt
```

Para empacotar em `.exe` depois:

```bash
pip install -r requirements-dev.txt
```

## Como executar

Abrindo a interface desktop:

```bash
python bing_automation_gui.py
```

Usando a CLI com a lista padrao de buscas:

```bash
python bing_automation.py
```

Usando um arquivo proprio:

```bash
python bing_automation.py --queries-file queries.txt --delay 3 --keep-open 5
```

Validando a configuracao sem abrir o navegador:

```bash
python bing_automation.py --dry-run
```

Executando em segundo plano:

```bash
python bing_automation.py --headless
```

## Configuracao por JSON

O projeto pode carregar automaticamente um `config.json` ao lado do script.
Ha um exemplo pronto em `config.example.json`.

Exemplo:

```json
{
  "queries_file": "queries.txt",
  "delay_seconds": 3.0,
  "keep_open_seconds": 5.0,
  "timeout_seconds": 15,
  "start_url": "https://www.bing.com",
  "headless": false,
  "log_file": "logs/bing_automation.log"
}
```

Argumentos de linha de comando continuam tendo prioridade sobre o JSON.

## Formato do arquivo de consultas

O arquivo deve estar em UTF-8 e conter uma consulta por linha:

```text
# comentario
Python automacao com Selenium
Como funciona o Edge
```

## Estrutura

```text
.
|-- bing_automation.py
|-- bing_automation_gui.py
|-- build.ps1
|-- config.example.json
|-- queries.txt
|-- requirements.txt
|-- requirements-dev.txt
|-- tests/
|-- edgedriver_win64/
`-- imgs/
```

## Testes

```bash
python -m unittest discover -s tests -v
```

## Preparacao para .exe

Gerando o `.exe` da interface grafica:

```powershell
.\build.ps1
```

Gerando tambem a versao de linha de comando:

```powershell
.\build.ps1 -Target Both
```

Arquivos esperados em `dist/`:

- `bing_automation.exe` para a interface grafica
- `bing_automation_cli.exe` para a versao por terminal
- `config.example.json` e `queries.txt` como arquivos de apoio

## Observacao importante

Use este repositorio apenas para aprendizado de automacao de navegador e testes locais. Ele nao foi projetado para burlar politicas, automatizar sistemas de recompensa ou simular atividade artificial em servicos de terceiros.
