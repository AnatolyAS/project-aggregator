from pathlib import Path
from typing import List, Callable
from .base import BaseFormatHandler

class MarkdownHandler(BaseFormatHandler):
    """Отвечает за генерацию Markdown-документа."""
    
    def generate(self, target_dir: Path, files: List[Path], content_reader: Callable[[Path], str]) -> str:
        output = [f"# Агрегация проекта: {target_dir.name}\n"]
        for file_path in files:
            relative_path = file_path.relative_to(target_dir)
            output.append(f"## Файл: {relative_path}")
            output.append(f"```{file_path.suffix.lstrip('.')}")
            try:
                output.append(content_reader(file_path))
            except Exception as e:
                output.append(f"[Ошибка чтения файла: {e}]")
            output.append("```\n")
        return "\n".join(output)