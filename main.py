import sys
from loguru import logger

from cli.main import app as cli_app
from gui.main import run_gui
from utils.logger import setup_logger

def main() -> None:
    """Глобальная точка входа в приложение."""
    # Инициализация подсистемы логирования до запуска любых компонентов
    setup_logger()
    logger.info("=== Запуск Project Aggregator ===")

    try:
        if len(sys.argv) > 1:
            logger.info("Обнаружены аргументы командной строки. Инициализация режима CLI (Typer).")
            cli_app()
        else:
            logger.info("Аргументы не обнаружены. Инициализация режима GUI (PySide6).")
            run_gui()
    except Exception as e:
        logger.critical(f"Критический сбой на уровне глобального маршрутизатора: {e}")
        sys.exit(1)
    finally:
        logger.info("=== Завершение работы Project Aggregator ===\n")

if __name__ == "__main__":
    main()