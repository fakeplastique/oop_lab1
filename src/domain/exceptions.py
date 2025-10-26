
class DomainException(Exception):
    """Базовий виняток для domain layer."""
    pass


class ExpressionSyntaxError(DomainException):
    """Помилка синтаксису виразу."""

    def __init__(self, message: str, position: int = -1):
        """
        Ініціалізує виняток з повідомленням та позицією помилки.

        Args:
            message: Опис помилки
            position: Позиція у виразі, де виникла помилка
        """
        self.position = position
        super().__init__(message)


class CircularReferenceError(DomainException):
    """Помилка циклічного посилання між клітинками."""
    pass


class CellReferenceError(DomainException):
    """Помилка посилання на клітинку."""
    pass


class EvaluationError(DomainException):
    """Помилка обчислення виразу."""
    pass
