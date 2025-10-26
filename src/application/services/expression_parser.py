import re

from src.domain.exceptions import ExpressionSyntaxError
from src.domain.value_objects import (
    ASTNode,
    BinaryOpNode,
    CellRefNode,
    CellReference,
    NumberNode,
    UnaryOpNode,
)
from src.infrastructure.logging.logging_factory import LoggingFactory


class Token:
    """Токен лексичного аналізу."""

    def __init__(self, type_: str, value: str, position: int):
        self.type = type_
        self.value = value
        self.position = position

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, pos={self.position})"


class ExpressionParser:
    """
    Парсер виразів з синтаксичним аналізом.

    Використовує метод рекурсивного спуску для побудови AST.
    Підтримує пріоритети операцій та локалізацію помилок.

    Граматика (в порядку зростання пріоритету):
    expression ::= logical_or_expr
    logical_or_expr ::= logical_and_expr ('or' logical_and_expr)*
    logical_and_expr ::= comparison_expr ('and' comparison_expr)*
    comparison_expr ::= additive_expr (('=' | '<' | '>') additive_expr)?
    additive_expr ::= multiplicative_expr (('+' | '-') multiplicative_expr)*
    multiplicative_expr ::= power_expr (('*' | '/') power_expr)*
    power_expr ::= unary_expr ('^' power_expr)?
    unary_expr ::= ('+' | '-' | 'not') unary_expr | primary
    primary ::= NUMBER | CELL_REF | '(' expression ')'
    """

    # Типи токенів
    TOKEN_NUMBER = 'NUMBER'
    TOKEN_CELL_REF = 'CELL_REF'
    TOKEN_PLUS = 'PLUS'
    TOKEN_MINUS = 'MINUS'
    TOKEN_MULTIPLY = 'MULTIPLY'
    TOKEN_DIVIDE = 'DIVIDE'
    TOKEN_POWER = 'POWER'
    TOKEN_EQUAL = 'EQUAL'
    TOKEN_LESS = 'LESS'
    TOKEN_GREATER = 'GREATER'
    TOKEN_NOT = 'NOT'
    TOKEN_AND = 'AND'
    TOKEN_OR = 'OR'
    TOKEN_LPAREN = 'LPAREN'
    TOKEN_RPAREN = 'RPAREN'
    TOKEN_EOF = 'EOF'

    # Token regex
    TOKEN_PATTERNS = [
        (TOKEN_NUMBER, r'\d+'),
        (TOKEN_CELL_REF, r'[A-Z]+\d+'),
        (TOKEN_POWER, r'\^'),
        (TOKEN_EQUAL, r'='),
        (TOKEN_LESS, r'<'),
        (TOKEN_GREATER, r'>'),
        (TOKEN_PLUS, r'\+'),
        (TOKEN_MINUS, r'-'),
        (TOKEN_MULTIPLY, r'\*'),
        (TOKEN_DIVIDE, r'/'),
        (TOKEN_NOT, r'\bnot\b'),
        (TOKEN_AND, r'\band\b'),
        (TOKEN_OR, r'\bor\b'),
        (TOKEN_LPAREN, r'\('),
        (TOKEN_RPAREN, r'\)'),
    ]

    def __init__(self):
        self.logger = LoggingFactory.get_logger(__name__)
        self.tokens: list[Token] = []
        self.current_pos: int = 0
        self.expression: str = ""

    def parse(self, expression: str) -> ASTNode:
        """
        Парсить вираз та повертає AST.

        Args:
            expression: Рядок з виразом

        Returns:
            Корінь AST дерева

        Raises:
            ExpressionSyntaxError: При помилках синтаксису
        """
        self.logger.info(f"Парсинг виразу: {expression}")
        self.expression = expression.strip()

        if not self.expression:
            raise ExpressionSyntaxError("Порожній вираз", 0)

        # lexical analysis
        self.tokens = self._tokenize(self.expression)
        self.current_pos = 0

        # syntax analysis
        try:
            ast = self._parse_expression()

            # Перевіряємо, що всі токени оброблені
            if self._current_token().type != self.TOKEN_EOF:
                raise ExpressionSyntaxError(
                    f"Неочікуваний токен: {self._current_token().value}",
                    self._current_token().position
                )

            self.logger.info("Парсинг успішний")
            return ast

        except ExpressionSyntaxError:
            raise
        except Exception as e:
            self.logger.error(f"Помилка парсингу: {e}")
            raise ExpressionSyntaxError(str(e), self._current_token().position)

    def _tokenize(self, expression: str) -> list[Token]:
        """
        Лексичний аналіз - розбиває вираз на токени.

        Args:
            expression: Рядок виразу

        Returns:
            Список токенів

        Raises:
            ExpressionSyntaxError: При невідомих символах
        """
        tokens = []
        position = 0

        while position < len(expression):
            if expression[position].isspace():
                position += 1
                continue

            matched = False
            for token_type, pattern in self.TOKEN_PATTERNS:
                regex = re.compile(pattern)
                match = regex.match(expression, position)
                if match:
                    value = match.group(0)
                    tokens.append(Token(token_type, value, position))
                    position = match.end()
                    matched = True
                    break

            if not matched:
                raise ExpressionSyntaxError(
                    f"Невідомий символ: '{expression[position]}'",
                    position
                )

        # Додаємо EOF токен
        tokens.append(Token(self.TOKEN_EOF, '', position))
        return tokens

    def _current_token(self) -> Token:
        """Повертає поточний токен."""
        if self.current_pos < len(self.tokens):
            return self.tokens[self.current_pos]
        return self.tokens[-1]  # EOF

    def _consume(self, expected_type: str | None = None) -> Token:
        """
        Споживає поточний токен та переходить до наступного.

        Args:
            expected_type: Очікуваний тип токена (для валідації)

        Returns:
            Спожитий токен

        Raises:
            ExpressionSyntaxError: Якщо тип токена не відповідає очікуваному
        """
        token = self._current_token()

        if expected_type and token.type != expected_type:
            raise ExpressionSyntaxError(
                f"Очікувався {expected_type}, знайдено {token.type}",
                token.position
            )

        self.current_pos += 1
        return token

    def _parse_expression(self) -> ASTNode:
        """Парсить вираз (найнижчий пріоритет)."""
        return self._parse_logical_or()

    def _parse_logical_or(self) -> ASTNode:
        """Парсить логічне OR."""
        left = self._parse_logical_and()

        while self._current_token().type == self.TOKEN_OR:
            op_token = self._consume()
            right = self._parse_logical_and()
            left = BinaryOpNode(operator='or', left=left, right=right)

        return left

    def _parse_logical_and(self) -> ASTNode:
        """Парсить логічне AND."""
        left = self._parse_comparison()

        while self._current_token().type == self.TOKEN_AND:
            op_token = self._consume()
            right = self._parse_comparison()
            left = BinaryOpNode(operator='and', left=left, right=right)

        return left

    def _parse_comparison(self) -> ASTNode:
        """Парсить порівняння (=, <, >)."""
        left = self._parse_additive()

        token = self._current_token()
        if token.type in (self.TOKEN_EQUAL, self.TOKEN_LESS, self.TOKEN_GREATER):
            op_token = self._consume()
            right = self._parse_additive()
            operator = {'=': '=', '<': '<', '>': '>'}[op_token.value]
            return BinaryOpNode(operator=operator, left=left, right=right)

        return left

    def _parse_additive(self) -> ASTNode:
        """Парсить додавання та віднімання."""
        left = self._parse_multiplicative()

        while self._current_token().type in (self.TOKEN_PLUS, self.TOKEN_MINUS):
            op_token = self._consume()
            right = self._parse_multiplicative()
            operator = '+' if op_token.type == self.TOKEN_PLUS else '-'
            left = BinaryOpNode(operator=operator, left=left, right=right)

        return left

    def _parse_multiplicative(self) -> ASTNode:
        """Парсить множення та ділення."""
        left = self._parse_power()

        while self._current_token().type in (self.TOKEN_MULTIPLY, self.TOKEN_DIVIDE):
            op_token = self._consume()
            right = self._parse_power()
            operator = '*' if op_token.type == self.TOKEN_MULTIPLY else '/'
            left = BinaryOpNode(operator=operator, left=left, right=right)

        return left

    def _parse_power(self) -> ASTNode:
        """Парсить піднесення до степеню (правоасоціативне)."""
        left = self._parse_unary()

        if self._current_token().type == self.TOKEN_POWER:
            self._consume()
            right = self._parse_power()  # Правоасоціативність
            return BinaryOpNode(operator='^', left=left, right=right)

        return left

    def _parse_unary(self) -> ASTNode:
        """Парсить унарні операції."""
        token = self._current_token()

        if token.type in (self.TOKEN_PLUS, self.TOKEN_MINUS, self.TOKEN_NOT):
            op_token = self._consume()
            operand = self._parse_unary()
            operator = {
                self.TOKEN_PLUS: '+',
                self.TOKEN_MINUS: '-',
                self.TOKEN_NOT: 'not'
            }[op_token.type]
            return UnaryOpNode(operator=operator, operand=operand)

        return self._parse_primary()

    def _parse_primary(self) -> ASTNode:
        """Парсить первинні вирази (числа, посилання, дужки)."""
        token = self._current_token()

        # Число
        if token.type == self.TOKEN_NUMBER:
            self._consume()
            return NumberNode(value=int(token.value))

        # Посилання на клітинку
        if token.type == self.TOKEN_CELL_REF:
            self._consume()
            try:
                ref = CellReference.from_string(token.value)
                return CellRefNode(reference=ref)
            except ValueError as e:
                raise ExpressionSyntaxError(str(e), token.position)

        # Дужки
        if token.type == self.TOKEN_LPAREN:
            self._consume(self.TOKEN_LPAREN)
            expr = self._parse_expression()
            self._consume(self.TOKEN_RPAREN)
            return expr

        raise ExpressionSyntaxError(
            f"Очікувалося число, посилання на клітинку або '(', знайдено: {token.value}",
            token.position
        )
