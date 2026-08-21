import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt

from gui.views.main_view import MainView


class MainWindow(QMainWindow):
    """Главное окно графического интерфейса пользователя.

    Служит контейнером для основного представления (MainView). Отвечает за
    настройку геометрии окна и общих параметров приложения.
    """

    def __init__(self) -> None:
        """Инициализирует главное окно и устанавливает MainView как центральный виджет."""
        super().__init__()
        self.setWindowTitle("Project Aggregator")
        self.resize(700, 450)
        self.setMinimumSize(500, 350)

        # Установка функционального виджета в качестве центрального элемента
        self.main_view = MainView(self)
        self.setCentralWidget(self.main_view)


def run_gui() -> None:
    """Инициализирует и запускает цикл обработки событий графического интерфейса.

    Создает экземпляр QApplication, применяет системные стили и отображает
    главное окно приложения. Блокирует выполнение до закрытия окна.
    """
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())