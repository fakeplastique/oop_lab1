import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from src.infrastructure.logging.logging_factory import LoggingFactory
from src.presentation.views.main_window import MainWindow
from src.presentation.styles import get_application_stylesheet


def main():
    log_dir = Path.home() / ".spreadsheet" / "logs"
    log_file = log_dir / "spreadsheet.log"

    LoggingFactory.configure(
        log_file=log_file,
        log_level=20,  # INFO
    )

    logger = LoggingFactory.get_logger(__name__)
    logger.info("=" * 50)
    logger.info("Запуск застосунку")
    logger.info("=" * 50)

    app = QApplication(sys.argv)
    app.setApplicationName("Python Excel")

    app.setStyle("Fusion")
    logger.info("Стиль Fusion встановлено")

    app.setStyleSheet(get_application_stylesheet())
    logger.info("QSS стилі застосовано")

    window = MainWindow()
    window.show()

    logger.info("Головне вікно відкрито")

    exit_code = app.exec()

    logger.info(f"Застосунок завершено з кодом: {exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
