from pathlib import Path
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QImage, QPainter
from PySide6.QtCore import Qt, QSize
from PIL import Image

def generate_icons() -> None:
    """Генерирует многоуровневый файл ICO для Windows.

    Читает мастер-иконку (assets/master.svg), осуществляет глубокое векторное
    масштабирование в промежуточные PNG-файлы и компилирует их в windows.ico.
    """
    assets_dir = Path("assets")
    master_svg = assets_dir / "master.svg"
    
    if not master_svg.exists():
        print(f"Ошибка: Мастер-иконка не найдена по пути {master_svg.resolve()}")
        return

    # 1. Рендеринг SVG в PNG заданных размеров
    sizes = [16, 24, 32, 48, 64, 96, 128, 256, 512]
    renderer = QSvgRenderer(str(master_svg))
    png_images = []

    print("[*] Запуск глубокого векторного масштабирования...")
    for size in sizes:
        img = QImage(QSize(size, size), QImage.Format_ARGB32_Premultiplied)
        img.fill(Qt.transparent)
        
        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing)
        renderer.render(painter)
        painter.end()

        png_path = assets_dir / f"icon_{size}x{size}.png"
        img.save(str(png_path), "PNG")
        
        png_images.append(Image.open(png_path))
        print(f"  - Сгенерирован слой: {size}x{size}px")

    # 2. Компиляция в многоуровневый ICO
    ico_path = assets_dir / "windows.ico"
    png_images[0].save(
        ico_path,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=png_images[1:]
    )
    print(f"[+] Многоуровневый файл {ico_path.name} успешно скомпилирован.")

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    generate_icons()