import logging
import sys
from pathlib import Path


class LoggingFactory:

    _initialized: bool = False
    _log_file: Path | None = None
    _log_level: int = logging.INFO

    @classmethod
    def configure(
        cls,
        log_file: Path | None = None,
        log_level: int = logging.INFO,
        format_string: str | None = None
    ) -> None:
        """
        Args:
            log_file: Шлях до файлу для запису логів
            log_level: Рівень логування (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            format_string: Формат повідомлень логера
        """
        cls._log_file = log_file
        cls._log_level = log_level

        if format_string is None:
            format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        root_logger.handlers.clear()

        formatter = logging.Formatter(format_string)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

        cls._initialized = True

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Створює або повертає логер з вказаним ім'ям.

        Args:
            name: Ім'я логера (зазвичай __name__ модуля)

        Returns:
            Налаштований екземпляр логера
        """
        if not cls._initialized:
            cls.configure()

        return logging.getLogger(name)
