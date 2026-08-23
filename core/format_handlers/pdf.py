import urllib.request
from pathlib import Path
from typing import List, Callable
from fpdf import FPDF
from .base import BaseFormatHandler

class PDFHandler(BaseFormatHandler):
    """Отвечает за генерацию документа в формате PDF с поддержкой кириллицы."""
    
    def _ensure_pdf_font(self) -> Path:
        font_path = Path("assets") / "Roboto-Regular.ttf"
        font_path.parent.mkdir(parents=True, exist_ok=True)
        if not font_path.exists():
            font_url = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf"
            urllib.request.urlretrieve(font_url, font_path)
        return font_path

    def generate(self, target_dir: Path, files: List[Path], content_reader: Callable[[Path], str]) -> bytes:
        font_path = self._ensure_pdf_font()
        pdf = FPDF()
        pdf.add_font("Roboto", "", str(font_path), uni=True)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        pdf.set_font("Roboto", size=14)
        pdf.cell(0, 10, f"Проект: {target_dir.name}", ln=True, align='C')
        pdf.ln(10)
        
        pdf.set_font("Roboto", size=10)
        for file_path in files:
            relative_path = str(file_path.relative_to(target_dir))
            pdf.set_font("Roboto", size=12)
            pdf.cell(0, 10, f"--- {relative_path} ---", ln=True, fill=False)
            pdf.set_font("Roboto", size=8)
            try:
                content = content_reader(file_path)
            except Exception as e:
                content = f"[Ошибка чтения: {e}]"
            pdf.multi_cell(0, 5, content)
            pdf.ln(5)
            
        return bytes(pdf.output())