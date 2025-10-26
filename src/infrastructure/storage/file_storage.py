import json
from pathlib import Path

from src.infrastructure.logging.logging_factory import LoggingFactory


class FileStorage:
    """
    Сховище для роботи з файлами таблиць.

    Використовує JSON формат для збереження даних таблиці.
    """

    def __init__(self):
        """Ініціалізує сховище."""
        self.logger = LoggingFactory.get_logger(__name__)

    def save(self, file_path: Path, data: dict) -> None:
        """
        Зберігає дані таблиці у файл.

        Args:
            file_path: Шлях до файлу
            data: Дані для збереження

        Raises:
            IOError: При помилках запису
        """
        self.logger.info(f"Збереження таблиці у файл: {file_path}")

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Таблиця успішно збережена: {file_path}")

        except Exception as e:
            self.logger.error(f"Помилка збереження файлу: {e}")
            raise IOError(f"Не вдалося зберегти файл: {e}")

    def load(self, file_path: Path) -> dict:
        """
        Завантажує дані таблиці з файлу.

        Args:
            file_path: Шлях до файлу

        Returns:
            Завантажені дані

        Raises:
            IOError: При помилках читання
            ValueError: При невалідному форматі файлу
        """
        self.logger.info(f"Завантаження таблиці з файлу: {file_path}")

        if not file_path.exists():
            raise IOError(f"Файл не знайдено: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self._validate_data(data)

            self.logger.info(f"Таблиця успішно завантажена: {file_path}")
            return data

        except json.JSONDecodeError as e:
            self.logger.error(f"Помилка парсингу JSON: {e}")
            raise ValueError(f"Невалідний формат файлу: {e}")
        except Exception as e:
            self.logger.error(f"Помилка завантаження файлу: {e}")
            raise IOError(f"Не вдалося завантажити файл: {e}")

    def _validate_data(self, data: dict) -> None:
        """
        Валідує структуру завантажених даних.

        Args:
            data: Дані для валідації

        Raises:
            ValueError: Якщо структура невалідна
        """
        required_keys = ['rows', 'columns', 'cells']

        for key in required_keys:
            if key not in data:
                raise ValueError(f"Відсутнє обов'язкове поле: {key}")

        if not isinstance(data['rows'], int) or data['rows'] < 1:
            raise ValueError("Поле 'rows' має бути цілим числом >= 1")

        if not isinstance(data['columns'], int) or data['columns'] < 1:
            raise ValueError("Поле 'columns' має бути цілим числом >= 1")

        if not isinstance(data['cells'], list):
            raise ValueError("Поле 'cells' має бути списком")

        # Валідація клітинок
        for cell in data['cells']:
            if not isinstance(cell, dict):
                raise ValueError("Кожна клітинка має бути словником")

            required_cell_keys = ['row', 'col', 'expression']
            for key in required_cell_keys:
                if key not in cell:
                    raise ValueError(f"Відсутнє обов'язкове поле клітинки: {key}")
