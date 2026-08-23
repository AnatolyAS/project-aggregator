import sys
from pathlib import Path
from loguru import logger

def setup_logger() -> None:
    """Инициализирует и настраивает глобальный логгер приложения.
    
    Обеспечивает запись всех событий (от уровня DEBUG до CRITICAL) 
    в ротируемый файл логов с подробной трассировкой вызовов.
    Терминальный вывод (stdout) отключен, чтобы не конфликтовать с 
    пользовательскими интерфейсами Rich и PySide6.
    """
    # 1. Отключаем стандартный вывод в консоль
    logger.remove()

    # 2. Создаем директорию для логов (Git её игнорирует, если она не в исключениях, 
    # но лучше создать её на уровне пользователя)
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "app.log"

    # 3. Настраиваем файловый обработчик
    logger.add(
        str(log_file),
        rotation="5 MB",           # Ротация: новый файл каждые 5 МБ
        retention="10 days",       # Хранение: удалять файлы старше 10 дней
        level="DEBUG",             # Максимальный охват событий
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        enqueue=True,              # Потокобезопасность
        encoding="utf-8",
        backtrace=True,            # Полная трассировка исключений
        diagnose=True              # Детальная диагностика переменных при сбоях
    )
    
    logger.debug("Логгер успешно инициализирован.")