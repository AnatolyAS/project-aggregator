from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QComboBox, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt

from core.aggregator import FileAggregator, ConsolidationMethod


class MainView(QWidget):
    """Главный виджет (представление) для управления процессом агрегации.

    Содержит элементы пользовательского интерфейса (поля ввода, кнопки, выпадающие
    списки) для выбора целевой директории, файла сохранения и метода форматирования.
    Обеспечивает связывание графического интерфейса с бизнес-логикой ядра.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Инициализирует виджет, выстраивает сетку элементов и подключает сигналы."""
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Создает и размещает элементы управления на макете виджета."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. Выбор целевой директории
        layout.addWidget(QLabel("Целевая директория проекта:", self))
        dir_layout = QHBoxLayout()
        self.dir_input = QLineEdit(self)
        self.dir_input.setPlaceholderText("Выберите папку для агрегации...")
        self.dir_input.setReadOnly(True)
        self.btn_browse_dir = QPushButton("Обзор...", self)
        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(self.btn_browse_dir)
        layout.addLayout(dir_layout)

        # 2. Выбор выходного файла
        layout.addWidget(QLabel("Файл для сохранения результата:", self))
        file_layout = QHBoxLayout()
        self.file_input = QLineEdit(self)
        self.file_input.setText(str(Path.cwd() / "aggregated_output.md"))
        self.btn_browse_file = QPushButton("Обзор...", self)
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(self.btn_browse_file)
        layout.addLayout(file_layout)

        # 3. Выбор метода агрегации
        layout.addWidget(QLabel("Метод форматирования:", self))
        self.method_combo = QComboBox(self)
        for method in ConsolidationMethod:
            # Добавляем элементы, используя значение enum как текст, а сам enum как скрытые данные
            self.method_combo.addItem(method.value.replace("_", " ").title(), method)
        layout.addWidget(self.method_combo)

        layout.addStretch()

        # 4. Кнопка запуска
        self.btn_run = QPushButton("Запустить агрегацию", self)
        self.btn_run.setMinimumHeight(40)
        # Применение базового CSS-стиля для акцентной кнопки
        self.btn_run.setStyleSheet("""
            QPushButton {
                background-color: #0078D7;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #1084ea; }
            QPushButton:pressed { background-color: #006cc1; }
        """)
        layout.addWidget(self.btn_run)

    def _connect_signals(self) -> None:
        """Связывает события кнопок (клики) с соответствующими методами-обработчиками."""
        self.btn_browse_dir.clicked.connect(self._on_browse_dir)
        self.btn_browse_file.clicked.connect(self._on_browse_file)
        self.btn_run.clicked.connect(self._on_run_aggregation)

    def _on_browse_dir(self) -> None:
        """Открывает диалоговое окно для выбора целевой директории."""
        directory = QFileDialog.getExistingDirectory(self, "Выберите директорию проекта")
        if directory:
            self.dir_input.setText(directory)

    def _on_browse_file(self) -> None:
        """Открывает диалоговое окно для выбора пути сохранения файла."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Сохранить результат как", 
            self.file_input.text(),
            "All Files (*.*);;Markdown (*.md);;Text (*.txt);;JSON (*.json)"
        )
        if file_path:
            self.file_input.setText(file_path)

    def _on_run_aggregation(self) -> None:
        """Инициирует процесс агрегации при нажатии на кнопку запуска.

        Считывает данные из полей ввода, инициализирует ядро FileAggregator,
        выполняет сбор данных, записывает их в файл и выводит окно с результатом.
        """
        target_dir = self.dir_input.text()
        output_file = self.file_input.text()
        method: ConsolidationMethod = self.method_combo.currentData()

        if not target_dir:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, выберите целевую директорию.")
            return
        if not output_file:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, укажите файл для сохранения.")
            return

        try:
            # Инициализация ядра
            aggregator = FileAggregator(target_dir=target_dir, method=method)
            
            # Выполнение консолидации
            result_data = aggregator.aggregate()
            
            # Запись результата
            out_path = Path(output_file)
            out_path.write_text(result_data, encoding='utf-8')

            QMessageBox.information(
                self, 
                "Успех", 
                f"Агрегация успешно завершена!\nФайл сохранен:\n{out_path.resolve()}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла ошибка при агрегации:\n{str(e)}")