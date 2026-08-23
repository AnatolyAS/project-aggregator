import json
from pathlib import Path
from typing import List, Dict, Any, Callable
from .base import BaseFormatHandler

class JSONHandler(BaseFormatHandler):
    """Отвечает за формирование структурированного JSON-объекта."""
    
    def generate(self, target_dir: Path, files: List[Path], content_reader: Callable[[Path], str]) -> str:
        data: Dict[str, Any] = {"project_name": target_dir.name, "files": []}
        for file_path in files:
            relative_path = str(file_path.relative_to(target_dir))
            try:
                content = content_reader(file_path)
                status = "success"
            except Exception as e:
                content = str(e)
                status = "error"
            data["files"].append({
                "path": relative_path, "extension": file_path.suffix, 
                "status": status, "content": content
            })
        return json.dumps(data, ensure_ascii=False, indent=4)