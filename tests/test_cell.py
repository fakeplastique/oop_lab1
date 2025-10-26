import pytest
from src.domain.entities.cell import Cell
from src.domain.value_objects import NumberNode


class TestCell:

    def test_cell_initialization_empty(self):
        cell = Cell()
        assert cell.expression == ""
        assert cell.is_empty()
        assert not cell.is_formula()
        assert not cell.has_error()
        assert cell.cached_value is None

    def test_cell_initialization_with_expression(self):
        cell = Cell("=2+3")
        assert cell.expression == "=2+3"
        assert not cell.is_empty()
        assert cell.is_formula()
        assert cell.cached_value is None

    def test_cell_is_formula(self):
        cell = Cell("=5+5")
        assert cell.is_formula()

        cell = Cell("  = 10 * 2  ")
        assert cell.is_formula()

        cell = Cell("42")
        assert not cell.is_formula()

        cell = Cell("")
        assert not cell.is_formula()

    def test_cell_get_formula_expression(self):
        cell = Cell("=2+3")
        assert cell.get_formula_expression() == "2+3"

        cell = Cell("  =  A1 + B2  ")
        assert cell.get_formula_expression() == "A1 + B2"

        cell = Cell("42")
        assert cell.get_formula_expression() == ""

    def test_cell_is_literal(self):
        cell = Cell("42")
        assert cell.is_literal()
        assert not cell.is_formula()

        cell = Cell("Hello")
        assert cell.is_literal()

        cell = Cell("=2+3")
        assert not cell.is_literal()

        cell = Cell("")
        assert not cell.is_literal()

    def test_cell_expression_setter(self):
        cell = Cell("=5+5")
        cell.cached_value = 10
        cell.ast = NumberNode(value=10)

        cell.expression = "=2+2"
        assert cell.cached_value is None
        assert cell.ast is None
        assert cell.is_dirty

    def test_cell_invalidate(self):
        """Test invalidating cell cache."""
        cell = Cell("=5+5")
        cell.cached_value = 10
        cell.ast = NumberNode(value=10)
        cell.error = None

        cell.invalidate()
        assert cell.cached_value is None
        assert cell.ast is None
        assert cell.error is None
        assert cell.is_dirty

    def test_cell_has_error(self):
        cell = Cell("=2/0")
        assert not cell.has_error()

        cell.error = "Division by zero"
        assert cell.has_error()

    def test_cell_get_display_value_empty(self):
        cell = Cell("")
        assert cell.get_display_value() == ""

    def test_cell_get_display_value_literal(self):
        cell = Cell("42")
        assert cell.get_display_value() == "42"

        cell = Cell("  Hello World  ")
        assert cell.get_display_value() == "Hello World"

    def test_cell_get_display_value_formula(self):
        cell = Cell("=5+5")
        cell.cached_value = 10
        assert cell.get_display_value() == "10"

        cell2 = Cell("=2+2")
        assert cell2.get_display_value() == "?"

    def test_cell_get_display_value_error(self):
        cell = Cell("=2/0")
        cell.error = "Division by zero"
        assert cell.get_display_value() == "ПОМИЛКА"

    def test_cell_is_boolean_expression(self):
        cell = Cell("=5 = 5")
        assert cell.is_boolean_expression()

        cell = Cell("=3 < 5")
        assert cell.is_boolean_expression()

        cell = Cell("=1 and 1")
        assert cell.is_boolean_expression()

        cell = Cell("=0 or 1")
        assert cell.is_boolean_expression()

        cell = Cell("=not 0")
        assert cell.is_boolean_expression()

        cell = Cell("=2+3")
        assert not cell.is_boolean_expression()

        cell = Cell("42")
        assert not cell.is_boolean_expression()

    def test_cell_get_display_value_boolean(self):
        cell = Cell("=5 = 5")
        cell.cached_value = 1
        assert cell.get_display_value() == "TRUE"

        cell2 = Cell("=3 > 5")
        cell2.cached_value = 0
        assert cell2.get_display_value() == "FALSE"

    def test_cell_expression_unchanged(self):
        cell = Cell("=5+5")
        cell.cached_value = 10
        original_value = cell.cached_value

        cell.expression = "=5+5"
        assert cell.cached_value == original_value

    def test_cell_repr(self):
        cell = Cell("=2+3")
        cell.cached_value = 5
        repr_str = repr(cell)
        assert "Cell" in repr_str
        assert "2+3" in repr_str
        assert "5" in repr_str
