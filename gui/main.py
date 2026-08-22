import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from gui.views.main_view import MainView

class MainWindow(QMainWindow):
    """Главное окно графического интерфейса пользователя."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Project Aggregator")
        self.resize(700, 450)
        self.setMinimumSize(500, 350)
        
        # Загрузка системной иконки из рабочей директории assets/
        icon_path = Path("assets/app_icon.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.main_view = MainView(self)
        self.setCentralWidget(self.main_view)

def run_gui() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())