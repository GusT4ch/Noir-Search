from __future__ import annotations

import argparse
import json
import logging
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import random  # Certifique-se que já tem este import

def randomizar_queries(queries: list[str]) -> list[str]:
    """Embaralha a ordem das pesquisas para parecer mais humano."""
    shuffled = queries.copy()
    random.shuffle(shuffled)
    return shuffled


def deduplicate_queries(raw_queries: Sequence[str]) -> list[str]:
    """Remove comentarios, itens vazios e duplicatas da lista local."""
    queries: list[str] = []
    seen: set[str] = set()

    for raw_query in raw_queries:
        query = " ".join(raw_query.strip().split())
        if not query or query.startswith("#"):
            continue

        query_key = query.casefold()
        if query_key in seen:
            continue

        seen.add(query_key)
        queries.append(query)

    return queries


def refresh_local_queries_file(queries_file: Path) -> list[str]:
    """Atualiza o arquivo local com buscas unicas e ordem embaralhada."""
    if not queries_file.exists():
        raise FileNotFoundError(f"Arquivo de consultas nao encontrado: {queries_file}")

    queries = deduplicate_queries(queries_file.read_text(encoding="utf-8").splitlines())
    if not queries:
        raise ValueError("O arquivo de consultas nao contem itens validos.")

    refreshed_queries = randomizar_queries(queries)
    queries_file.write_text("\n".join(refreshed_queries) + "\n", encoding="utf-8")
    return refreshed_queries

DEFAULT_START_URL = "https://www.bing.com"
DEFAULT_DELAY_SECONDS = 8.0  # ALTERADO: 8 segundos para Microsoft Rewards
DEFAULT_KEEP_OPEN_SECONDS = 5.0
DEFAULT_TIMEOUT_SECONDS = 20  # ALTERADO: 20 segundos para carregar
DEFAULT_LOG_RELATIVE_PATH = Path("logs") / "noir_search.log"
LOGGER_NAME = "noir_search"

# Lista padrão com 40 pesquisas variadas
DEFAULT_QUERIES = [
    "clima em Sao Paulo hoje",
    "noticias do Brasil",
    "receita de bolo de chocolate",
    "como limpar o quarto",
    "significado da palavra resiliencia",
    "filmes em cartaz 2025",
    "previsao do tempo amanha",
    "cotacao dolar hoje",
    "receita de pao caseiro",
    "como aprender ingles rapido",
    "melhores series netflix",
    "como investir na bolsa",
    "significado de empatia",
    "jogos para pc gratis",
    "como fazer jejum intermitente",
    "musicas mais tocadas 2025",
    "receita de lasanha simples",
    "como plantar morango",
    "noticias de tecnologia",
    "como perder barriga rapido",
    "significado de gratidao",
    "melhores destinos para viajar",
    "como fazer um currículo",
    "receita de sorvete caseiro",
    "como cuidar da pele",
    "jogos de ps5 lancamentos",
    "como ganhar dinheiro na internet",
    "significado de amor proprio",
    "receita de pudim de leite",
    "como fazer abdominal corretamente",
    "melhores livros para ler",
    "como decorar para prova",
    "receita de bolo de cenoura",
    "como passar no enem",
    "significado de liberdade",
    "como viajar com pouco dinheiro",
    "receita de strogonoff de frango",
    "como fazer alongamento",
    "melhores aplicativos de produtividade",
    "como organizar o armario",
]

ProgressCallback = Callable[[int, int, str, str], None]
StopCallback = Callable[[], bool]


@dataclass(frozen=True)
class AppConfig:
    config_file: Path | None
    queries_file: Path | None
    delay_seconds: float
    keep_open_seconds: float
    timeout_seconds: int
    start_url: str
    headless: bool
    dry_run: bool
    log_file: Path


@dataclass(frozen=True)
class RunSummary:
    successes: int
    failures: int
    total_queries: int
    duration_seconds: float
    cancelled: bool = False
    dry_run: bool = False


class AutomationCancelled(Exception):
    def __init__(self, successes: int, failures: int):
        super().__init__("Execucao interrompida.")
        self.successes = successes
        self.failures = failures


# ============================================================
# FUNÇÕES DE COMPORTAMENTO HUMANO (NOVAS)
# ============================================================

