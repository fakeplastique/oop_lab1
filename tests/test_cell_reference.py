import pytest
from src.domain.value_objects.cell_reference import CellReference


class TestCellReference:
    """Test suite for CellReference class."""

    def test_from_string_valid(self):
        ref = CellReference.from_string("A1")
        assert ref.column == "A"
        assert ref.row == 1

        ref = CellReference.from_string("AB10")
        assert ref.column == "AB"
        assert ref.row == 10

        ref = CellReference.from_string("b5")
        assert ref.column == "B"
        assert ref.row == 5

    def test_from_string_invalid(self):
        with pytest.raises(ValueError):
            CellReference.from_string("123")  

        with pytest.raises(ValueError):
            CellReference.from_string("ABC")  

        with pytest.raises(ValueError):
            CellReference.from_string("A0")  

    def test_to_string(self):
        ref = CellReference(column="C", row=15)
        assert ref.to_string() == "C15"

        ref = CellReference(column="AA", row=1)
        assert ref.to_string() == "AA1"

    def test_to_indices(self):
        ref = CellReference(column="A", row=1)
        row_idx, col_idx = ref.to_indices()
        assert row_idx == 0
        assert col_idx == 0

        ref = CellReference(column="B", row=5)
        row_idx, col_idx = ref.to_indices()
        assert row_idx == 4
        assert col_idx == 1

        ref = CellReference(column="AA", row=1)
        row_idx, col_idx = ref.to_indices()
        assert row_idx == 0
        assert col_idx == 26

    def test_from_indices(self):
        ref = CellReference.from_indices(0, 0)
        assert ref.column == "A"
        assert ref.row == 1

        ref = CellReference.from_indices(4, 1)
        assert ref.column == "B"
        assert ref.row == 5

        ref = CellReference.from_indices(0, 26)
        assert ref.column == "AA"
        assert ref.row == 1

    def test_round_trip_conversion(self):
        original = CellReference(column="C", row=10)
        row_idx, col_idx = original.to_indices()
        restored = CellReference.from_indices(row_idx, col_idx)
        assert restored == original

        original = CellReference(column="AB", row=25)
        row_idx, col_idx = original.to_indices()
        restored = CellReference.from_indices(row_idx, col_idx)
        assert restored == original
