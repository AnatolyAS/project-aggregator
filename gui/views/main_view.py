from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QComboBox, QFileDialog, QMessageBox, QCheckBox
)
from PySide6.QtCore import Qt

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

        # 2. Фильтр расширений
        layout.addWidget(QLabel("Фильтр расширений (через запятую, оставьте пустым для всех):", self))
        self.ext_input = QLineEdit(self)
        self.ext_input.setPlaceholderText("Например: py, md, json")
        layout.addWidget(self.ext_input)

        # 3. Метод форматирования и сжатие
        method_layout = QHBoxLayout()
        
        method_vbox = QVBoxLayout()
        method_vbox.addWidget(QLabel("Метод форматирования:", self))
        self.method_combo = QComboBox(self)
        for method in ConsolidationMethod:
            self.method_combo.addItem(method.value.replace("_", " ").title(), method)
        method_vbox.addWidget(self.method_combo)
        
        compress_vbox = QVBoxLayout()
        compress_vbox.addWidget(QLabel("Оптимизация для LLM:", self))
        self.compress_checkbox = QCheckBox("Сжать код (удалить пустые строки)", self)
        compress_vbox.addWidget(self.compress_checkbox)
        
        method_layout.addLayout(method_vbox)
        method_layout.addSpacing(20)
        method_layout.addLayout(compress_vbox)
        method_layout.addStretch()
        
        layout.addLayout(method_layout)

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
        self.method_combo.currentIndexChanged.connect(self._on_method_changed)
        # НОВОЕ: Отслеживание изменения чекбокса сжатия
        self.compress_checkbox.toggled.connect(self._on_compress_toggled)

    def _on_method_changed(self) -> None:
        current_path = Path(self.file_input.text())
        if not current_path.name:
            current_path = Path("aggregated_output")
            
        method: ConsolidationMethod = self.method_combo.currentData()
        ext_map = {
            ConsolidationMethod.MARKDOWN: ".md",
            ConsolidationMethod.PLAIN_TEXT: ".txt",
            ConsolidationMethod.JSON: ".json",
            ConsolidationMethod.HTML: ".html",
            ConsolidationMethod.PDF: ".pdf"
        }
        new_path = current_path.with_suffix(ext_map.get(method, ".txt"))
        self.file_input.setText(str(new_path))

    def _on_compress_toggled(self, checked: bool) -> None:
        """Добавляет или удаляет суффикс _compressed у имени файла."""
        current_path = Path(self.file_input.text())
        if not current_path.name:
            return

        stem = current_path.stem
        ext = current_path.suffix
        suffix = "_compressed"

        if checked and not stem.endswith(suffix):
            new_stem = f"{stem}{suffix}"
        elif not checked and stem.endswith(suffix):
            new_stem = stem[:-len(suffix)]
        else:
            return

        new_path = current_path.with_name(f"{new_stem}{ext}")
        self.file_input.setText(str(new_path))

    def _on_browse_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Выберите директорию проекта")
        if directory:
            self.dir_input.setText(directory)

    def _on_browse_file(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения результата")
        if directory:
            current_path = Path(self.file_input.text())
            current_file_name = current_path.name or "aggregated_output.md"
            new_full_path = Path(directory) / current_file_name
            self.file_input.setText(str(new_full_path.resolve()))

    def _on_run_aggregation(self) -> None:
        target_dir = self.dir_input.text()
        output_file = self.file_input.text()
        method: ConsolidationMethod = self.method_combo.currentData()
        compress = self.compress_checkbox.isChecked()
        
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
                allowed_extensions=allowed_exts,
                compress_code=compress
            )
            result_data = aggregator.aggregate()
            
            out_path = Path(output_file)
            token_info = ""
            
            if isinstance(result_data, bytes):
                out_path.write_bytes(result_data)
            else:
                out_path.write_text(result_data, encoding='utf-8')
                tokens = FileAggregator.count_tokens(result_data)
                token_info = f"\nКоличество токенов (gpt-4o): {tokens:,}"

            QMessageBox.information(
                self, 
                "Успех", 
                f"Агрегация успешно завершена!\nФайл сохранен:\n{out_path.resolve()}\n{token_info}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла ошибка при агрегации:\n{str(e)}")