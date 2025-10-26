from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QDialogButtonBox
)
from PySide6.QtCore import Qt
from enum import Enum


class StorageType(Enum):
    """Тип сховища для файлів."""
    LOCAL = "local"
    GOOGLE_DRIVE = "google_drive"


class StorageChoiceDialog(QDialog):
    """
    Діалог для вибору типу сховища.

    Користувач може вибрати між:
    - Локальною файловою системою
    - Google Drive
    """

    def __init__(self, parent=None, operation: str = "відкрити"):
        """
        Ініціалізує діалог вибору сховища.

        Args:
            parent: Батьківський віджет
            operation: Назва операції ("відкрити" або "зберегти")
        """
        super().__init__(parent)
        self.operation = operation
        self.selected_storage: StorageType = StorageType.LOCAL
        self._setup_ui()

    def _setup_ui(self):
        """Налаштовує інтерфейс діалогу."""
        self.setWindowTitle(f"Вибрати джерело для {self.operation}")
        self.setMinimumWidth(400)

        layout = QVBoxLayout()

        # Заголовок
        title = QLabel(f"<h3>Оберіть, звідки {self.operation} файл:</h3>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Кнопки вибору
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(15)

        local_container = QVBoxLayout()
        local_container.setSpacing(5)

        local_btn = QPushButton("💾  Локальна файлова система")
        local_btn.setMinimumHeight(60)
        local_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 10px;
                text-align: left;
                border: 2px solid #2196F3;
                border-radius: 5px;
                color: black;
                background-color: white;
            }
            QPushButton:hover {
                background-color: #E3F2FD;
            }
        """)
        local_btn.clicked.connect(self._on_local_clicked)
        local_container.addWidget(local_btn)

        local_hint = QLabel("Зберегти файл на вашому комп'ютері у форматі JSON")
        local_hint.setStyleSheet("color: grey; font-size: 12px; margin-left: 10px; margin-top: 3px;")
        local_hint.setWordWrap(True)
        local_container.addWidget(local_hint)

        buttons_layout.addLayout(local_container)

        drive_container = QVBoxLayout()
        drive_container.setSpacing(5)

        drive_btn = QPushButton("☁️  Google Drive")
        drive_btn.setMinimumHeight(60)
        drive_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 10px;
                text-align: left;
                border: 2px solid #4CAF50;
                border-radius: 5px;
                color: black;
                background-color: white;
            }
            QPushButton:hover {
                background-color: #E8F5E9;
            }
        """)
        drive_btn.clicked.connect(self._on_drive_clicked)
        drive_container.addWidget(drive_btn)

        drive_hint = QLabel("Зберегти файл у хмарі як Google Sheets")
        drive_hint.setStyleSheet("color: grey; font-size: 12px; margin-left: 10px; margin-top: 3px;")
        drive_hint.setWordWrap(True)
        drive_container.addWidget(drive_hint)

        buttons_layout.addLayout(drive_container)

        layout.addLayout(buttons_layout)

        # Кнопка скасування
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def _on_local_clicked(self):
        """Обробник вибору локальної файлової системи."""
        self.selected_storage = StorageType.LOCAL
        self.accept()

    def _on_drive_clicked(self):
        """Обробник вибору Google Drive."""
        self.selected_storage = StorageType.GOOGLE_DRIVE
        self.accept()

    def get_selected_storage(self) -> StorageType:
        """
        Повертає вибраний тип сховища.

        Returns:
            StorageType: Вибраний тип сховища
        """
        return self.selected_storage
