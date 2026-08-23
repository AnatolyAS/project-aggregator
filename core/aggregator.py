from pathlib import Path
from enum import Enum
from typing import List, Optional, Union

import pathspec
import tiktoken

# Импорт независимых обработчиков из утвержденной директории
from core.format_handlers import (
    MarkdownHandler, PlainTextHandler, 
    JSONHandler, HTMLHandler, PDFHandler
)


class ConsolidationMethod(Enum):
    """Определение доступных методов консолидации данных."""
    MARKDOWN = "markdown"
    PLAIN_TEXT = "plain_text"
    JSON = "json"
    HTML = "html"
    PDF = "pdf"


class FileAggregator:
    """Ядро агрегации (Контекст).
    
    Обеспечивает обход директорий и маршрутизацию данных в классы-обработчики.
    """

    DEFAULT_IGNORE_DIRS = {'.git', '.venv', 'venv', '__pycache__', '.vscode', '.idea'}

    _HANDLERS = {
        ConsolidationMethod.MARKDOWN: MarkdownHandler(),
        ConsolidationMethod.PLAIN_TEXT: PlainTextHandler(),
        ConsolidationMethod.JSON: JSONHandler(),
        ConsolidationMethod.HTML: HTMLHandler(),
        ConsolidationMethod.PDF: PDFHandler(),
    }

    def __init__(
        self, 
        target_dir: str | Path, 
        method: ConsolidationMethod = ConsolidationMethod.MARKDOWN,
        ignore_dirs: Optional[set[str]] = None,
        allowed_extensions: Optional[List[str]] = None,
        compress_code: bool = False
    ) -> None:
        self.target_dir = Path(target_dir).resolve()
        self.method = method
        self.ignore_dirs = ignore_dirs if ignore_dirs is not None else self.DEFAULT_IGNORE_DIRS
        self.compress_code = compress_code
        
        if allowed_extensions:
            self.allowed_extensions = {
                ext.lower() if ext.startswith('.') else f'.{ext.lower()}' 
                for ext in allowed_extensions
            }
        else:
            self.allowed_extensions = None

        self.gitignore_spec = self._load_gitignore()

    @staticmethod
    def count_tokens(text: str, model: str = "gpt-4o") -> int:
        try:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except Exception:
            return 0

    def _load_gitignore(self) -> Optional[pathspec.PathSpec]:
        gitignore_path = self.target_dir / '.gitignore'
        if gitignore_path.is_file():
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                return pathspec.PathSpec.from_lines('gitwildmatch', f)
        return None

    def _is_text_file(self, file_path: Path) -> bool:
        try:
            with open(file_path, 'tr', encoding='utf-8') as f:
                f.read(1024)
            return True
        except UnicodeDecodeError:
            return False

    def _gather_files(self) -> List[Path]:
        gathered_files = []
        for file_path in self.target_dir.rglob('*'):
            if not file_path.is_file(): continue
            relative_path = file_path.relative_to(self.target_dir)
            if any(part in self.ignore_dirs for part in relative_path.parts): continue
            if self.gitignore_spec and self.gitignore_spec.match_file(relative_path.as_posix()): continue
            if self.allowed_extensions and file_path.suffix.lower() not in self.allowed_extensions: continue
            if self._is_text_file(file_path): gathered_files.append(file_path)
        return sorted(gathered_files)

    def _process_content(self, file_path: Path) -> str:
        """Безопасно читает файл и применяет сжатие, если включено."""
        content = file_path.read_text(encoding='utf-8')
        if self.compress_code:
            lines = [line.rstrip() for line in content.splitlines() if line.strip()]
            content = "\n".join(lines)
        return content

    def aggregate(self) -> Union[str, bytes]:
        """Точка входа. Собирает файлы и передает их в обработчик формата."""
        if not self.target_dir.exists() or not self.target_dir.is_dir():
            raise ValueError(f"Директория не найдена: {self.target_dir}")

        files = self._gather_files()
        handler = self._HANDLERS.get(self.method)
        
        if not handler:
            raise NotImplementedError(f"Обработчик для метода {self.method} не реализован.")
            
        return handler.generate(self.target_dir, files, self._process_content)