from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QDialogButtonBox
)
from PySide6.QtCore import Qt


class FileNameDialog(QDialog):
    """
    Діалог для введення назви файлу.

    Використовується при збереженні файлу на Google Drive
    для отримання назви від користувача.
    """

    def __init__(self, parent=None, default_name: str = ""):
        """
        Ініціалізує діалог введення назви.

        Args:
            parent: Батьківський віджет
            default_name: Назва за замовчуванням
        """
        super().__init__(parent)
        self.file_name = default_name
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Введіть назву файлу")
        self.setMinimumWidth(400)

        layout = QVBoxLayout()

        # Заголовок
        title = QLabel("<h3>Збереження на Google Drive</h3>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        instruction = QLabel("Введіть назву для вашого файлу:")
        instruction.setStyleSheet("color: #666; margin-top: 10px;")
        layout.addWidget(instruction)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Наприклад: Моя таблиця")
        self.name_input.setText(self.file_name)
        self.name_input.textChanged.connect(self._on_text_changed)
        self.name_input.setMinimumHeight(35)
        self.name_input.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 2px solid #BDBDBD;
                border-radius: 3px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
        """)
        layout.addWidget(self.name_input)


        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        self.ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setText("Зберегти")
        self.ok_button.setEnabled(bool(self.file_name.strip()))
        button_box.accepted.connect(self._on_ok_clicked)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

        self.name_input.setFocus()
        self.name_input.selectAll()

    def _on_text_changed(self, text: str):
        """
        Обробник зміни тексту.

        Args:
            text: Новий текст
        """
        # Активуємо кнопку OK тільки якщо текст не порожній
        self.ok_button.setEnabled(bool(text.strip()))

    def _on_ok_clicked(self):
        """Обробник натискання кнопки OK."""
        self.file_name = self.name_input.text().strip()
        if self.file_name:
            self.accept()

    def get_file_name(self) -> str:
        """
        Повертає введену назву файлу.

        Returns:
            str: Назва файлу
        """
        return self.file_name
