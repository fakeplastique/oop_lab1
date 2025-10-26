"""AST (Abstract Syntax Tree) для виразів."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from .cell_reference import CellReference


class ASTNode(ABC):
    """Базовий клас для вузлів AST."""

    @abstractmethod
    def accept(self, visitor: 'ASTVisitor') -> Any:
        """
        Приймає відвідувача для обходу дерева (Visitor pattern).

        Args:
            visitor: Відвідувач, що обробляє вузли

        Returns:
            Результат обробки вузла
        """
        pass


@dataclass
class NumberNode(ASTNode):
    """Вузол для числового літералу."""
    value: int

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_number(self)


@dataclass
class CellRefNode(ASTNode):
    """Вузол для посилання на клітинку."""
    reference: CellReference

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_cell_ref(self)


@dataclass
class UnaryOpNode(ASTNode):
    """Вузол для унарної операції."""
    operator: str  # '+', '-', 'not'
    operand: ASTNode

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_unary_op(self)


@dataclass
class BinaryOpNode(ASTNode):
    """Вузол для бінарної операції."""
    operator: str  # '+', '-', '*', '/', '^', '=', '<', '>', 'and', 'or'
    left: ASTNode
    right: ASTNode

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_binary_op(self)


class ASTVisitor(ABC):
    """Інтерфейс для відвідувача AST (Visitor pattern)."""

    @abstractmethod
    def visit_number(self, node: NumberNode) -> Any:
        """Відвідує числовий вузол."""
        pass

    @abstractmethod
    def visit_cell_ref(self, node: CellRefNode) -> Any:
        """Відвідує вузол посилання на клітинку."""
        pass

    @abstractmethod
    def visit_unary_op(self, node: UnaryOpNode) -> Any:
        """Відвідує вузол унарної операції."""
        pass

    @abstractmethod
    def visit_binary_op(self, node: BinaryOpNode) -> Any:
        """Відвідує вузол бінарної операції."""
        pass
