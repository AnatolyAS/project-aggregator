from pathlib import Path
from typing import List, Callable
from jinja2 import Template

from pygments import highlight
from pygments.lexers import get_lexer_for_filename
from pygments.lexers.special import TextLexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound

from .base import BaseFormatHandler

class HTMLHandler(BaseFormatHandler):
    """Отвечает за генерацию интерактивного HTML-отчета с профессиональной подсветкой синтаксиса."""
    
    # Шаблон обновлен: добавлены переменные для CSS Pygments, убрано экранирование (| e), 
    # так как Pygments самостоятельно генерирует безопасный HTML-код.
    HTML_TEMPLATE = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Агрегация проекта: {{ project_name }}</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; display: flex; height: 100vh; background-color: #1e1e1e; color: #d4d4d4; }
            .sidebar { width: 300px; background-color: #252526; padding: 20px; overflow-y: auto; border-right: 1px solid #333; }
            .sidebar a { color: #569cd6; text-decoration: none; display: block; margin-bottom: 10px; font-size: 14px; word-break: break-all; }
            .sidebar a:hover { text-decoration: underline; }
            .content { flex: 1; padding: 20px; overflow-y: auto; background-color: #1e1e1e; }
            .file-block { margin-bottom: 40px; border: 1px solid #333; border-radius: 5px; background-color: #1e1e1e; overflow: hidden; }
            .file-header { background-color: #2d2d30; padding: 10px 20px; font-weight: bold; border-bottom: 1px solid #333; }
            
            /* Динамические стили подсветки синтаксиса (Pygments) */
            {{ pygments_css }}
            
            /* Переопределение стилей контейнера для бесшовной интеграции с нашей темой */
            .highlight { margin: 0; padding: 15px; overflow-x: auto; background-color: #1e1e1e !important; }
            .highlight pre { margin: 0; font-family: 'Consolas', 'Courier New', monospace; font-size: 14px; line-height: 1.4; }
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
                    <!-- Блок кода, отформатированный Pygments -->
                    {{ file.content }}
                </div>
            {% endfor %}
        </div>
    </body>
    </html>
    """

    def generate(self, target_dir: Path, files: List[Path], content_reader: Callable[[Path], str]) -> str:
        template = Template(self.HTML_TEMPLATE)
        file_data = []
        
        # Инициализация форматтера HTML в стиле 'monokai'
        formatter = HtmlFormatter(style='monokai', cssclass='highlight')
        # Получение CSS-стилей, сгенерированных Pygments
        pygments_css = formatter.get_style_defs('.highlight')

        for file_path in files:
            relative_path = str(file_path.relative_to(target_dir))
            try:
                content = content_reader(file_path)
                
                # Интеллектуальное определение языка программирования
                try:
                    lexer = get_lexer_for_filename(file_path.name)
                except ClassNotFound:
                    lexer = TextLexer() # Fallback для неизвестных расширений
                    
                # Генерация HTML-разметки с подсветкой синтаксиса
                highlighted_content = highlight(content, lexer, formatter)
                
            except Exception as e:
                highlighted_content = f"<div class='highlight'><pre>[Ошибка обработки: {e}]</pre></div>"
                
            file_data.append({"path": relative_path, "content": highlighted_content})
            
        return template.render(
            project_name=target_dir.name, 
            files=file_data, 
            pygments_css=pygments_css
        )