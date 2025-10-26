import asyncio
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QInputDialog,
    QMessageBox,
    QStatusBar,
    QDialog,
)
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Qt, QThread, Signal

from src.application.services.table_service import TableService
from src.domain.value_objects import CellReference
from src.infrastructure.logging.logging_factory import LoggingFactory
from src.infrastructure.storage.file_storage import FileStorage
from src.infrastructure.auth.google_auth_service import GoogleAuthService
from src.infrastructure.storage.google_drive_storage import GoogleDriveStorage
from ..dialogs.help_dialog import HelpDialog
from ..dialogs.storage_choice_dialog import StorageChoiceDialog, StorageType
from ..dialogs.drive_file_selector_dialog import DriveFileSelectorDialog
from ..dialogs.file_name_dialog import FileNameDialog
from .table_widget import TableWidget


class DriveDownloadThread(QThread):
    """Потік для асинхронного завантаження файлу з Google Drive."""
    download_completed = Signal(dict)  # Сигнал з даними
    error_occurred = Signal(str)  # Сигнал помилки

    def __init__(self, drive_storage: GoogleDriveStorage, file_id: str):
        super().__init__()
        self.drive_storage = drive_storage
        self.file_id = file_id

    def run(self):
        """Виконує завантаження файлу."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            data = loop.run_until_complete(
                self.drive_storage.download_spreadsheet(self.file_id)
            )

            loop.close()
            self.download_completed.emit(data)

        except Exception as e:
            self.error_occurred.emit(str(e))


class DriveUploadThread(QThread):
    """Потік для асинхронного завантаження файлу на Google Drive."""
    upload_completed = Signal(str)  # Сигнал з ID файлу
    error_occurred = Signal(str)  # Сигнал помилки

    def __init__(
        self,
        drive_storage: GoogleDriveStorage,
        data: dict,
        file_name: str,
        file_id: str | None = None
    ):
        super().__init__()
        self.drive_storage = drive_storage
        self.data = data
        self.file_name = file_name
        self.file_id = file_id

    def run(self):
        """Виконує завантаження файлу."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            file_id = loop.run_until_complete(
                self.drive_storage.upload_spreadsheet(
                    self.data,
                    self.file_name,
                    self.file_id
                )
            )

            loop.close()
            self.upload_completed.emit(file_id)

        except Exception as e:
            self.error_occurred.emit(str(e))


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.logger = LoggingFactory.get_logger(__name__)

        # Services
        self.table_service = TableService()
        self.file_storage = FileStorage()
        self.current_file: Path | None = None

        # Google Drive services 
        self._google_auth_service: GoogleAuthService | None = None
        self._google_drive_storage: GoogleDriveStorage | None = None
        self._current_drive_file_id: str | None = None

        # Window settings
        self.setWindowTitle("Python Sheets")
        self.resize(1150, 700)

        # UI
        self._create_table_widget()
        self._create_toolbar()
        self._create_statusbar()

        self.logger.info("Головне вікно ініціалізоване")

    def _create_table_widget(self) -> None:
        """Створює widget таблиці."""
        self.table_widget = TableWidget(self.table_service, self)
        self.setCentralWidget(self.table_widget)

        # Connecting signals
        self.table_widget.cell_changed.connect(self._on_cell_changed)


    def _create_toolbar(self) -> None:
        """Створює панель інструментів."""
        toolbar = self.addToolBar("Головна панель")

        # Нова таблиця
        new_action = QAction("Нова", self)
        new_action.triggered.connect(self._on_new)
        toolbar.addAction(new_action)

        # Відкрити
        open_action = QAction("Відкрити", self)
        open_action.triggered.connect(self._on_open)
        toolbar.addAction(open_action)

        # Зберегти
        save_action = QAction("Зберегти", self)
        save_action.triggered.connect(self._on_save)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        # Змінити розмір
        resize_action = QAction("Змінити розмір", self)
        resize_action.triggered.connect(self._on_resize)
        toolbar.addAction(resize_action)

        # Очистити
        clear_action = QAction("Очистити", self)
        clear_action.triggered.connect(self._on_clear)
        toolbar.addAction(clear_action)

        toolbar.addSeparator()

        # Перемикач режиму відображення
        self.toggle_display_action = QAction("Показувати вирази", self)
        self.toggle_display_action.setCheckable(True)
        self.toggle_display_action.setChecked(False)
        self.toggle_display_action.triggered.connect(self._on_toggle_display)
        toolbar.addAction(self.toggle_display_action)

        toolbar.addSeparator()

        # Ресеттінг авторизації
        logout_action = QAction("Скинути авторизацію", self)
        logout_action.triggered.connect(self._logout)
        toolbar.addAction(logout_action)

        toolbar.addSeparator()

        # Інфа про додаток
        help_action = QAction("Про додаток", self)
        help_action.triggered.connect(self._on_help)
        toolbar.addAction(help_action)

    def _create_statusbar(self) -> None:
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self._update_statusbar()

    def _update_statusbar(self, message: str = "") -> None:
        """
        Оновлює рядок стану.

        Args:
            message: Повідомлення для відображення
        """
        if message:
            self.statusbar.showMessage(message, 3000)  # 3 секунди
        else:
            rows = self.table_service.table.rows
            cols = self.table_service.table.columns
            mode = "ВИРАЗ" if not self.table_widget.show_values else "ЗНАЧЕННЯ"
            self.statusbar.showMessage(f"Рядків: {rows} | Стовпчиків: {cols} | Режим: {mode}")

    def _on_new(self) -> None:
        """Обробляє створення нової таблиці."""
        # Питаємо розмір таблиці
        rows, ok1 = QInputDialog.getInt(
            self,
            "Нова таблиця",
            "Кількість рядків:",
            10, 1, 1000, 1
        )

        if not ok1:
            return

        cols, ok2 = QInputDialog.getInt(
            self,
            "Нова таблиця",
            "Кількість стовпчиків:",
            10, 1, 100, 1
        )

        if not ok2:
            return

        self.table_service.create_table(rows, cols)
        self.table_widget.resize_table(rows, cols)
        self.current_file = None
        self.setWindowTitle("Python Sheets - Нова таблиця")
        self._update_statusbar("Створено нову таблицю")

    def _on_open(self) -> None:
        """Обробляє відкриття файлу."""
        # Показуємо діалог вибору типу сховища
        storage_dialog = StorageChoiceDialog(self, "відкрити")
        if storage_dialog.exec() != QDialog.DialogCode.Accepted:
            return

        storage_type = storage_dialog.get_selected_storage()

        if storage_type == StorageType.GOOGLE_DRIVE:
            self._load_from_google_drive()
        else:
            self._load_from_local_file()

    def _load_from_local_file(self) -> None:
        """Завантажує файл з локальної файлової системи."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Відкрити таблицю",
            str(Path.home()),
            "JSON файли (*.json);;Всі файли (*)"
        )

        if not file_path:
            return

        try:
            data = self.file_storage.load(Path(file_path))
            self.table_service.load_table_data(data)

            rows = self.table_service.table.rows
            cols = self.table_service.table.columns

            # Оновлюємо тільки UI widget'а, без зміни даних сервісу
            self.table_widget.setRowCount(rows)
            self.table_widget.setColumnCount(cols)

            # Оновлюємо заголовки
            headers = [CellReference.from_indices(0, col).column for col in range(cols)]
            self.table_widget.setHorizontalHeaderLabels(headers)

            row_headers = [str(i + 1) for i in range(rows)]
            self.table_widget.setVerticalHeaderLabels(row_headers)

            # Встановлюємо висоту для всіх рядків
            for row in range(rows):
                self.table_widget.setRowHeight(row, 40)

            # Оновлюємо відображення після завантаження
            self.table_widget.refresh_display()

            self.current_file = Path(file_path)
            self._current_drive_file_id = None  # Скидаємо Google Drive ID
            self.setWindowTitle(f"Python Sheets - {self.current_file.name}")
            self._update_statusbar("Таблицю завантажено")

        except Exception as e:
            self.logger.error(f"Помилка відкриття файлу: {e}")
            QMessageBox.critical(
                self,
                "Помилка",
                f"Не вдалося відкрити файл:\n{e}"
            )

    def _on_save(self) -> None:
        """Обробляє збереження файлу."""
        # Якщо файл вже відкритий з Google Drive, зберігаємо туди
        if self._current_drive_file_id:
            title = self.windowTitle()
            file_name = title.replace("Python Sheets - ", "").replace(" (Google Drive)", "")
            self._upload_to_drive(file_name, self._current_drive_file_id)
        # Якщо відкрито локальний файл
        elif self.current_file is not None:
            self._save_to_file(self.current_file)
        # Інакше показуємо діалог "Зберегти як"
        else:
            self._on_save_as()

    def _on_save_as(self) -> None:
        """Обробляє збереження файлу з новим ім'ям."""

        storage_dialog = StorageChoiceDialog(self, "зберегти")
        if storage_dialog.exec() != QDialog.DialogCode.Accepted:
            return

        storage_type = storage_dialog.get_selected_storage()

        if storage_type == StorageType.GOOGLE_DRIVE:
            self._save_to_google_drive()
        else:
            self._save_as_local_file()

    def _save_as_local_file(self) -> None:
        """Зберігає файл у локальну файлову систему."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Зберегти таблицю",
            str(Path.home() / "table.json"),
            "JSON файли (*.json);;Всі файли (*)"
        )

        if not file_path:
            return

        self._save_to_file(Path(file_path))

    def _save_to_file(self, file_path: Path) -> None:
        """
        Зберігає таблицю у файл.

        Args:
            file_path: Шлях до файлу
        """
        try:
            data = self.table_service.get_table_data_for_export()
            self.file_storage.save(file_path, data)

            self.current_file = file_path
            self._current_drive_file_id = None  # Скидаємо Google Drive ID
            self.setWindowTitle(f"Python Sheets - {self.current_file.name}")
            self._update_statusbar("Таблицю збережено")

        except Exception as e:
            self.logger.error(f"Помилка збереження файлу: {e}")
            QMessageBox.critical(
                self,
                "Помилка",
                f"Не вдалося зберегти файл:\n{e}"
            )

    def _on_resize(self) -> None:
        """Обробляє зміну розміру таблиці."""
        current_rows = self.table_service.table.rows
        current_cols = self.table_service.table.columns

        rows, ok1 = QInputDialog.getInt(
            self,
            "Змінити розмір",
            "Кількість рядків:",
            current_rows, 1, 1000, 1
        )

        if not ok1:
            return

        cols, ok2 = QInputDialog.getInt(
            self,
            "Змінити розмір",
            "Кількість стовпчиків:",
            current_cols, 1, 100, 1
        )

        if not ok2:
            return

        self.table_widget.resize_table(rows, cols)
        self._update_statusbar("Розмір таблиці змінено")

    def _on_clear(self) -> None:
        """Обробляє очищення таблиці."""
        reply = QMessageBox.question(
            self,
            "Підтвердження",
            "Ви впевнені, що хочете очистити всю таблицю?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.table_widget.clear_table()
            self._update_statusbar("Таблицю очищено")

    def _on_toggle_display(self) -> None:
        """Обробляє перемикання режиму відображення."""
        self.table_widget.toggle_display_mode()

        if self.table_widget.show_values:
            self.toggle_display_action.setText("Показувати вирази")
            self.toggle_display_action.setChecked(False)
        else:
            self.toggle_display_action.setText("Показувати значення")
            self.toggle_display_action.setChecked(True)

        self._update_statusbar()

    def _on_help(self) -> None:
        """Відкриває діалог довідки."""
        dialog = HelpDialog(self)
        dialog.exec()

    def _on_cell_changed(self, row: int, col: int) -> None:
        """
        Обробляє зміну клітинки.

        Args:
            row: Рядок клітинки
            col: Стовпчик клітинки
        """
        self._update_statusbar()

    # Google Drive методи

    def _init_google_drive_services(self) -> bool:
        """
        Ініціалізує Google Drive сервіси та виконує автентифікацію.

        Returns:
            bool: True якщо успішно, False інакше
        """
        try:
            if not self._google_auth_service:
                self._google_auth_service = GoogleAuthService()

            # автентифікація
            self._google_auth_service.authenticate()

            if not self._google_drive_storage:
                self._google_drive_storage = GoogleDriveStorage(self._google_auth_service)

            return True

        except FileNotFoundError as e:
            QMessageBox.warning(
                self,
                "Відсутній файл налаштувань",
                "Помістіть credentials.json в папку проекту."
            )
            return False

        except Exception as e:
            self.logger.error(f"Помилка ініціалізації Google Drive: {e}")
            QMessageBox.critical(
                self,
                "Помилка автентифікації",
                f"Не вдалося автентифікуватися в Google:\n{e}"
            )
            return False

    def _load_from_google_drive(self) -> None:
        """Завантажує файл з Google Drive."""
        if not self._init_google_drive_services():
            return

        dialog = DriveFileSelectorDialog(self._google_drive_storage, self) # type: ignore
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        selected_file = dialog.get_selected_file()
        if not selected_file:
            return

        self._download_from_drive(selected_file['id'], selected_file['name'])

    def _download_from_drive(self, file_id: str, file_name: str) -> None:
        """
        Завантажує дані з Google Drive.

        Args:
            file_id: ID файлу
            file_name: Назва файлу
        """
        self._update_statusbar("Завантаження з Google Drive...")

        # завантаження в окремому потоці
        thread = DriveDownloadThread(self._google_drive_storage, file_id) # type: ignore
        thread.download_completed.connect(
            lambda data: self._on_drive_download_completed(data, file_id, file_name)
        )
        thread.error_occurred.connect(self._on_drive_error)
        thread.start()

        # Зберігаємо посилання на потік, щоб він не був видалений
        self._download_thread = thread

    def _on_drive_download_completed(self, data: dict, file_id: str, file_name: str) -> None:
        """
        Обробник успішного завантаження з Google Drive.

        Args:
            data: Дані таблиці
            file_id: ID файлу
            file_name: Назва файлу
        """
        try:
            self.table_service.load_table_data(data)

            rows = self.table_service.table.rows
            cols = self.table_service.table.columns

            self.table_widget.setRowCount(rows)
            self.table_widget.setColumnCount(cols)

            headers = [CellReference.from_indices(0, col).column for col in range(cols)]
            self.table_widget.setHorizontalHeaderLabels(headers)

            row_headers = [str(i + 1) for i in range(rows)]
            self.table_widget.setVerticalHeaderLabels(row_headers)

            for row in range(rows):
                self.table_widget.setRowHeight(row, 40)

            self.table_widget.refresh_display()

            self._current_drive_file_id = file_id
            self.current_file = None  

            self.setWindowTitle(f"Python Sheets - {file_name} (Google Drive)")
            self._update_statusbar("Таблицю завантажено з Google Drive")

        except Exception as e:
            self.logger.error(f"Помилка обробки даних з Google Drive: {e}")
            QMessageBox.critical(
                self,
                "Помилка",
                f"Не вдалося завантажити дані:\n{e}"
            )

    def _save_to_google_drive(self) -> None:
        """Зберігає файл на Google Drive."""
        if not self._init_google_drive_services():
            return

        current_name = ""
        if self.current_file:
            current_name = self.current_file.stem

        dialog = FileNameDialog(self, current_name)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        file_name = dialog.get_file_name()
        if not file_name:
            return

        self._upload_to_drive(file_name)

    def _upload_to_drive(self, file_name: str, file_id: str | None = None) -> None:
        """
        Завантажує дані на Google Drive.

        Args:
            file_name: Назва файлу
            file_id: ID файлу для оновлення (None для нового файлу)
        """
        self._update_statusbar("Завантаження на Google Drive...")

        data = self.table_service.get_table_data_for_export()

        thread = DriveUploadThread(
            self._google_drive_storage, # type: ignore
            data,
            file_name,
            file_id or self._current_drive_file_id
        )
        thread.upload_completed.connect(
            lambda new_file_id: self._on_drive_upload_completed(new_file_id, file_name)
        )
        thread.error_occurred.connect(self._on_drive_error)
        thread.start()

        # Зберігаємо посилання на потік
        self._upload_thread = thread

    def _on_drive_upload_completed(self, file_id: str, file_name: str) -> None:
        """
        Обробник успішного завантаження на Google Drive.

        Args:
            file_id: ID створеного/оновленого файлу
            file_name: Назва файлу
        """
        self._current_drive_file_id = file_id
        self.current_file = None  

        self.setWindowTitle(f"Python Sheets - {file_name} (Google Drive)")
        self._update_statusbar("Таблицю збережено на Google Drive")

        QMessageBox.information(
            self,
            "Успіх",
            f"Файл '{file_name}' успішно збережено на Google Drive!"
        )

    def _on_drive_error(self, error_message: str) -> None:
        """
        Обробник помилки роботи з Google Drive.

        Args:
            error_message: Повідомлення про помилку
        """
        self._update_statusbar("Помилка роботи з Google Drive")

        QMessageBox.critical(
            self,
            "Помилка Google Drive",
            f"Виникла помилка:\n{error_message}"
        )


    def _logout(self):
        try:
            if not self._google_auth_service:
                self._google_auth_service = GoogleAuthService()

            self._google_auth_service.logout()

            if self._google_drive_storage:
                self._google_drive_storage.reset_services()

            QMessageBox.information(
                self,
                "Успіх",
                f"Потрібно буде повторно авторизуватись при спробі завантаження/збереження файлів з Google Drive."
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Помилка при видаленні токена сесії",
                f"Виникла помилка:\n{str(e)}"
            )
