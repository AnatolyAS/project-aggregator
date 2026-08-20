import json
from pathlib import Path
from enum import Enum
from typing import List, Dict, Any, Optional

class ConsolidationMethod(Enum):
    """Определение доступных методов консолидации данных."""
    MARKDOWN = "markdown"
    PLAIN_TEXT = "plain_text"
    JSON = "json"

class FileAggregator:
    """
    Основной класс ядра для агрегации файлов проекта.
    Обеспечиет кроссплатформенный обход директорий и консолидацию данных.
    """
    
    # Базовые директории, исключаемые из обработки по умолчанию
    DEFAULT_IGNORE_DIRS = {'.git', '.venv', 'venv', '__pycache__', '.vscode', '.idea', 'extra_assets'}

    def __init__(
        self, 
        target_dir: str | Path, 
        method: ConsolidationMethod = ConsolidationMethod.MARKDOWN,
        ignore_dirs: Optional[set[str]] = None
    ):
        self.target_dir = Path(target_dir).resolve()
        self.method = method
        self.ignore_dirs = ignore_dirs if ignore_dirs is not None else self.DEFAULT_IGNORE_DIRS

    def _is_text_file(self, file_path: Path) -> bool:
        """Эвристическая проверка файла на принадлежность к текстовому формату."""
        try:
            with open(file_path, 'tr', encoding='utf-8') as f:
                f.read(1024)
            return True
        except UnicodeDecodeError:
            return False

    def _gather_files(self) -> List[Path]:
        """Рекурсивный сбор файлов с учетом игнорируемых директорий."""
        gathered_files = []
        for file_path in self.target_dir.rglob('*'):
            if not file_path.is_file():
                continue
            
            # Проверка наличия игнорируемых директорий в пути
            if any(part in self.ignore_dirs for part in file_path.relative_to(self.target_dir).parts):
                continue
                
            if self._is_text_file(file_path):
                gathered_files.append(file_path)
                
        # Сортировка для предсказуемости результирующего файла
        return sorted(gathered_files)

    def _format_markdown(self, files: List[Path]) -> str:
        """Консолидация в формате Markdown (оптимально для чтения и LLM)."""
        output = [f"# Агрегация проекта: {self.target_dir.name}\n"]
        for file_path in files:
            relative_path = file_path.relative_to(self.target_dir)
            output.append(f"## Файл: {relative_path}")
            output.append(f"```{file_path.suffix.lstrip('.')}")
            try:
                output.append(file_path.read_text(encoding='utf-8'))
            except Exception as e:
                output.append(f"[Ошибка чтения файла: {e}]")
            output.append("```\n")
        return "\n".join(output)

    def _format_plain_text(self, files: List[Path]) -> str:
        """Консолидация в формате простого текста с разделителями."""
        separator = "=" * 60
        output = [f"ПРОЕКТ: {self.target_dir.name}\n{separator}\n"]
        for file_path in files:
            relative_path = file_path.relative_to(self.target_dir)
            output.append(f"--- НАЧАЛО ФАЙЛА: {relative_path} ---")
            try:
                output.append(file_path.read_text(encoding='utf-8'))
            except Exception as e:
                output.append(f"[Ошибка чтения файла: {e}]")
            output.append(f"--- КОНЕЦ ФАЙЛА: {relative_path} ---\n")
        return "\n".join(output)

    def _format_json(self, files: List[Path]) -> str:
        """Консолидация в структурированный JSON-формат."""
        data: Dict[str, Any] = {
            "project_name": self.target_dir.name,
            "files": []
        }
        for file_path in files:
            relative_path = str(file_path.relative_to(self.target_dir))
            try:
                content = file_path.read_text(encoding='utf-8')
                status = "success"
            except Exception as e:
                content = str(e)
                status = "error"
                
            data["files"].append({
                "path": relative_path,
                "extension": file_path.suffix,
                "status": status,
                "content": content
            })
        return json.dumps(data, ensure_ascii=False, indent=4)

    def aggregate(self) -> str:
        """Главный метод выполнения агрегации."""
        if not self.target_dir.exists() or not self.target_dir.is_dir():
            raise ValueError(f"Директория не найдена: {self.target_dir}")

        files = self._gather_files()
        
        if self.method == ConsolidationMethod.MARKDOWN:
            return self._format_markdown(files)
        elif self.method == ConsolidationMethod.PLAIN_TEXT:
            return self._format_plain_text(files)
        elif self.method == ConsolidationMethod.JSON:
            return self._format_json(files)
        else:
            raise NotImplementedError(f"Метод {self.method} не поддерживается.")