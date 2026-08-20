import typer
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.theme import Theme

from core.aggregator import FileAggregator, ConsolidationMethod

# Настройка эстетичной цветовой схемы для терминала
custom_theme = Theme({
    "info": "cyan",
    "success": "bold green",
    "warning": "yellow",
    "error": "bold red"
})

console = Console(theme=custom_theme)

app = typer.Typer(
    name="Project Aggregator CLI",
    help="Профессиональная утилита для консолидации файлов проекта.",
    add_completion=False,
)


@app.command()
def aggregate(
    target_dir: Path = typer.Argument(
        ...,
        help="Абсолютный или относительный путь к директории проекта для агрегации.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    output_file: Path = typer.Option(
        Path("aggregated_output.md"),
        "--output",
        "-o",
        help="Путь к результирующему файлу, в который будут сохранены данные.",
        writable=True,
    ),
    method: ConsolidationMethod = typer.Option(
        ConsolidationMethod.MARKDOWN,
        "--method",
        "-m",
        help="Метод форматирования выходных данных (markdown, plain_text, json).",
    ),
    ignore: Optional[List[str]] = typer.Option(
        None,
        "--ignore",
        "-i",
        help="Дополнительные имена директорий для исключения из обхода.",
    )
) -> None:
    """Выполняет процесс агрегации файлов с визуальным сопровождением.

    Команда собирает текстовые файлы из указанной директории, форматирует их
    выбранным методом и сохраняет результат в выходной файл. Процесс сопровождается
    анимированным спиннером и информационными панелями в терминале.

    Args:
        target_dir (Path): Путь к целевой директории. Проверяется Typer на существование.
        output_file (Path): Путь для сохранения результата. По умолчанию 'aggregated_output.md'.
        method (ConsolidationMethod): Формат агрегации. По умолчанию MARKDOWN.
        ignore (Optional[List[str]]): Дополнительные директории для игнорирования.

    Raises:
        typer.Exit: В случае возникновения критической ошибки при чтении или записи.
    """
    # Приветственная панель
    welcome_panel = Panel(
        f"[bold]Project Aggregator[/bold]\n"
        f"Целевая директория: [info]{target_dir}[/info]\n"
        f"Метод: [info]{method.value}[/info]",
        border_style="cyan",
        expand=False
    )
    console.print(welcome_panel)

    # Подготовка пользовательских исключений, если они переданы
    ignore_dirs = set(ignore) if ignore else None

    # Инициализация ядра с обработкой возможных ошибок
    try:
        aggregator = FileAggregator(
            target_dir=target_dir,
            method=method,
            ignore_dirs=ignore_dirs
        )
    except Exception as e:
        console.print(f"[error]Ошибка инициализации: {e}[/error]")
        raise typer.Exit(code=1)

    # Выполнение агрегации с визуализацией прогресса (спиннер)
    aggregated_data = ""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("[info]Сбор и форматирование файлов...[/info]", total=None)
        
        try:
            aggregated_data = aggregator.aggregate()
            progress.update(task, completed=True)
        except Exception as e:
            progress.stop()
            console.print(f"[error]Критическая ошибка при агрегации: {e}[/error]")
            raise typer.Exit(code=1)

    # Запись результата в файл
    try:
        output_file.write_text(aggregated_data, encoding='utf-8')
        success_panel = Panel(
            f"Агрегация успешно завершена!\n"
            f"Файл сохранен: [success]{output_file.resolve()}[/success]",
            border_style="green",
            expand=False
        )
        console.print(success_panel)
    except Exception as e:
        console.print(f"[error]Ошибка при записи в файл: {e}[/error]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()