import json
from pathlib import Path
from enum import Enum
from typing import List, Dict, Any, Optional

import pathspec


class ConsolidationMethod(Enum):
    """Определение доступных методов консолидации данных.

    Attributes:
        MARKDOWN: Форматирование вывода в виде Markdown-разметки.
        PLAIN_TEXT: Форматирование вывода в виде простого текста с разделителями.
        JSON: Форматирование вывода в виде структурированного JSON-объекта.
    """
    MARKDOWN = "markdown"
    PLAIN_TEXT = "plain_text"
    JSON = "json"


class FileAggregator:
    """Основной класс ядра для агрегации файлов проекта.

    Обеспечивает кроссплатформенный обход директорий, интеллектуальную фильтрацию
    (базовые директории, .gitignore, расширения файлов), отсев бинарных файлов
    и консолидацию текстовых данных выбранным методом.

    Attributes:
        DEFAULT_IGNORE_DIRS (set[str]): Базовый набор исключаемых директорий.
        target_dir (Path): Абсолютный путь к целевой директории.
        method (ConsolidationMethod): Выбранный метод форматирования данных.
        ignore_dirs (set[str]): Итоговый набор имен игнорируемых директорий.
        allowed_extensions (Optional[set[str]]): Набор разрешенных расширений.
        gitignore_spec (Optional[pathspec.PathSpec]): Скомпилированные правила .gitignore.
    """

    DEFAULT_IGNORE_DIRS = {'.git', '.venv', 'venv', '__pycache__', '.vscode', '.idea', 'extra_assets'}

    def __init__(
        self, 
        target_dir: str | Path, 
        method: ConsolidationMethod = ConsolidationMethod.MARKDOWN,
        ignore_dirs: Optional[set[str]] = None,
        allowed_extensions: Optional[List[str]] = None
    ) -> None:
        """Инициализирует экземпляр FileAggregator с настройками фильтрации.

        Args:
            target_dir (str | Path): Путь к целевой директории.
            method (ConsolidationMethod, optional): Метод форматирования.
            ignore_dirs (Optional[set[str]], optional): Пользовательские исключения директорий.
            allowed_extensions (Optional[List[str]], optional): Список разрешенных
                расширений файлов (например, ['.py', 'md']). Если None, разрешены все.
        """
        self.target_dir = Path(target_dir).resolve()
        self.method = method
        self.ignore_dirs = ignore_dirs if ignore_dirs is not None else self.DEFAULT_IGNORE_DIRS
        
        # Нормализация переданных расширений (приведение к виду '.ext' и нижнему регистру)
        if allowed_extensions:
            self.allowed_extensions = {
                ext.lower() if ext.startswith('.') else f'.{ext.lower()}' 
                for ext in allowed_extensions
            }
        else:
            self.allowed_extensions = None

        self.gitignore_spec = self._load_gitignore()

    def _load_gitignore(self) -> Optional[pathspec.PathSpec]:
        """Ищет и парсит файл .gitignore в корне целевой директории.

        Returns:
            Optional[pathspec.PathSpec]: Объект спецификации путей для фильтрации,
                либо None, если файл .gitignore отсутствует.
        """
        gitignore_path = self.target_dir / '.gitignore'
        if gitignore_path.is_file():
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                return pathspec.PathSpec.from_lines('gitwildmatch', f)
        return None

    def _is_text_file(self, file_path: Path) -> bool:
        """Выполняет эвристическую проверку файла на принадлежность к текстовому формату.

        Args:
            file_path (Path): Путь к проверяемому файлу.

        Returns:
            bool: True, если файл успешно прочитан как текст, иначе False.
        """
        try:
            with open(file_path, 'tr', encoding='utf-8') as f:
                f.read(1024)
            return True
        except UnicodeDecodeError:
            return False

    def _gather_files(self) -> List[Path]:
        """Осуществляет рекурсивный сбор файлов с каскадной интеллектуальной фильтрацией.

        Процесс отсева:
        1. Проверка вхождения в базовые игнорируемые директории.
        2. Проверка по правилам .gitignore (если присутствует).
        3. Проверка на соответствие разрешенным расширениям (если заданы).
        4. Проверка на принадлежность к текстовым форматам (исключение бинарников).

        Returns:
            List[Path]: Отсортированный список валидных текстовых файлов.
        """
        gathered_files = []
        for file_path in self.target_dir.rglob('*'):
            if not file_path.is_file():
                continue
            
            relative_path = file_path.relative_to(self.target_dir)
            
            # 1. Проверка базовых игнорируемых директорий
            if any(part in self.ignore_dirs for part in relative_path.parts):
                continue
                
            # 2. Проверка по правилам .gitignore (используется POSIX-формат путей)
            if self.gitignore_spec and self.gitignore_spec.match_file(relative_path.as_posix()):
                continue
                
            # 3. Фильтрация по явно заданным расширениям
            if self.allowed_extensions and file_path.suffix.lower() not in self.allowed_extensions:
                continue
                
            # 4. Проверка на текстовый формат
            if self._is_text_file(file_path):
                gathered_files.append(file_path)
                
        return sorted(gathered_files)

    def _format_markdown(self, files: List[Path]) -> str:
        """Формирует консолидированную строку в формате Markdown."""
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
        """Формирует консолидированную строку в формате простого текста."""
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
        """Формирует консолидированную строку в формате JSON."""
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
        """Выполняет главный процесс агрегации файлов проекта."""
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