def human_type(element, text: str, delay_range: tuple[float, float] = (0.05, 0.15)):
    """Digita como um humano, com pausas aleatórias entre letras."""
    element.clear()
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(*delay_range))


def human_scroll(driver: WebDriver, min_scrolls: int = 1, max_scrolls: int = 3):
    """Rola a página de forma humana e aleatória."""
    scrolls = random.randint(min_scrolls, max_scrolls)
    for _ in range(scrolls):
        scroll_amount = random.randint(200, 500)
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        time.sleep(random.uniform(0.3, 0.8))


def random_micro_pause(min_sec: float = 0.1, max_sec: float = 0.5):
    """Pausa micro-aleatória entre ações."""
    time.sleep(random.uniform(min_sec, max_sec))


# ============================================================
# FUNÇÕES ORIGINAIS (MANTIDAS E ATUALIZADAS)
# ============================================================

def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Noir Search executa uma sequencia de buscas no Bing para Microsoft Rewards. "
            "Otimizado para 40 pesquisas com intervalo de 8 segundos."
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Arquivo JSON de configuracao. Se omitido, usa config.json ao lado do script quando existir.",
    )
    parser.add_argument(
        "--queries-file",
        type=Path,
        default=None,
        help="Arquivo UTF-8 com uma busca por linha. Linhas vazias e com # sao ignoradas.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=None,
        help=f"Intervalo entre buscas em segundos. Padrao: {DEFAULT_DELAY_SECONDS}.",
    )
    parser.add_argument(
        "--keep-open",
        type=float,
        default=None,
        help=(
            "Tempo em segundos para manter o navegador aberto ao final da execucao. "
            f"Padrao: {DEFAULT_KEEP_OPEN_SECONDS}."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help=f"Tempo maximo de espera por elementos da pagina. Padrao: {DEFAULT_TIMEOUT_SECONDS}.",
    )
    parser.add_argument(
        "--start-url",
        default=None,
        help=f"URL inicial da automacao. Padrao: {DEFAULT_START_URL}.",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=None,
        help="Arquivo de log. Padrao: logs/noir_search.log.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Valida a configuracao e mostra as buscas sem abrir o navegador.",
    )

    headless_group = parser.add_mutually_exclusive_group()
    headless_group.add_argument(
        "--headless",
        dest="headless",
        action="store_true",
        help="Executa o navegador em segundo plano.",
    )
    headless_group.add_argument(
        "--show-browser",
        dest="headless",
        action="store_false",
        help="Forca a exibicao do navegador, mesmo se o config.json definir headless.",
    )
    parser.set_defaults(headless=None)
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    return create_parser().parse_args(argv)


def resolve_resource_base_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent


def resolve_runtime_base_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def load_json_config(config_file: Path | None) -> dict[str, Any]:
    if config_file is None:
        return {}

    if not config_file.exists():
        raise FileNotFoundError(f"Arquivo de configuracao nao encontrado: {config_file}")

    try:
        data = json.loads(config_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON invalido em {config_file}: {exc.msg}") from exc

    if not isinstance(data, dict):
        raise ValueError("O arquivo de configuracao precisa conter um objeto JSON na raiz.")

    return data


def resolve_cli_path(path_value: Path | None) -> Path | None:
    if path_value is None:
        return None
    if path_value.is_absolute():
        return path_value
    return (Path.cwd() / path_value).resolve()


def resolve_config_path(path_value: str | Path | None, base_path: Path) -> Path | None:
    if path_value is None:
        return None

    path = Path(path_value)
    if path.is_absolute():
        return path
    return (base_path / path).resolve()


def create_app_config(
    *,
    config_file: Path | None,
    queries_file: Path | None,
    delay_seconds: float,
    keep_open_seconds: float,
    timeout_seconds: int,
    start_url: str,
    headless: bool,
    dry_run: bool,
    log_file: Path,
) -> AppConfig:
    if delay_seconds < 0:
        raise ValueError("delay_seconds precisa ser maior ou igual a zero.")
    if keep_open_seconds < 0:
        raise ValueError("keep_open_seconds precisa ser maior ou igual a zero.")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds precisa ser maior que zero.")
    if not start_url.startswith(("http://", "https://")):
        raise ValueError("start_url precisa comecar com http:// ou https://.")

    return AppConfig(
        config_file=config_file,
        queries_file=queries_file,
        delay_seconds=float(delay_seconds),
        keep_open_seconds=float(keep_open_seconds),
        timeout_seconds=int(timeout_seconds),
        start_url=start_url,
        headless=bool(headless),
        dry_run=bool(dry_run),
        log_file=log_file,
    )


def build_config(
    args: argparse.Namespace,
    runtime_base_path: Path,
    resource_base_path: Path,
) -> AppConfig:
    config_file = resolve_cli_path(args.config)
    if config_file is None:
        default_config_file = runtime_base_path / "config.json"
        if default_config_file.exists():
            config_file = default_config_file

    file_settings = load_json_config(config_file)
    config_base_path = config_file.parent if config_file else runtime_base_path

    cli_queries_file = resolve_cli_path(args.queries_file)
    config_queries_file = resolve_config_path(file_settings.get("queries_file"), config_base_path)
    runtime_queries_file = runtime_base_path / "queries.txt"
    resource_queries_file = resource_base_path / "queries.txt"

    queries_file = cli_queries_file or config_queries_file
    if queries_file is None:
        if runtime_queries_file.exists():
            queries_file = runtime_queries_file
        elif resource_queries_file.exists():
            queries_file = resource_queries_file

    cli_log_file = resolve_cli_path(args.log_file)
    config_log_file = resolve_config_path(file_settings.get("log_file"), config_base_path)
    log_file = cli_log_file or config_log_file or (runtime_base_path / DEFAULT_LOG_RELATIVE_PATH)

    delay_seconds = args.delay
    if delay_seconds is None:
        delay_seconds = float(file_settings.get("delay_seconds", DEFAULT_DELAY_SECONDS))

    keep_open_seconds = args.keep_open
    if keep_open_seconds is None:
        keep_open_seconds = float(
            file_settings.get("keep_open_seconds", DEFAULT_KEEP_OPEN_SECONDS)
        )

    timeout_seconds = args.timeout
    if timeout_seconds is None:
        timeout_seconds = int(file_settings.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS))

    start_url = args.start_url or str(file_settings.get("start_url", DEFAULT_START_URL))

    if args.headless is None:
        headless = bool(file_settings.get("headless", False))
    else:
        headless = args.headless

    return create_app_config(
        config_file=config_file,
        queries_file=queries_file,
        delay_seconds=delay_seconds,
        keep_open_seconds=keep_open_seconds,
        timeout_seconds=timeout_seconds,
        start_url=start_url,
        headless=headless,
        dry_run=args.dry_run,
        log_file=log_file,
    )


def load_queries(queries_file: Path | None) -> list[str]:
    if not queries_file:
        queries = deduplicate_queries(DEFAULT_QUERIES)
    else:
        if not queries_file.exists():
            raise FileNotFoundError(f"Arquivo de consultas nao encontrado: {queries_file}")

        queries = deduplicate_queries(queries_file.read_text(encoding="utf-8").splitlines())

        if not queries:
            raise ValueError("O arquivo de consultas nao contem itens validos.")
    
    # ALEATORIZA A ORDEM DAS PESQUISAS
    random.shuffle(queries)
    
    return queries


def setup_logging(
    log_file: Path,
    *,
    include_console: bool = True,
    extra_handlers: Sequence[logging.Handler] | None = None,
) -> logging.Logger:
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    if include_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(console_handler)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    )
    logger.addHandler(file_handler)

    for handler in extra_handlers or []:
        logger.addHandler(handler)

    return logger


