from src.domain.value_objects import ASTNode


class Cell:
    """
    Entity для клітинки електронної таблиці.

    Клітинка може містити:
    - Текстовий вираз (expression)
    - Розпарсене AST дерево (ast)
    - Кешоване обчислене значення (cached_value)
    - Стан помилки (error)
    """

    def __init__(self, expression: str = ""):
        """
        Ініціалізує клітинку.

        Args:
            expression: Текстовий вираз
        """
        self._expression: str = expression
        self._ast: ASTNode | None = None
        self._cached_value: int | None = None
        self._error: str | None = None
        self._is_dirty: bool = True  

    @property
    def expression(self) -> str:
        """Повертає текстовий вираз."""
        return self._expression

    @expression.setter
    def expression(self, value: str) -> None:
        """
        Встановлює новий вираз та інвалідує кеш.

        Args:
            value: Новий вираз
        """
        if self._expression != value:
            self._expression = value
            self.invalidate()

    @property
    def ast(self) -> ASTNode | None:
        """Повертає AST дерево виразу."""
        return self._ast

    @ast.setter
    def ast(self, value: ASTNode | None) -> None:
        """Встановлює AST дерево."""
        self._ast = value

    @property
    def cached_value(self) -> int | None:
        """Повертає кешоване значення."""
        return self._cached_value

    @cached_value.setter
    def cached_value(self, value: int | None) -> None:
        """Встановлює кешоване значення."""
        self._cached_value = value
        self._is_dirty = False

    @property
    def error(self) -> str | None:
        """Повертає повідомлення про помилку."""
        return self._error

    @error.setter
    def error(self, value: str | None) -> None:
        """Встановлює повідомлення про помилку."""
        self._error = value

    @property
    def is_dirty(self) -> bool:
        """Чи потребує клітинка перерахунку."""
        return self._is_dirty

    def invalidate(self) -> None:
        """Інвалідує кеш клітинки."""
        self._ast = None
        self._cached_value = None
        self._error = None
        self._is_dirty = True

    def invalidate_value(self) -> None:
        """Інвалідує тільки обчислене значення, зберігаючи AST."""
        self._cached_value = None
        self._error = None
        self._is_dirty = True

    def is_empty(self) -> bool:
        """Чи є клітинка порожньою."""
        return not self._expression.strip()

    def has_error(self) -> bool:
        """Чи є помилка у клітинці."""
        return self._error is not None

    def is_formula(self) -> bool:
        """
        Перевіряє чи є вміст клітинки формулою (починається з =).

        Returns:
            True якщо це формула, False інакше
        """
        return self._expression.strip().startswith('=')

    def get_formula_expression(self) -> str:
        """
        Повертає вираз формули без префіксу =.

        Returns:
            Вираз без = або порожній рядок
        """
        if self.is_formula():
            return self._expression.strip()[1:].strip()
        return ""

    def is_literal(self) -> bool:
        """
        Перевіряє чи є вміст клітинки літералом (число або текст).

        Returns:
            True якщо це літерал, False якщо формула
        """
        return not self.is_empty() and not self.is_formula()

    def is_boolean_expression(self) -> bool:
        """
        Перевіряє чи формула містить логічні операції.

        Returns:
            True якщо формула містить логічні оператори
        """
        if not self.is_formula():
            return False

        formula = self.get_formula_expression().lower()
        logical_operators = ['and', 'or', 'not', '=', '<', '>']
        return any(op in formula for op in logical_operators)

    def get_display_value(self) -> str:
        """
        Повертає значення для відображення.

        Returns:
            Рядок для відображення (значення або помилка)
        """
        if self.has_error():
            return f"ПОМИЛКА"

        if self.is_literal():
            return self._expression.strip()

        if self._cached_value is not None:
            if self.is_boolean_expression():
                return "TRUE" if self._cached_value != 0 else "FALSE"
            return str(self._cached_value)

        if self.is_empty():
            return ""

        return "?"

    def __repr__(self) -> str:
        return f"Cell(expression={self._expression!r}, value={self._cached_value})"
