import json
import urllib.request
from pathlib import Path
from enum import Enum
from typing import List, Dict, Any, Optional, Union

import pathspec
from jinja2 import Template
from fpdf import FPDF


class ConsolidationMethod(Enum):
    """Определение доступных методов консолидации данных."""
    MARKDOWN = "markdown"
    PLAIN_TEXT = "plain_text"
    JSON = "json"
    HTML = "html"
    PDF = "pdf"


class FileAggregator:
    """Основной класс ядра для агрегации файлов проекта.

    Обеспечивает кроссплатформенный обход директорий, интеллектуальную фильтрацию
    и консолидацию данных, включая расширенные форматы вывода (HTML, PDF).
    """

    DEFAULT_IGNORE_DIRS = {'.git', '.venv', 'venv', '__pycache__', '.vscode', '.idea', 'extra_assets'}

    # Встроенный шаблон для генерации интерактивного HTML
    HTML_TEMPLATE = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Агрегация проекта: {{ project_name }}</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; margin: 0; display: flex; height: 100vh; background-color: #1e1e1e; color: #d4d4d4; }
            .sidebar { width: 300px; background-color: #252526; padding: 20px; overflow-y: auto; border-right: 1px solid #333; }
            .sidebar a { color: #569cd6; text-decoration: none; display: block; margin-bottom: 10px; font-size: 14px; word-break: break-all; }
            .sidebar a:hover { text-decoration: underline; }
            .content { flex: 1; padding: 20px; overflow-y: auto; }
            .file-block { margin-bottom: 40px; background-color: #1e1e1e; border: 1px solid #333; border-radius: 5px; }
            .file-header { background-color: #2d2d30; padding: 10px 20px; font-weight: bold; border-bottom: 1px solid #333; }
            pre { margin: 0; padding: 20px; overflow-x: auto; font-family: 'Consolas', monospace; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="sidebar">
            <h3>Файлы проекта</h3>
            {% for file in files %}
                <a href="#file-{{ loop.index }}">{{ file.path }}</a>
            {% endfor %}
        </div>
        <div class="content">
            <h1>Проект: {{ project_name }}</h1>
            {% for file in files %}
                <div class="file-block" id="file-{{ loop.index }}">
                    <div class="file-header">{{ file.path }}</div>
                    <pre>{{ file.content | e }}</pre>
                </div>
            {% endfor %}
        </div>
    </body>
    </html>
    """

    def __init__(
        self, 
        target_dir: str | Path, 
        method: ConsolidationMethod = ConsolidationMethod.MARKDOWN,
        ignore_dirs: Optional[set[str]] = None,
        allowed_extensions: Optional[List[str]] = None
    ) -> None:
        self.target_dir = Path(target_dir).resolve()
        self.method = method
        self.ignore_dirs = ignore_dirs if ignore_dirs is not None else self.DEFAULT_IGNORE_DIRS
        
        if allowed_extensions:
            self.allowed_extensions = {
                ext.lower() if ext.startswith('.') else f'.{ext.lower()}' 
                for ext in allowed_extensions
            }
        else:
            self.allowed_extensions = None

        self.gitignore_spec = self._load_gitignore()

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
            if not file_path.is_file():
                continue
            
            relative_path = file_path.relative_to(self.target_dir)
            
            if any(part in self.ignore_dirs for part in relative_path.parts):
                continue
                
            if self.gitignore_spec and self.gitignore_spec.match_file(relative_path.as_posix()):
                continue
                
            if self.allowed_extensions and file_path.suffix.lower() not in self.allowed_extensions:
                continue
                
            if self._is_text_file(file_path):
                gathered_files.append(file_path)
                
        return sorted(gathered_files)

    def _format_markdown(self, files: List[Path]) -> str:
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
        data: Dict[str, Any] = {"project_name": self.target_dir.name, "files": []}
        for file_path in files:
            relative_path = str(file_path.relative_to(self.target_dir))
            try:
                content = file_path.read_text(encoding='utf-8')
                status = "success"
            except Exception as e:
                content = str(e)
                status = "error"
            data["files"].append({
                "path": relative_path, "extension": file_path.suffix, 
                "status": status, "content": content
            })
        return json.dumps(data, ensure_ascii=False, indent=4)

    def _format_html(self, files: List[Path]) -> str:
        """Генерирует интерактивный HTML-документ с использованием Jinja2."""
        template = Template(self.HTML_TEMPLATE)
        file_data = []
        for file_path in files:
            relative_path = str(file_path.relative_to(self.target_dir))
            try:
                content = file_path.read_text(encoding='utf-8')
            except Exception as e:
                content = f"[Ошибка чтения: {e}]"
            file_data.append({"path": relative_path, "content": content})
            
        return template.render(project_name=self.target_dir.name, files=file_data)

    def _ensure_pdf_font(self) -> Path:
        """Обеспечивает наличие шрифта с поддержкой кириллицы (UTF-8).
        Сохраняет шрифт в разрешенную директорию extra_assets/.
        """
        font_path = Path("extra_assets") / "Roboto-Regular.ttf"
        font_path.parent.mkdir(exist_ok=True)
        
        if not font_path.exists():
            font_url = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf"
            urllib.request.urlretrieve(font_url, font_path)
        return font_path

    def _format_pdf(self, files: List[Path]) -> bytes:
        """Генерирует PDF-документ."""
        font_path = self._ensure_pdf_font()
        
        pdf = FPDF()
        pdf.add_font("Roboto", "", str(font_path), uni=True)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Roboto", size=14)
        
        # Заголовок
        pdf.cell(0, 10, f"Проект: {self.target_dir.name}", ln=True, align='C')
        pdf.ln(10)
        
        # Содержимое
        pdf.set_font("Roboto", size=10)
        for file_path in files:
            relative_path = str(file_path.relative_to(self.target_dir))
            pdf.set_font("Roboto", size=12)
            pdf.cell(0, 10, f"--- {relative_path} ---", ln=True, fill=False)
            pdf.set_font("Roboto", size=8)
            
            try:
                content = file_path.read_text(encoding='utf-8')
            except Exception as e:
                content = f"[Ошибка чтения: {e}]"
                
            pdf.multi_cell(0, 5, content)
            pdf.ln(5)
            
        return bytes(pdf.output())

    def aggregate(self) -> Union[str, bytes]:
        """Выполняет процесс агрегации. Возвращает строку или байты (для PDF)."""
        if not self.target_dir.exists() or not self.target_dir.is_dir():
            raise ValueError(f"Директория не найдена: {self.target_dir}")

        files = self._gather_files()
        
        match self.method:
            case ConsolidationMethod.MARKDOWN: return self._format_markdown(files)
            case ConsolidationMethod.PLAIN_TEXT: return self._format_plain_text(files)
            case ConsolidationMethod.JSON: return self._format_json(files)
            case ConsolidationMethod.HTML: return self._format_html(files)
            case ConsolidationMethod.PDF: return self._format_pdf(files)
            case _: raise NotImplementedError(f"Метод {self.method} не поддерживается.")