def build_driver(base_path: Path, headless: bool, logger: logging.Logger) -> WebDriver:
    options = Options()
    options.add_argument("--log-level=3")
    
    # Adiciona argumentos para evitar detecção
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1280,900")
    else:
        options.add_argument("--window-size=1366,768")  # Tamanho comum de notebook

    bundled_driver = base_path / "edgedriver_win64" / "msedgedriver.exe"
    if bundled_driver.exists():
        logger.info("Usando driver local em %s", bundled_driver)
        service = Service(executable_path=str(bundled_driver))
        driver = webdriver.Edge(service=service, options=options)
    else:
        logger.info(
            "Driver local nao encontrado. "
            "Tentando iniciar o Edge com a configuracao padrao do Selenium..."
        )
        driver = webdriver.Edge(options=options)
    
    # Remove o webdriver property para evitar detecção
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


def wait_for_search_box(driver: WebDriver, timeout_seconds: int):
    return WebDriverWait(driver, timeout_seconds).until(
        EC.element_to_be_clickable((By.NAME, "q"))
    )


def abort_if_requested(
    should_stop: StopCallback | None,
    successes: int,
    failures: int,
) -> None:
    if should_stop and should_stop():
        raise AutomationCancelled(successes, failures)


def sleep_with_cancel(
    seconds: float,
    should_stop: StopCallback | None,
    successes: int,
    failures: int,
) -> None:
    deadline = time.monotonic() + seconds
    while True:
        abort_if_requested(should_stop, successes, failures)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return
        time.sleep(min(0.1, remaining))


