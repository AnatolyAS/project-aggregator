import json
from pathlib import Path
from enum import Enum
from typing import List, Dict, Any, Optional


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

    Обеспечивает кроссплатформенный обход директорий, фильтрацию нежелательных
    папок (включая extra_assets) и бинарных файлов, а также консолидацию
    текстовых данных с использованием различных методов форматирования.

    Attributes:
        DEFAULT_IGNORE_DIRS (set[str]): Набор имен директорий, которые исключаются
            из обработки по умолчанию.
        target_dir (Path): Абсолютный путь к целевой директории.
        method (ConsolidationMethod): Выбранный метод форматирования данных.
        ignore_dirs (set[str]): Итоговый набор имен игнорируемых директорий.
    """

    DEFAULT_IGNORE_DIRS = {'.git', '.venv', 'venv', '__pycache__', '.vscode', '.idea', 'extra_assets'}

    def __init__(
        self, 
        target_dir: str | Path, 
        method: ConsolidationMethod = ConsolidationMethod.MARKDOWN,
        ignore_dirs: Optional[set[str]] = None
    ) -> None:
        """Инициализирует экземпляр класса FileAggregator.

        Args:
            target_dir (str | Path): Путь к целевой директории, файлы которой
                необходимо агрегировать.
            method (ConsolidationMethod, optional): Выбранный метод форматирования
                результирующих данных. По умолчанию ConsolidationMethod.MARKDOWN.
            ignore_dirs (Optional[set[str]], optional): Пользовательский набор имен
                директорий для исключения из обхода. Если не указан, используется
                DEFAULT_IGNORE_DIRS.
        """
        self.target_dir = Path(target_dir).resolve()
        self.method = method
        self.ignore_dirs = ignore_dirs if ignore_dirs is not None else self.DEFAULT_IGNORE_DIRS

    def _is_text_file(self, file_path: Path) -> bool:
        """Выполняет эвристическую проверку файла на принадлежность к текстовому формату.

        Функция пытается прочитать первые 1024 байта файла, используя кодировку UTF-8.
        Если возникает ошибка декодирования, файл считается бинарным.

        Args:
            file_path (Path): Абсолютный или относительный путь к проверяемому файлу.

        Returns:
            bool: True, если файл успешно прочитан как текст (UTF-8), иначе False.
        """
        try:
            with open(file_path, 'tr', encoding='utf-8') as f:
                f.read(1024)
            return True
        except UnicodeDecodeError:
            return False

    def _gather_files(self) -> List[Path]:
        """Осуществляет рекурсивный сбор файлов внутри целевой директории.

        Обходит файловую систему, пропуская файлы, путь к которым содержит директории
        из набора ignore_dirs, а также отсеивая бинарные файлы с помощью _is_text_file.
        Результирующий список сортируется в алфавитном порядке для обеспечения
        предсказуемости вывода.

        Returns:
            List[Path]: Отсортированный список объектов Path, представляющих
                обнаруженные текстовые файлы.
        """
        gathered_files = []
        for file_path in self.target_dir.rglob('*'):
            if not file_path.is_file():
                continue
            
            # Проверка наличия игнорируемых директорий в пути
            if any(part in self.ignore_dirs for part in file_path.relative_to(self.target_dir).parts):
                continue
                
            if self._is_text_file(file_path):
                gathered_files.append(file_path)
                
        return sorted(gathered_files)

    def _format_markdown(self, files: List[Path]) -> str:
        """Формирует консолидированную строку из файлов в формате Markdown.

        Каждый файл оборачивается в блок кода с указанием расширения для подсветки
        синтаксиса. В качестве заголовков используется относительный путь к файлу.

        Args:
            files (List[Path]): Список путей к файлам, подлежащим обработке.

        Returns:
            str: Агрегированные данные, отформатированные как Markdown-документ.
        """
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
        """Формирует консолидированную строку из файлов в формате простого текста.

        Для визуального разделения файлов используются текстовые границы (разделители)
        с указанием начала и конца содержимого конкретного файла.

        Args:
            files (List[Path]): Список путей к файлам, подлежащим обработке.

        Returns:
            str: Агрегированные данные, отформатированные как простой текст.
        """
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
        """Формирует консолидированную строку из файлов в формате JSON.

        Создает структурированный объект, содержащий имя проекта и список файлов.
        Для каждого файла указывается его относительный путь, расширение,
        статус чтения и содержимое (или текст ошибки).

        Args:
            files (List[Path]): Список путей к файлам, подлежащим обработке.

        Returns:
            str: Агрегированные данные в виде отформатированной JSON-строки.
        """
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
        """Выполняет главный процесс агрегации файлов проекта.

        Проверяет существование целевой директории, собирает валидные файлы
        и применяет выбранный при инициализации метод консолидации данных.

        Returns:
            str: Итоговая строка, содержащая агрегированные данные всех файлов
                в выбранном формате.

        Raises:
            ValueError: Если целевая директория не существует или не является папкой.
            NotImplementedError: Если выбран неподдерживаемый метод консолидации.
        """
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