from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QComboBox, QFileDialog, QMessageBox
)

from core.aggregator import FileAggregator, ConsolidationMethod

class MainView(QWidget):
    """Главный виджет (представление) для управления процессом агрегации."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. Целевая директория
        layout.addWidget(QLabel("Целевая директория проекта:", self))
        dir_layout = QHBoxLayout()
        self.dir_input = QLineEdit(self)
        self.dir_input.setPlaceholderText("Выберите папку для агрегации...")
        self.dir_input.setReadOnly(True)
        self.btn_browse_dir = QPushButton("Обзор...", self)
        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(self.btn_browse_dir)
        layout.addLayout(dir_layout)

        # 2. Фильтр расширений (НОВОЕ)
        layout.addWidget(QLabel("Фильтр расширений (через запятую, оставьте пустым для всех):", self))
        self.ext_input = QLineEdit(self)
        self.ext_input.setPlaceholderText("Например: py, md, json")
        layout.addWidget(self.ext_input)

        # 3. Выбор метода агрегации
        layout.addWidget(QLabel("Метод форматирования:", self))
        self.method_combo = QComboBox(self)
        for method in ConsolidationMethod:
            self.method_combo.addItem(method.value.replace("_", " ").title(), method)
        layout.addWidget(self.method_combo)

        # 4. Файл сохранения
        layout.addWidget(QLabel("Файл для сохранения результата:", self))
        file_layout = QHBoxLayout()
        self.file_input = QLineEdit(self)
        self.file_input.setText(str(Path.cwd() / "aggregated_output.md"))
        self.btn_browse_file = QPushButton("Обзор...", self)
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(self.btn_browse_file)
        layout.addLayout(file_layout)

        layout.addStretch()

        # 5. Кнопка запуска
        self.btn_run = QPushButton("Запустить агрегацию", self)
        self.btn_run.setMinimumHeight(40)
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
        self.btn_browse_dir.clicked.connect(self._on_browse_dir)
        self.btn_browse_file.clicked.connect(self._on_browse_file)
        self.btn_run.clicked.connect(self._on_run_aggregation)

    def _on_browse_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Выберите директорию проекта")
        if directory:
            self.dir_input.setText(directory)

    def _on_browse_file(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Сохранить результат как", 
            self.file_input.text(),
            "All Files (*.*);;Markdown (*.md);;Text (*.txt);;JSON (*.json);;HTML (*.html);;PDF (*.pdf)"
        )
        if file_path:
            self.file_input.setText(file_path)

    def _on_run_aggregation(self) -> None:
        target_dir = self.dir_input.text()
        output_file = self.file_input.text()
        method: ConsolidationMethod = self.method_combo.currentData()
        
        # Обработка введенных расширений
        raw_exts = self.ext_input.text().strip()
        allowed_exts = [e.strip() for e in raw_exts.split(',')] if raw_exts else None

        if not target_dir:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, выберите целевую директорию.")
            return
        if not output_file:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, укажите файл для сохранения.")
            return

        try:
            aggregator = FileAggregator(
                target_dir=target_dir, 
                method=method,
                allowed_extensions=allowed_exts
            )
            result_data = aggregator.aggregate()
            
            out_path = Path(output_file)
            
            if isinstance(result_data, bytes):
                out_path.write_bytes(result_data)
            else:
                out_path.write_text(result_data, encoding='utf-8')

            QMessageBox.information(
                self, 
                "Успех", 
                f"Агрегация успешно завершена!\nФайл сохранен:\n{out_path.resolve()}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла ошибка при агрегации:\n{str(e)}")