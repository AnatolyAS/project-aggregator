import typer
from pathlib import Path
from typing import List, Optional

import questionary
from questionary import Style
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.theme import Theme

from core.aggregator import FileAggregator, ConsolidationMethod

# Цветовая схема для Rich (панели и логи)
custom_theme = Theme({
    "info": "cyan",
    "success": "bold green",
    "warning": "yellow",
    "error": "bold red"
})

console = Console(theme=custom_theme)

# Кастомный стиль Questionary для полного соответствия GitHub CLI (gh)
gh_cli_style = Style([
    ('qmark', 'fg:green bold'),         # Зеленый знак вопроса '?'
    ('question', 'bold'),               # Жирный текст вопроса
    ('answer', 'fg:cyan'),              # Циановый цвет введенного ответа
    ('pointer', 'fg:cyan bold'),        # Циановый курсор '>'
    ('highlighted', 'fg:cyan bold'),    # Выделенный пункт меню
    ('instruction', 'fg:darkgray'),     # Серый текст подсказки '[Use arrows...]'
])

app = typer.Typer(
    name="Project Aggregator CLI",
    help="Профессиональная утилита для консолидации файлов проекта.",
    add_completion=False,
)

@app.command(name="start")
def start_command(
    target_dir: Optional[Path] = typer.Argument(
        None,
        help="Путь к директории проекта. Если не указан, запустится интерактивный режим.",
    ),
    output_file: Path = typer.Option(
        Path("aggregated_output.md"), "--output", "-o",
        help="Путь к результирующему файлу.",
    ),
    method: ConsolidationMethod = typer.Option(
        ConsolidationMethod.MARKDOWN, "--method", "-m",
        help="Метод форматирования выходных данных.",
    ),
    ignore: Optional[List[str]] = typer.Option(
        None, "--ignore", "-i",
        help="Дополнительные директории для исключения.",
    ),
    extensions: Optional[List[str]] = typer.Option(
        None, "--ext", "-e",
        help="Фильтр расширений (например: -e py -e md).",
    ),
    compress: bool = typer.Option(
        False, "--compress", "-c",
        help="Включить сжатие кода.",
    )
) -> None:
    """Выполняет процесс агрегации файлов (интерактивный или автоматический режим)."""
    
    # ИНТЕРАКТИВНЫЙ РЕЖИМ (Стиль GitHub CLI)
    if target_dir is None:
        console.print("\n") # Отступ для красоты
        
        target_dir_str = questionary.path(
            "Target directory (целевая папка):",
            style=gh_cli_style
        ).ask()
        
        # Если пользователь нажал Ctrl+C
        if target_dir_str is None:
            raise typer.Exit()
            
        target_dir = Path(target_dir_str).resolve()
        
        method_str = questionary.select(
            "Consolidation method (метод вывода):",
            choices=[m.value for m in ConsolidationMethod],
            instruction="(Use arrows to move, type to filter)",
            style=gh_cli_style
        ).ask()
        if method_str is None: raise typer.Exit()
        method = ConsolidationMethod(method_str)
        
        ext_str = questionary.text(
            "Extensions (расширения через запятую, оставьте пустым для всех):",
            style=gh_cli_style
        ).ask()
        if ext_str is None: raise typer.Exit()
        
        if ext_str.strip():
            extensions = [e.strip() for e in ext_str.split(',')]
            
        compress = questionary.confirm(
            "Compress code (оптимизировать код для LLM)?",
            default=False,
            style=gh_cli_style
        ).ask()
        if compress is None: raise typer.Exit()
        
        out_str = questionary.text(
            "Output file (файл сохранения):", 
            default="aggregated_output.md",
            style=gh_cli_style
        ).ask()
        if out_str is None: raise typer.Exit()
        output_file = Path(out_str)
        console.print("\n")

    # Автоматическая корректировка расширения файла
    if output_file.name == "aggregated_output.md":
        ext_map = {
            ConsolidationMethod.MARKDOWN: ".md",
            ConsolidationMethod.PLAIN_TEXT: ".txt",
            ConsolidationMethod.JSON: ".json",
            ConsolidationMethod.HTML: ".html",
            ConsolidationMethod.PDF: ".pdf"
        }
        output_file = output_file.with_suffix(ext_map.get(method, ".md"))

    # Добавление суффикса при сжатии
    if compress and not output_file.stem.endswith("_compressed"):
        output_file = output_file.with_name(f"{output_file.stem}_compressed{output_file.suffix}")

    ext_info = f"[info]{', '.join(extensions)}[/info]" if extensions else "[info]Все текстовые[/info]"
    compress_info = "[success]Включено[/success]" if compress else "[warning]Отключено[/warning]"
    
    console.print(Panel(
        f"[bold]Project Aggregator[/bold]\n"
        f"Директория: [info]{target_dir}[/info]\n"
        f"Метод: [info]{method.value}[/info]\n"
        f"Расширения: {ext_info}\n"
        f"Сжатие: {compress_info}",
        border_style="cyan", expand=False
    ))

    ignore_dirs = set(ignore) if ignore else None

    try:
        aggregator = FileAggregator(
            target_dir=target_dir, method=method,
            ignore_dirs=ignore_dirs, allowed_extensions=extensions,
            compress_code=compress
        )
    except Exception as e:
        console.print(f"[error]Ошибка инициализации: {e}[/error]")
        raise typer.Exit(code=1)

    aggregated_data = ""
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console, transient=True) as progress:
        task = progress.add_task("[info]Сбор и форматирование файлов...[/info]", total=None)
        try:
            aggregated_data = aggregator.aggregate()
            progress.update(task, completed=True)
        except Exception as e:
            progress.stop()
            console.print(f"[error]Критическая ошибка: {e}[/error]")
            raise typer.Exit(code=1)

    try:
        if isinstance(aggregated_data, bytes):
            output_file.write_bytes(aggregated_data)
            token_info = ""
        else:
            output_file.write_text(aggregated_data, encoding='utf-8')
            tokens = FileAggregator.count_tokens(aggregated_data)
            token_info = f"\nТокенов (gpt-4o): [info]{tokens:,}[/info]"
            
        console.print(Panel(
            f"Агрегация завершена!\nСохранен: [success]{output_file.resolve()}[/success]{token_info}",
            border_style="green", expand=False
        ))
    except Exception as e:
        console.print(f"[error]Ошибка записи: {e}[/error]")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()