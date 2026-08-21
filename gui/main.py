import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class MainWindow(QMainWindow):
    """Главное окно графического интерфейса пользователя.

    Реализует эстетичный базовый каркас приложения (GUI). Включает настройку
    размеров, центрирование контента и применение современных типографических
    стандартов.
    """

    def __init__(self) -> None:
        """Инициализирует экземпляр главного окна, настраивая его геометрию и стили."""
        super().__init__()
        self.setWindowTitle("Project Aggregator")
        self.resize(900, 600)
        self.setMinimumSize(600, 400)

        # Создание центрального виджета и компоновщика
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Приветственная надпись с использованием эстетичной типографики
        welcome_label = QLabel("Project Aggregator", self)
        
        # Настройка шрифта для заголовка
        font = QFont("Segoe UI", 24)
        font.setBold(True)
        welcome_label.setFont(font)
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Информационная подпись
        subtitle_label = QLabel("Утилита для профессиональной консолидации файлов", self)
        subtitle_font = QFont("Segoe UI", 12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: gray;")

        layout.addWidget(welcome_label)
        layout.addWidget(subtitle_label)


def run_gui() -> None:
    """Инициализирует и запускает цикл обработки событий графического интерфейса.

    Создает экземпляр QApplication, применяет базовые системные стили и
    отображает главное окно приложения. Блокирует выполнение до закрытия окна.
    """
    app = QApplication(sys.argv)
    
    # Принудительное использование современного системного стиля (Fusion)
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())