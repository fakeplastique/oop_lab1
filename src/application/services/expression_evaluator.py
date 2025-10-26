from typing import Callable

from src.domain.exceptions import (
    CircularReferenceError,
    EvaluationError,
    CellReferenceError,
)
from src.domain.value_objects import (
    ASTNode,
    ASTVisitor,
    BinaryOpNode,
    CellRefNode,
    CellReference,
    NumberNode,
    UnaryOpNode,
)
from src.infrastructure.logging.logging_factory import LoggingFactory


class ExpressionEvaluator(ASTVisitor):
    """
    Обчислює:
    - Цілі числа довільної довжини
    - Унарні операції: +, -, not
    - Бінарні операції: +, -, *, /, ^
    - Порівняння: =, <, >
    - Логічні операції: and, or
    - Посилання на клітинки
    """

    def __init__(self, cell_value_provider: Callable[[CellReference], int]):
        """

        Args:
            cell_value_provider: Функція для отримання значення клітинки
                                за її посиланням
        """
        self.logger = LoggingFactory.get_logger(__name__)
        self.cell_value_provider = cell_value_provider
        self._evaluation_stack: set[str] = set()  # Для виявлення циклів

    def evaluate(self, ast: ASTNode, current_cell: CellReference | None = None) -> int:
        """
        Обчислює значення AST.

        Args:
            ast: Корінь дерева виразу
            current_cell: Посилання на поточну клітинку (для виявлення циклів)

        Returns:
            Обчислене значення (ціле число)

        Raises:
            EvaluationError: При помилках обчислення
            CircularReferenceError: При циклічних посиланнях
        """
        self._evaluation_stack.clear()
        if current_cell:
            self._evaluation_stack.add(current_cell.to_string())

        try:
            result = ast.accept(self)
            self.logger.debug(f"Результат обчислення: {result}")
            return result
        except (EvaluationError, CircularReferenceError, CellReferenceError):
            raise
        except Exception as e:
            self.logger.error(f"Помилка обчислення: {e}")
            raise EvaluationError(f"Помилка обчислення: {e}")

    def visit_number(self, node: NumberNode) -> int:
        return node.value

    def visit_cell_ref(self, node: CellRefNode) -> int:
        """
        Відвідує вузол посилання на клітинку.

        Raises:
            CircularReferenceError: Якщо виявлено циклічне посилання
            CellReferenceError: Якщо не вдалося отримати значення клітинки
        """
        ref_str = node.reference.to_string()

        if ref_str in self._evaluation_stack:
            raise CircularReferenceError(
                f"Виявлено циклічне посилання на клітинку {ref_str}"
            )

        self._evaluation_stack.add(ref_str)

        try:
            value = self.cell_value_provider(node.reference)
            return value
        except Exception as e:
            raise CellReferenceError(
                f"Помилка отримання значення клітинки {ref_str}: {e}"
            )
        finally:
            self._evaluation_stack.discard(ref_str)

    def visit_unary_op(self, node: UnaryOpNode) -> int:
        """Відвідує вузол унарної операції."""
        operand_value = node.operand.accept(self)

        if node.operator == '+':
            return operand_value
        elif node.operator == '-':
            return -operand_value
        elif node.operator == 'not':
            # not: 0 -> 1, non-zero -> 0
            return 1 if operand_value == 0 else 0
        else:
            raise EvaluationError(f"Невідома унарна операція: {node.operator}")

    def visit_binary_op(self, node: BinaryOpNode) -> int:
        """Відвідує вузол бінарної операції."""
        if node.operator == '+':
            return node.left.accept(self) + node.right.accept(self)
        elif node.operator == '-':
            return node.left.accept(self) - node.right.accept(self)
        elif node.operator == '*':
            return node.left.accept(self) * node.right.accept(self)
        elif node.operator == '/':
            left_val = node.left.accept(self)
            right_val = node.right.accept(self)
            if right_val == 0:
                raise EvaluationError("Ділення на нуль")
            return round(left_val / right_val,3) 
        elif node.operator == '^':
            left_val = node.left.accept(self)
            right_val = node.right.accept(self)
            if right_val < 0:
                raise EvaluationError("Від'ємний степінь не підтримується")
            return left_val ** right_val

        elif node.operator == '=':
            return 1 if node.left.accept(self) == node.right.accept(self) else 0
        elif node.operator == '<':
            return 1 if node.left.accept(self) < node.right.accept(self) else 0
        elif node.operator == '>':
            return 1 if node.left.accept(self) > node.right.accept(self) else 0

        elif node.operator == 'and':
            left_val = node.left.accept(self)
            if left_val == 0:
                return 0  # Short-circuit
            right_val = node.right.accept(self)
            return 1 if right_val != 0 else 0
        elif node.operator == 'or':
            left_val = node.left.accept(self)
            if left_val != 0:
                return 1  # Short-circuit
            right_val = node.right.accept(self)
            return 1 if right_val != 0 else 0

        else:
            raise EvaluationError(f"Невідома бінарна операція: {node.operator}")
