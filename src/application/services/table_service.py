"""Сервіс для роботи з таблицею (Application Layer)."""

from src.domain.entities import Cell, Table
from src.domain.exceptions import (
    CircularReferenceError,
    DomainException,
    ExpressionSyntaxError,
)
from src.domain.value_objects import CellReference
from src.infrastructure.logging.logging_factory import LoggingFactory
from .expression_evaluator import ExpressionEvaluator
from .expression_parser import ExpressionParser


class TableService:
    """
    Сервіс для координації роботи з таблицею.

    Відповідальності (Single Responsibility Principle):
    - Валідація та парсинг виразів
    - Обчислення значень клітинок
    - Координація операцій з таблицею
    """

    def __init__(self):
        """Ініціалізує сервіс."""
        self.logger = LoggingFactory.get_logger(__name__)
        self.table = Table()
        self.parser = ExpressionParser()
        self._evaluator: ExpressionEvaluator | None = None
        self._initialize_evaluator()

    def _initialize_evaluator(self) -> None:
        """Ініціалізує evaluator з callback для отримання значень клітинок."""
        self._evaluator = ExpressionEvaluator(
            cell_value_provider=self._get_cell_value_for_evaluator
        )

    def _get_cell_value_for_evaluator(self, reference: CellReference) -> int:
        """
        Callback для evaluator'а для отримання значення клітинки.

        Args:
            reference: Посилання на клітинку

        Returns:
            Значення клітинки (ціле число)

        Raises:
            Exception: Якщо клітинка порожня або має помилку
        """
        cell = self.table.get_cell_by_reference(reference)

        if cell.has_error():
            raise Exception(f"Клітинка {reference} має помилку: {cell.error}")

        if cell.is_empty():
            # Порожня клітинка має значення 0
            return 0

        # Якщо це літерал, намагаємося конвертувати у число
        if cell.is_literal():
            try:
                return int(cell.expression.strip())
            except ValueError:
                raise Exception(f"Клітинка {reference} містить не числове значення: {cell.expression}")

        # Якщо це формула, обчислюємо її AST
        if cell.is_formula():
            if not cell.ast:
                raise Exception(f"Клітинка {reference} не була розпарсена")

            value = cell.ast.accept(self._evaluator)

            return value

        raise Exception(f"Невідомий тип вмісту клітинки {reference}")

    def create_table(self, rows: int, columns: int) -> None:
        """
        Створює нову таблицю з заданими розмірами.

        Args:
            rows: Кількість рядків
            columns: Кількість стовпчиків
        """
        self.logger.info(f"Створення нової таблиці {rows}x{columns}")
        self.table = Table(rows, columns)

    def resize_table(self, rows: int, columns: int) -> None:
        """
        Змінює розмір таблиці.

        Args:
            rows: Нова кількість рядків
            columns: Нова кількість стовпчиків
        """
        self.logger.info(f"Зміна розміру таблиці на {rows}x{columns}")
        self.table.resize(rows, columns)
        # Інвалідуємо всі клітинки для перерахунку
        self.table.invalidate_all()

    def set_cell_expression(self, row: int, col: int, expression: str) -> tuple[bool, str]:
        """
        Встановлює вираз для клітинки та виконує його валідацію.

        Args:
            row: Індекс рядка
            col: Індекс стовпчика
            expression: Текстовий вираз (може бути формула з = або літерал)

        Returns:
            Кортеж (успіх, повідомлення_про_помилку)
        """
        self.logger.debug(f"Встановлення виразу [{row},{col}]: {expression}")

        cell = self.table.get_cell(row, col)
        cell.expression = expression

        # Якщо клітинка порожня, нічого не робимо
        if cell.is_empty():
            cell.cached_value = None
            cell.error = None
            return True, ""

        # Якщо це літерал (не формула), просто зберігаємо як текст
        if cell.is_literal():
            cell.ast = None
            cell.cached_value = None
            cell.error = None
            return True, ""

        # Якщо це формула (починається з =), парсимо її
        if cell.is_formula():
            formula_expr = cell.get_formula_expression()

            # Етап 1: Синтаксична перевірка
            try:
                ast = self.parser.parse(formula_expr)
                cell.ast = ast
                cell.error = None
            except ExpressionSyntaxError as e:
                error_msg = f"Синтаксична помилка: {e}"
                self.logger.warning(f"Помилка парсингу [{row},{col}]: {error_msg}")
                cell.error = error_msg
                cell.cached_value = None
                return False, error_msg
            except Exception as e:
                error_msg = f"Помилка: {e}"
                self.logger.error(f"Неочікувана помилка парсингу [{row},{col}]: {e}")
                cell.error = error_msg
                cell.cached_value = None
                return False, error_msg

            # Етап 2: Обчислення значення (викликається окремо через calculate_all)
            return True, ""

        return True, ""

    def calculate_all(self) -> None:
        """
        Обчислює значення всіх клітинок таблиці.

        Виконує обчислення у порядку залежностей.
        Обчислює тільки формули (клітинки з =).
        """
        self.logger.info("Обчислення всіх клітинок")

        for row, col, cell in self.table.get_all_cells():
            if cell.is_formula() and cell.ast:
                self._calculate_cell(row, col)

    def _calculate_cell(self, row: int, col: int) -> None:
        """
        Обчислює значення однієї клітинки.

        Args:
            row: Індекс рядка
            col: Індекс стовпчика
        """
        cell = self.table.get_cell(row, col)

        if cell.is_empty() or not cell.ast:
            return

        try:
            current_ref = CellReference.from_indices(row, col)

            value = self._evaluator.evaluate(cell.ast, current_ref) # type: ignore
            cell.cached_value = value
            cell.error = None

            self.logger.debug(f"Клітинка [{row},{col}] обчислена: {value}")

        except CircularReferenceError as e:
            error_msg = f"Циклічне посилання: {e}"
            self.logger.warning(f"Помилка обчислення [{row},{col}]: {error_msg}")
            cell.error = error_msg
            cell.cached_value = None

        except DomainException as e:
            error_msg = str(e)
            self.logger.warning(f"Помилка обчислення [{row},{col}]: {error_msg}")
            cell.error = error_msg
            cell.cached_value = None

        except Exception as e:
            error_msg = f"Помилка обчислення: {e}"
            self.logger.error(f"Неочікувана помилка обчислення [{row},{col}]: {e}")
            cell.error = error_msg
            cell.cached_value = None

    def _calculate_cell_by_reference(self, reference: CellReference) -> None:
        """
        Обчислює значення клітинки за посиланням.

        Args:
            reference: Посилання на клітинку
        """
        row, col = reference.to_indices()
        self._calculate_cell(row, col)

    def get_cell(self, row: int, col: int) -> Cell:
        """
        Повертає клітинку за індексами.

        Args:
            row: Індекс рядка
            col: Індекс стовпчика

        Returns:
            Клітинка
        """
        return self.table.get_cell(row, col)

    def clear_all(self) -> None:
        """Очищає всі клітинки таблиці."""
        self.logger.info("Очищення всіх клітинок")
        self.table.clear_all()

    def get_table_data_for_export(self) -> dict:
        """
        Повертає дані таблиці для експорту.

        Returns:
            Словник з даними таблиці
        """
        data = {
            'rows': self.table.rows,
            'columns': self.table.columns,
            'cells': []
        }

        for row, col, cell in self.table.get_all_cells():
            if not cell.is_empty():
                data['cells'].append({
                    'row': row,
                    'col': col,
                    'expression': cell.expression
                })

        return data

    def load_table_data(self, data: dict) -> None:
        """
        Завантажує дані таблиці з словника.

        Args:
            data: Словник з даними таблиці
        """
        self.logger.info("Завантаження даних таблиці")

        self.table = Table(data['rows'], data['columns'])

        for cell_data in data['cells']:
            row = cell_data['row']
            col = cell_data['col']
            expression = cell_data['expression']
            self.set_cell_expression(row, col, expression)

        # Обчислюємо всі клітинки
        self.calculate_all()
