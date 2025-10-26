import asyncio
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QListWidget, QListWidgetItem, QDialogButtonBox,
    QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal

from ...infrastructure.storage.google_drive_storage import GoogleDriveStorage


class FileLoaderThread(QThread):
    """
    Потік для асинхронного завантаження списку файлів.
    """
    files_loaded = Signal(list)  # Сигнал з списком файлів
    error_occurred = Signal(str)  # Сигнал помилки

    def __init__(self, drive_storage: GoogleDriveStorage):
        super().__init__()
        self.drive_storage = drive_storage

    def run(self):
        """Виконує завантаження списку файлів."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            files = loop.run_until_complete(
                self.drive_storage.list_spreadsheets()
            )

            loop.close()

            self.files_loaded.emit(files)

        except Exception as e:
            self.error_occurred.emit(str(e))


class DriveFileSelectorDialog(QDialog):
    """
    Діалог для вибору Google Sheets файлу з Google Drive.

    Показує список доступних файлів та дозволяє користувачу вибрати один.
    """

    def __init__(self, drive_storage: GoogleDriveStorage, parent=None):
        """
        Ініціалізує діалог вибору файлу.

        Args:
            drive_storage: Сервіс Google Drive
            parent: Батьківський віджет
        """
        super().__init__(parent)
        self.drive_storage = drive_storage
        self.files: list[dict] = []
        self.selected_file: dict | None = None
        self._loader_thread: FileLoaderThread | None = None
        self._setup_ui()
        self._load_files()

    def _setup_ui(self):
        self.setWindowTitle("Вибрати файл з Google Drive")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout()

        title = QLabel("<h3>Ваші Google Sheets файли</h3>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Progress bar для завантаження
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) 
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.info_label = QLabel("Завантаження файлів...")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.info_label)

        self.file_list = QListWidget()
        self.file_list.setEnabled(False)
        self.file_list.itemDoubleClicked.connect(self._on_file_double_clicked)
        layout.addWidget(self.file_list)

        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        self.ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setEnabled(False)
        self.ok_button.setText("Вибрати")
        button_box.accepted.connect(self._on_ok_clicked)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def _load_files(self):
        """Завантажує список файлів з Google Drive."""
        self.progress_bar.setVisible(True)
        self.info_label.setText("Завантаження файлів з Google Drive...")
        self.file_list.setEnabled(False)

        self._loader_thread = FileLoaderThread(self.drive_storage)
        self._loader_thread.files_loaded.connect(self._on_files_loaded)
        self._loader_thread.error_occurred.connect(self._on_error)
        self._loader_thread.start()

    def _on_files_loaded(self, files: list[dict]):
        """
        Обробник успішного завантаження файлів.

        Args:
            files: Список файлів
        """
        self.progress_bar.setVisible(False)
        self.files = files

        if not files:
            self.info_label.setText("Файлів не знайдено. Створіть новий файл в Google Sheets.")
            return

        self.info_label.setVisible(False)
        self.file_list.setEnabled(True)
        self.ok_button.setEnabled(True)

        for file in files:
            item = QListWidgetItem()

            modified_time = self._format_datetime(file.get('modifiedTime', ''))

            item.setText(f"{file['name']}\n  Змінено: {modified_time}")
            item.setData(Qt.ItemDataRole.UserRole, file)

            self.file_list.addItem(item)

        if self.file_list.count() > 0:
            self.file_list.setCurrentRow(0)

    def _on_error(self, error_message: str):
        """
        Обробник помилки завантаження.

        Args:
            error_message: Повідомлення про помилку
        """
        self.progress_bar.setVisible(False)
        self.info_label.setText("Помилка при завантаженні файлів")

        QMessageBox.critical(
            self,
            "Помилка",
            f"Не вдалося завантажити список файлів:\n{error_message}"
        )

    def _format_datetime(self, datetime_str: str) -> str:
        """
        Форматує дату та час у читабельний вигляд.

        Args:
            datetime_str: Рядок з датою в ISO форматі

        Returns:
            Відформатована дата
        """
        if not datetime_str:
            return "Невідомо"

        try:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.strftime('%d.%m.%Y %H:%M')
        except Exception:
            return datetime_str

    def _on_file_double_clicked(self, item: QListWidgetItem):
        """
        Обробник подвійного кліку на файлі.

        Args:
            item: Елемент списку
        """
        self._on_ok_clicked()

    def _on_ok_clicked(self):
        """Обробник натискання кнопки OK."""
        current_item = self.file_list.currentItem()
        if current_item:
            self.selected_file = current_item.data(Qt.ItemDataRole.UserRole)
            self.accept()

    def get_selected_file(self) -> dict | None:
        """
        Повертає вибраний файл.

        Returns:
            dict або None: Інформація про вибраний файл
                - id: ID файлу
                - name: Назва файлу
                - modifiedTime: Час модифікації
        """
        return self.selected_file
