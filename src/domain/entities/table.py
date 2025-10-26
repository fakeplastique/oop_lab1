from src.domain.value_objects import CellReference
from .cell import Cell


class Table:
    """
    Entity для електронної таблиці.

    Управляє колекцією клітинок та їх розміром.
    """

    def __init__(self, rows: int = 10, columns: int = 10):
        """
        Ініціалізує таблицю.

        Args:
            rows: Кількість рядків
            columns: Кількість стовпчиків
        """
        if rows < 1 or columns < 1:
            raise ValueError("Кількість рядків та стовпчиків має бути >= 1")

        self._rows: int = rows
        self._columns: int = columns
        self._cells: dict[tuple[int, int], Cell] = {}

    @property
    def rows(self) -> int:
        """Повертає кількість рядків."""
        return self._rows

    @property
    def columns(self) -> int:
        """Повертає кількість стовпчиків."""
        return self._columns

    def resize(self, rows: int, columns: int) -> None:
        """
        Змінює розмір таблиці.

        Args:
            rows: Нова кількість рядків
            columns: Нова кількість стовпчиків
        """
        if rows < 1 or columns < 1:
            raise ValueError("Кількість рядків та стовпчиків має бути >= 1")

        # Видаляємо клітинки, що виходять за нові межі
        if rows < self._rows or columns < self._columns:
            cells_to_remove = [
                (r, c) for (r, c) in self._cells.keys()
                if r >= rows or c >= columns
            ]
            for key in cells_to_remove:
                del self._cells[key]

        self._rows = rows
        self._columns = columns

    def get_cell(self, row: int, col: int) -> Cell:
        """
        Повертає клітинку за індексами.

        Якщо клітинка не існує, створює нову порожню.

        Args:
            row: Індекс рядка (0-based)
            col: Індекс стовпчика (0-based)

        Returns:
            Клітинка
        """
        self._validate_indices(row, col)

        if (row, col) not in self._cells:
            self._cells[(row, col)] = Cell()

        return self._cells[(row, col)]

    def get_cell_by_reference(self, reference: CellReference) -> Cell:
        """
        Повертає клітинку за посиланням.

        Args:
            reference: Посилання на клітинку

        Returns:
            Клітинка
        """
        row, col = reference.to_indices()
        return self.get_cell(row, col)

    def set_cell_expression(self, row: int, col: int, expression: str) -> None:
        """
        Встановлює вираз для клітинки.

        Args:
            row: Індекс рядка
            col: Індекс стовпчика
            expression: Текстовий вираз
        """
        cell = self.get_cell(row, col)
        cell.expression = expression

    def clear_cell(self, row: int, col: int) -> None:
        """
        Очищає клітинку.

        Args:
            row: Індекс рядка
            col: Індекс стовпчика
        """
        self._validate_indices(row, col)

        if (row, col) in self._cells:
            self._cells[(row, col)] = Cell()

    def clear_all(self) -> None:
        """Очищає всі клітинки."""
        self._cells.clear()

    def get_all_cells(self) -> list[tuple[int, int, Cell]]:
        """
        Повертає список всіх непорожніх клітинок.

        Returns:
            Список кортежів (row, col, cell)
        """
        return [
            (row, col, cell)
            for (row, col), cell in self._cells.items()
            if not cell.is_empty()
        ]

    def invalidate_all(self) -> None:
        """Інвалідує всі клітинки (для перерахунку)."""
        for cell in self._cells.values():
            cell.invalidate()

    def _validate_indices(self, row: int, col: int) -> None:
        """
        Валідує індекси рядка та стовпчика.

        Args:
            row: Індекс рядка
            col: Індекс стовпчика

        Raises:
            IndexError: Якщо індекси виходять за межі таблиці
        """
        if not (0 <= row < self._rows):
            raise IndexError(f"Індекс рядка {row} виходить за межі таблиці")
        if not (0 <= col < self._columns):
            raise IndexError(f"Індекс стовпчика {col} виходить за межі таблиці")

    def __repr__(self) -> str:
        return f"Table(rows={self._rows}, columns={self._columns}, cells={len(self._cells)})"
