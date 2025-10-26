from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton


class HelpDialog(QDialog):
    """Діалогове вікно з довідкою користувача."""

    def __init__(self, parent=None):
        """Ініціалізує діалог."""
        super().__init__(parent)
        self.setWindowTitle("Довідка")
        self.setModal(True)
        self.resize(700, 300)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Текстовий браузер для довідки
        help_browser = QTextBrowser()
        help_browser.setHtml(self._get_help_content())
        layout.addWidget(help_browser)

        close_button = QPushButton("Закрити")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

    def _get_help_content(self) -> str:
        """Повертає HTML контент довідки."""
        return """
        <h1>Лабораторна робота #1.</h1>
        <h2>Розробив студент групи К-25, Бондар Ігор</h2>
        <p>Застосунок для створення та обробки таблиць
        з підтримкою виразів та обчислень.</p>
        """
