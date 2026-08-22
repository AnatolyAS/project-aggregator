import typer
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.theme import Theme

from core.aggregator import FileAggregator, ConsolidationMethod

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
        help="Абсолютный или относительный путь к директории проекта.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    output_file: Path = typer.Option(
        Path("aggregated_output.md"),
        "--output",
        "-o",
        help="Путь к результирующему файлу.",
        writable=True,
    ),
    method: ConsolidationMethod = typer.Option(
        ConsolidationMethod.MARKDOWN,
        "--method",
        "-m",
        help="Метод форматирования выходных данных.",
    ),
    ignore: Optional[List[str]] = typer.Option(
        None,
        "--ignore",
        "-i",
        help="Дополнительные имена директорий для исключения.",
    ),
    extensions: Optional[List[str]] = typer.Option(
        None,
        "--ext",
        "-e",
        help="Фильтр расширений (например: -e py -e md).",
    ),
    compress: bool = typer.Option(
        False,
        "--compress",
        "-c",
        help="Включить сжатие кода (удаление пустых строк и лишних пробелов).",
    )
) -> None:
    """Выполняет процесс агрегации файлов с визуальным сопровождением."""
    
    if output_file.name == "aggregated_output.md":
        ext_map = {
            ConsolidationMethod.MARKDOWN: ".md",
            ConsolidationMethod.PLAIN_TEXT: ".txt",
            ConsolidationMethod.JSON: ".json",
            ConsolidationMethod.HTML: ".html",
            ConsolidationMethod.PDF: ".pdf"
        }
        output_file = output_file.with_suffix(ext_map.get(method, ".md"))

    # НОВОЕ: Автоматическое добавление суффикса _compressed
    if compress and not output_file.stem.endswith("_compressed"):
        output_file = output_file.with_name(f"{output_file.stem}_compressed{output_file.suffix}")

    ext_info = f"[info]{', '.join(extensions)}[/info]" if extensions else "[info]Все текстовые[/info]"
    compress_info = "[success]Включено[/success]" if compress else "[warning]Отключено[/warning]"
    
    welcome_panel = Panel(
        f"[bold]Project Aggregator[/bold]\n"
        f"Целевая директория: [info]{target_dir}[/info]\n"
        f"Метод: [info]{method.value}[/info]\n"
        f"Расширения: {ext_info}\n"
        f"Сжатие кода: {compress_info}",
        border_style="cyan",
        expand=False
    )
    console.print(welcome_panel)

    ignore_dirs = set(ignore) if ignore else None

    try:
        aggregator = FileAggregator(
            target_dir=target_dir,
            method=method,
            ignore_dirs=ignore_dirs,
            allowed_extensions=extensions,
            compress_code=compress
        )
    except Exception as e:
        console.print(f"[error]Ошибка инициализации: {e}[/error]")
        raise typer.Exit(code=1)

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

    try:
        if isinstance(aggregated_data, bytes):
            output_file.write_bytes(aggregated_data)
            token_info = ""
        else:
            output_file.write_text(aggregated_data, encoding='utf-8')
            tokens = FileAggregator.count_tokens(aggregated_data)
            token_info = f"\nТокенов (gpt-4o): [info]{tokens:,}[/info]"
            
        success_panel = Panel(
            f"Агрегация успешно завершена!\n"
            f"Файл сохранен: [success]{output_file.resolve()}[/success]{token_info}",
            border_style="green",
            expand=False
        )
        console.print(success_panel)
    except Exception as e:
        console.print(f"[error]Ошибка при записи в файл: {e}[/error]")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()