def run_searches(
    driver: WebDriver,
    queries: list[str],
    config: AppConfig,
    logger: logging.Logger,
    *,
    progress_callback: ProgressCallback | None = None,
    should_stop: StopCallback | None = None,
) -> tuple[int, int]:
    successes = 0
    failures = 0

    abort_if_requested(should_stop, successes, failures)
    driver.get(config.start_url)
    wait_for_search_box(driver, config.timeout_seconds)
    
    # Delay inicial aleatório (simula "pensando")
    time.sleep(random.uniform(1.0, 2.5))

    total_queries = len(queries)
    for index, query in enumerate(queries, start=1):
        abort_if_requested(should_stop, successes, failures)
        try:
            search_box = wait_for_search_box(driver, config.timeout_seconds)
            
            # Limpa o campo de busca de forma humana
            search_box.send_keys(Keys.CONTROL, "a")
            random_micro_pause(0.05, 0.15)
            search_box.send_keys(Keys.DELETE)
            random_micro_pause(0.1, 0.3)
            
            # Digita como humano
            human_type(search_box, query)
            random_micro_pause(0.3, 0.8)
            
            # Pressiona Enter
            search_box.send_keys(Keys.ENTER)
            
            # Após a pesquisa, rola a página como humano
            random_micro_pause(0.5, 1.0)
            human_scroll(driver, 1, 2)
            
            successes += 1
            logger.info("[%s/%s] Pesquisando: %s", index, total_queries, query)
            if progress_callback:
                progress_callback(index, total_queries, query, "success")
                
            # Aguarda o intervalo configurado com pequena variação (+/- 0.5s)
            actual_delay = config.delay_seconds + random.uniform(-0.5, 0.5)
            actual_delay = max(0.5, actual_delay)  # nunca menos que 0.5s
            sleep_with_cancel(actual_delay, should_stop, successes, failures)
            
        except TimeoutException:
            failures += 1
            logger.warning("[%s/%s] Tempo esgotado ao pesquisar: %s", index, total_queries, query)
            if progress_callback:
                progress_callback(index, total_queries, query, "timeout")
            time.sleep(2.0)
        except WebDriverException as exc:
            failures += 1
            logger.warning(
                "[%s/%s] Falha ao pesquisar '%s': %s",
                index,
                total_queries,
                query,
                exc,
            )
            if progress_callback:
                progress_callback(index, total_queries, query, "error")
            time.sleep(2.0)

    return successes, failures


def print_summary(summary: RunSummary, logger: logging.Logger) -> None:
    minutes, seconds = divmod(int(summary.duration_seconds), 60)
    logger.info("")
    logger.info("=" * 50)
    logger.info("RESUMO DA EXECUCAO")
    logger.info("=" * 50)
    logger.info("Buscas concluidas com sucesso: %s", summary.successes)
    logger.info("Falhas: %s", summary.failures)
    logger.info("Total de buscas: %s", summary.total_queries)
    logger.info("Tempo total: %s minuto(s) e %s segundo(s).", minutes, seconds)
    if summary.cancelled:
        logger.info("Status: INTERROMPIDO pelo usuario")
    else:
        logger.info("Status: FINALIZADO")
        if summary.successes >= 30:
            logger.info("Pontos do Microsoft Rewards devem ter sido contabilizados.")
        else:
            logger.warning("Menos de 30 buscas. Pode nao ter contado todos os pontos.")
    logger.info("=" * 50)


