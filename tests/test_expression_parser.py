import pytest
from src.application.services.expression_parser import ExpressionParser
from src.domain.exceptions import ExpressionSyntaxError
from src.domain.value_objects import (
    NumberNode,
    BinaryOpNode,
    UnaryOpNode,
    CellRefNode,
)


class TestExpressionParser:

    def setup_method(self):
        self.parser = ExpressionParser()

    def test_parse_simple_number(self):
        """Test parsing a simple number."""
        ast = self.parser.parse("42")
        assert isinstance(ast, NumberNode)
        assert ast.value == 42

    def test_parse_cell_reference(self):
        ast = self.parser.parse("A1")
        assert isinstance(ast, CellRefNode)
        assert ast.reference.to_string() == "A1"

        ast = self.parser.parse("AB10")
        assert isinstance(ast, CellRefNode)
        assert ast.reference.to_string() == "AB10"

    def test_parse_addition(self):
        ast = self.parser.parse("2 + 3")
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == "+"
        assert isinstance(ast.left, NumberNode)
        assert ast.left.value == 2
        assert isinstance(ast.right, NumberNode)
        assert ast.right.value == 3

    def test_parse_subtraction(self):
        ast = self.parser.parse("10 - 5")
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == "-"
        assert ast.left.value == 10
        assert ast.right.value == 5

    def test_parse_multiplication(self):
        ast = self.parser.parse("4 * 5")
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == "*"
        assert ast.left.value == 4
        assert ast.right.value == 5

    def test_parse_division(self):
        ast = self.parser.parse("20 / 4")
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == "/"
        assert ast.left.value == 20
        assert ast.right.value == 4

    def test_parse_power(self):
        ast = self.parser.parse("2 ^ 3")
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == "^"
        assert ast.left.value == 2
        assert ast.right.value == 3

    def test_parse_unary_minus(self):
        ast = self.parser.parse("-5")
        assert isinstance(ast, UnaryOpNode)
        assert ast.operator == "-"
        assert isinstance(ast.operand, NumberNode)
        assert ast.operand.value == 5

    def test_parse_unary_not(self):
        ast = self.parser.parse("not 1")
        assert isinstance(ast, UnaryOpNode)
        assert ast.operator == "not"
        assert ast.operand.value == 1

    def test_parse_comparison_equal(self):
        ast = self.parser.parse("5 = 5")
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == "="
        assert ast.left.value == 5
        assert ast.right.value == 5

    def test_parse_comparison_less(self):
        ast = self.parser.parse("3 < 5")
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == "<"

    def test_parse_comparison_greater(self):
        ast = self.parser.parse("7 > 3")
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == ">"

    def test_parse_logical_and(self):
        ast = self.parser.parse("1 and 1")
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == "and"

    def test_parse_logical_or(self):
        ast = self.parser.parse("0 or 1")
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == "or"

    def test_parse_parentheses(self):
        ast = self.parser.parse("(2 + 3) * 4")
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == "*"
        assert isinstance(ast.left, BinaryOpNode)
        assert ast.left.operator == "+"

    def test_parse_operator_precedence(self):
        ast = self.parser.parse("2 + 3 * 4")
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == "+"
        assert isinstance(ast.left, NumberNode)
        assert ast.left.value == 2
        assert isinstance(ast.right, BinaryOpNode)
        assert ast.right.operator == "*"
        assert ast.right.left.value == 3
        assert ast.right.right.value == 4

    def test_parse_complex_expression(self):
        ast = self.parser.parse("A1 + 5 * 2 - 3")
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == "-"

    def test_parse_empty_expression(self):
        with pytest.raises(ExpressionSyntaxError):
            self.parser.parse("")

        with pytest.raises(ExpressionSyntaxError):
            self.parser.parse("   ")

    def test_parse_invalid_syntax(self):
        with pytest.raises(ExpressionSyntaxError):
            self.parser.parse("(2 + 3")  

        with pytest.raises(ExpressionSyntaxError):
            self.parser.parse("2 +")  

        with pytest.raises(ExpressionSyntaxError):
            self.parser.parse("* 3")  

    def test_parse_invalid_characters(self):
        """Test parsing invalid characters raises error."""
        with pytest.raises(ExpressionSyntaxError):
            self.parser.parse("2 $ 3") 

        with pytest.raises(ExpressionSyntaxError):
            self.parser.parse("2 @ 3")  

    def test_parse_cell_reference_with_operations(self):
        """Test parsing cell references in expressions."""
        ast = self.parser.parse("A1 + B2")
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == "+"
        assert isinstance(ast.left, CellRefNode)
        assert isinstance(ast.right, CellRefNode)
        assert ast.left.reference.to_string() == "A1"
        assert ast.right.reference.to_string() == "B2"
