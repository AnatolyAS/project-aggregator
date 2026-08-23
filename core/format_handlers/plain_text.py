from pathlib import Path
from typing import List, Callable
from .base import BaseFormatHandler

class PlainTextHandler(BaseFormatHandler):
    """Отвечает за генерацию простого текста с разделителями."""
    
    def generate(self, target_dir: Path, files: List[Path], content_reader: Callable[[Path], str]) -> str:
        separator = "=" * 60
        output = [f"ПРОЕКТ: {target_dir.name}\n{separator}\n"]
        for file_path in files:
            relative_path = file_path.relative_to(target_dir)
            output.append(f"--- НАЧАЛО ФАЙЛА: {relative_path} ---")
            try:
                output.append(content_reader(file_path))
            except Exception as e:
                output.append(f"[Ошибка чтения файла: {e}]")
            output.append(f"--- КОНЕЦ ФАЙЛА: {relative_path} ---\n")
        return "\n".join(output)