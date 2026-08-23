from pathlib import Path
from typing import List, Callable
from jinja2 import Template
from .base import BaseFormatHandler

class HTMLHandler(BaseFormatHandler):
    """Отвечает за генерацию интерактивного HTML-отчета."""
    
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

    def generate(self, target_dir: Path, files: List[Path], content_reader: Callable[[Path], str]) -> str:
        template = Template(self.HTML_TEMPLATE)
        file_data = []
        for file_path in files:
            relative_path = str(file_path.relative_to(target_dir))
            try:
                content = content_reader(file_path)
            except Exception as e:
                content = f"[Ошибка чтения: {e}]"
            file_data.append({"path": relative_path, "content": content})
        return template.render(project_name=target_dir.name, files=file_data)