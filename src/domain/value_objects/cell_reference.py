"""Value object для посилання на клітинку."""
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class CellReference:
    """
    Value object для посилання на клітинку таблиці.
    """

    column: str  
    row: int     

    PATTERN = re.compile(r'^([A-Z]+)(\d+)$')

    def __post_init__(self):
        """Валідація даних після ініціалізації."""
        if not self.column or not self.column.isalpha() or not self.column.isupper():
            raise ValueError(f"Неправильна назва стовпчика: {self.column}")
        if self.row < 1:
            raise ValueError(f"Номер рядка має бути >= 1: {self.row}")

    @classmethod
    def from_string(cls, ref: str) -> 'CellReference':
        """
        Створює CellReference з рядка.

        Args:
            ref: стрінг (рядок з назвою клітинки)

        Returns:
            Екземпляр CellReference

        Raises:
            ValueError: Якщо формат рядка неправильний
        """
        match = cls.PATTERN.match(ref.strip().upper())
        if not match:
            raise ValueError(f"Неправильний формат посилання на клітинку: {ref}")

        column = match.group(1)
        row = int(match.group(2))

        return cls(column=column, row=row)

    def to_string(self) -> str:
        """Повертає рядкове представлення посилання."""
        return f"{self.column}{self.row}"

    def to_indices(self) -> tuple[int, int]:
        """
        Конвертує посилання у індекси (рядок, стовпчик).

        Returns:
            Кортеж (row_index, col_index), де індекси починаються з 0
        """
        col_index = self._column_to_index(self.column)
        row_index = self.row - 1
        return row_index, col_index

    @staticmethod
    def _column_to_index(column: str) -> int:
        """
        Конвертує назву стовпчика у індекс.
        """
        index = 0
        for char in column:
            index = index * 26 + (ord(char) - ord('A') + 1)
        return index - 1

    @classmethod
    def from_indices(cls, row_index: int, col_index: int) -> 'CellReference':
        """
        Створює CellReference з індексів.

        Args:
            row_index: Індекс рядка (починається з 0)
            col_index: Індекс стовпчика (починається з 0)

        Returns:
            Екземпляр CellReference
        """
        column = cls._index_to_column(col_index)
        row = row_index + 1
        return cls(column=column, row=row)

    @staticmethod
    def _index_to_column(index: int) -> str:
        """
        Конвертує індекс стовпчика у назву.
        """
        column = ""
        index += 1  
        while index > 0:
            index -= 1
            column = chr(ord('A') + index % 26) + column
            index //= 26
        return column

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        return f"CellReference('{self.to_string()}')"
