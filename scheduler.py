"""
Agendador para rodar o Noir Search diariamente.
Uso: python scheduler.py

O robô executará automaticamente todos os dias no horário definido.
"""

import schedule
import time
import subprocess
import logging
from datetime import datetime
import os
import sys

# Configuração do sistema de logs
LOG_FILE = "scheduler.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

def run_noir_search():
    """Executa o script de automação do Bing."""
    logging.info("=" * 50)
    logging.info(f"Iniciando execução agendada em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    logging.info("=" * 50)
    
    try:
        # Executa o script principal
        result = subprocess.run(
            [sys.executable, "noir_search.py"],
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutos máximo
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.returncode == 0:
            logging.info("Execução concluída com sucesso.")
            logging.info(result.stdout[-500:])  # Últimas 500 linhas
        else:
            logging.error(f"Erro na execução. Código: {result.returncode}")
            logging.error(f"Erro: {result.stderr[-500:]}")
            
    except subprocess.TimeoutExpired:
        logging.error("Execução excedeu o tempo limite de 10 minutos")
    except FileNotFoundError:
        logging.error("Arquivo noir_search.py não encontrado na pasta atual")
    except Exception as e:
        logging.error(f"Erro inesperado: {e}")

def mostrar_proximo_horario():
    """Mostra o próximo horário agendado."""
    next_run = schedule.next_run()
    if next_run:
        logging.info(f"Próxima execução: {next_run.strftime('%d/%m/%Y às %H:%M:%S')}")

# ============================================================
# CONFIGURAÇÃO DO HORÁRIO - ALTERE AQUI!
# ============================================================

# Exemplo: rodar todos os dias às 08:00 da manhã
HORARIO_EXECUCAO = "08:00"

# Outras opções (descomente a que você quiser):
# HORARIO_EXECUCAO = "13:00"  # 13:00 (1 da tarde)
# HORARIO_EXECUCAO = "18:30"  # 18:30 (6:30 da tarde)
# HORARIO_EXECUCAO = "23:00"  # 23:00 (11 da noite)

# Agenda a execução diária
schedule.every().day.at(HORARIO_EXECUCAO).do(run_noir_search)

logging.info("=" * 50)
logging.info("NOIR SEARCH - AGENDADOR")
logging.info("=" * 50)
logging.info(f"Horário agendado: Todos os dias às {HORARIO_EXECUCAO}")
logging.info(f"Pasta de trabalho: {os.path.dirname(os.path.abspath(__file__))}")
logging.info(f"Log do agendador: {LOG_FILE}")
logging.info("Agendador iniciado. Pressione CTRL+C para parar.")
logging.info("")

mostrar_proximo_horario()

# Loop principal
try:
    while True:
        schedule.run_pending()
        time.sleep(60)  # Verifica a cada minuto
except KeyboardInterrupt:
    logging.info("")
    logging.info("Agendador interrompido pelo usuário.")
    logging.info("Até mais!")