def preview_queries(
    queries: list[str],
    config: AppConfig,
    logger: logging.Logger,
    *,
    progress_callback: ProgressCallback | None = None,
) -> None:
    logger.info("=" * 50)
    logger.info("MODO DRY-RUN - Nenhum navegador sera aberto")
    logger.info("=" * 50)
    logger.info("URL inicial: %s", config.start_url)
    logger.info("Headless: %s", "sim" if config.headless else "nao")
    logger.info("Arquivo de consultas: %s", config.queries_file or "lista interna")
    logger.info("Intervalo entre buscas: %.1f segundo(s)", config.delay_seconds)
    logger.info("Numero de buscas: %s", len(queries))
    logger.info("")
    logger.info("LISTA DE BUSCAS:")
    logger.info("-" * 30)
    total_queries = len(queries)
    for index, query in enumerate(queries, start=1):
        logger.info("[%s/%s] %s", index, total_queries, query)
        if progress_callback:
            progress_callback(index, total_queries, query, "preview")


def execute_automation(
    config: AppConfig,
    *,
    resource_base_path: Path,
    logger: logging.Logger,
    progress_callback: ProgressCallback | None = None,
    should_stop: StopCallback | None = None,
) -> RunSummary:
    queries = load_queries(config.queries_file)
    total_queries = len(queries)
    start_time = time.time()

    if config.dry_run:
        preview_queries(
            queries,
            config,
            logger,
            progress_callback=progress_callback,
        )
        return RunSummary(
            successes=0,
            failures=0,
            total_queries=total_queries,
            duration_seconds=time.time() - start_time,
            dry_run=True,
        )

    driver: WebDriver | None = None
    try:
        driver = build_driver(resource_base_path, config.headless, logger)
        logger.info("=" * 50)
        logger.info("INICIANDO AUTOMACAO DE PESQUISAS")
        logger.info(f"Total de buscas: {total_queries}")
        logger.info(f"Intervalo entre buscas: {config.delay_seconds} segundos")
        logger.info("=" * 50)
        
        successes, failures = run_searches(
            driver,
            queries,
            config,
            logger,
            progress_callback=progress_callback,
            should_stop=should_stop,
        )
        summary = RunSummary(
            successes=successes,
            failures=failures,
            total_queries=total_queries,
            duration_seconds=time.time() - start_time,
        )
        print_summary(summary, logger)

        if config.keep_open_seconds:
            logger.info("")
            logger.info(
                "Mantendo o navegador aberto por %.1f segundo(s)...",
                config.keep_open_seconds,
            )
            sleep_with_cancel(
                config.keep_open_seconds,
                should_stop,
                successes,
                failures,
            )
        return summary
    except AutomationCancelled as exc:
        summary = RunSummary(
            successes=exc.successes,
            failures=exc.failures,
            total_queries=total_queries,
            duration_seconds=time.time() - start_time,
            cancelled=True,
        )
        logger.warning("")
        logger.warning("Execucao interrompida pelo usuario.")
        print_summary(summary, logger)
        return summary
    finally:
        if driver is not None:
            driver.quit()


def main(argv: Sequence[str] | None = None) -> int:
    resource_base_path = resolve_resource_base_path()
    runtime_base_path = resolve_runtime_base_path()

    try:
        args = parse_args(argv)
        config = build_config(args, runtime_base_path, resource_base_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Erro de configuracao: {exc}")
        return 1

    logger = setup_logging(config.log_file)
    logger.info("Log ativo em %s", config.log_file)
    if config.config_file:
        logger.info("Configuracao carregada de %s", config.config_file)

    try:
        summary = execute_automation(
            config,
            resource_base_path=resource_base_path,
            logger=logger,
        )
    except (FileNotFoundError, ValueError) as exc:
        logger.error("Erro de configuracao: %s", exc)
        return 1
    except WebDriverException as exc:
        logger.error("Erro ao iniciar o navegador: %s", exc)
        return 1
    except KeyboardInterrupt:
        logger.warning("Execucao interrompida pelo usuario.")
        return 130

    if summary.cancelled:
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
