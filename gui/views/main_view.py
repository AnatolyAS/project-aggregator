from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QComboBox, QFileDialog, QMessageBox, QCheckBox, QApplication
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPalette, QColor

from core.aggregator import FileAggregator, ConsolidationMethod

class MainView(QWidget):
    """Главный виджет (представление) для управления процессом агрегации."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        # Включение поддержки механизма перетаскивания (Drag-and-Drop)
        self.setAcceptDrops(True)
        # Инициализация хранилища настроек пользователя
        self.settings = QSettings("Personal", "ProjectAggregator")
        
        self._setup_ui()
        self._connect_signals()
        self._load_settings()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. Верхняя панель (Заголовок + Переключатель темы)
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Целевая директория (можно перетащить папку в окно):", self))
        top_layout.addStretch()
        self.theme_checkbox = QCheckBox("Темная тема", self)
        top_layout.addWidget(self.theme_checkbox)
        layout.addLayout(top_layout)

        # Целевая директория (поля)
        dir_layout = QHBoxLayout()
        self.dir_input = QLineEdit(self)
        self.dir_input.setPlaceholderText("Выберите или перетащите папку (Drag-and-Drop)...")
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
        self.compress_checkbox.toggled.connect(self._on_compress_toggled)
        self.theme_checkbox.toggled.connect(self._on_theme_toggled)

    # --- Подсистема настроек (QSettings) ---
    def _load_settings(self) -> None:
        """Загружает сохраненные настройки пользователя при запуске."""
        self.dir_input.setText(self.settings.value("target_dir", ""))
        self.file_input.setText(self.settings.value("output_file", str(Path.cwd() / "aggregated_output.md")))
        self.ext_input.setText(self.settings.value("extensions", ""))
        
        method_val = self.settings.value("method", ConsolidationMethod.MARKDOWN.value)
        for i in range(self.method_combo.count()):
            if self.method_combo.itemData(i).value == method_val:
                self.method_combo.setCurrentIndex(i)
                break
                
        self.compress_checkbox.setChecked(self.settings.value("compress", False, type=bool))
        
        is_dark = self.settings.value("dark_theme", False, type=bool)
        self.theme_checkbox.setChecked(is_dark)
        self._apply_theme(is_dark)

    def _save_settings(self) -> None:
        """Сохраняет текущие параметры в реестр/конфиг ОС."""
        self.settings.setValue("target_dir", self.dir_input.text())
        self.settings.setValue("output_file", self.file_input.text())
        self.settings.setValue("extensions", self.ext_input.text())
        self.settings.setValue("method", self.method_combo.currentData().value)
        self.settings.setValue("compress", self.compress_checkbox.isChecked())
        self.settings.setValue("dark_theme", self.theme_checkbox.isChecked())

    # --- Управление темой оформления ---
    def _on_theme_toggled(self, checked: bool) -> None:
        self._apply_theme(checked)
        self._save_settings()

    def _apply_theme(self, is_dark: bool) -> None:
        """Применяет системную светлую или нативную темную палитру."""
        app = QApplication.instance()
        if not app: return
        
        if is_dark:
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.WindowText, Qt.white)
            palette.setColor(QPalette.Base, QColor(25, 25, 25))
            palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ToolTipBase, Qt.white)
            palette.setColor(QPalette.ToolTipText, Qt.white)
            palette.setColor(QPalette.Text, Qt.white)
            palette.setColor(QPalette.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ButtonText, Qt.white)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.HighlightedText, Qt.black)
            app.setPalette(palette)
        else:
            app.setPalette(app.style().standardPalette())

    # --- Поддержка Drag-and-Drop ---
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if urls:
            path = Path(urls[0].toLocalFile())
            # Если пользователь перетащил файл, берем его родительскую папку
            if path.is_file():
                path = path.parent
            if path.is_dir():
                self.dir_input.setText(str(path))
                self._save_settings()

    # --- Стандартные обработчики ---
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
        self._save_settings()

    def _on_compress_toggled(self, checked: bool) -> None:
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
        self._save_settings()

    def _on_browse_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Выберите директорию проекта")
        if directory:
            self.dir_input.setText(directory)
            self._save_settings()

    def _on_browse_file(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения результата")
        if directory:
            current_path = Path(self.file_input.text())
            current_file_name = current_path.name or "aggregated_output.md"
            new_full_path = Path(directory) / current_file_name
            self.file_input.setText(str(new_full_path.resolve()))
            self._save_settings()

    def _on_run_aggregation(self) -> None:
        self._save_settings() # Принудительное сохранение перед запуском
        
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