"""Widget для відображення та редагування таблиці."""
from PySide6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont

from src.application.services.table_service import TableService
from src.domain.value_objects import CellReference
from src.infrastructure.logging.logging_factory import LoggingFactory
from src.presentation.styles import (
    get_table_cell_error_style,
    get_table_cell_normal_style,
    get_table_cell_formula_style,
    get_table_cell_literal_style,
)


class TableWidget(QTableWidget):
    """
    Widget для відображення та редагування електронної таблиці.

    Signals:
        cell_changed: Сигнал при зміні клітинки (row, col)
    """

    cell_changed = Signal(int, int)

    def __init__(self, table_service: TableService, parent=None):
        """
        Ініціалізує widget.

        Args:
            table_service: Сервіс для роботи з таблицею
            parent: Батьківський widget
        """
        super().__init__(parent)
        self.logger = LoggingFactory.get_logger(__name__)
        self.table_service = table_service
        self.show_values = True  # True - показувати значення, False - вирази

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Налаштовує інтерфейс таблиці."""
        self.setRowCount(self.table_service.table.rows)
        self.setColumnCount(self.table_service.table.columns)

        headers = [
            CellReference.from_indices(0, col).column
            for col in range(self.table_service.table.columns)
        ]
        self.setHorizontalHeaderLabels(headers)

        row_headers = [str(i + 1) for i in range(self.table_service.table.rows)]
        self.setVerticalHeaderLabels(row_headers)

        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.verticalHeader().setDefaultSectionSize(40)  # 40 пікселів висоти

        for row in range(self.table_service.table.rows):
            self.setRowHeight(row, 40)

    def _connect_signals(self) -> None:
        self.itemChanged.connect(self._on_item_changed)

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        """
        Обробляє зміну клітинки.

        Args:
            item: Змінена клітинка
        """
        row = item.row()
        col = item.column()
        text = item.text()

        self.logger.debug(f"Клітинка [{row},{col}] змінена: {text}")

        success, error = self.table_service.set_cell_expression(row, col, text)

        self.table_service.calculate_all()

        self.refresh_display()

        self.cell_changed.emit(row, col)

    def refresh_display(self) -> None:
        # Тимчасово відключаємо сигнал, щоб уникнути рекурсії
        self.blockSignals(True)

        for row in range(self.table_service.table.rows):
            for col in range(self.table_service.table.columns):
                cell = self.table_service.get_cell(row, col)
                item = self.item(row, col)

                if item is None:
                    item = QTableWidgetItem()
                    self.setItem(row, col, item)

                # Відображаємо вираз або значення
                if self.show_values:
                    # Режим ЗНАЧЕННЯ
                    display_text = cell.get_display_value()
                else:
                    # Режим ВИРАЗ
                    display_text = cell.expression

                item.setText(display_text)

                # Налаштовуємо стиль та підказку клітинки
                self._apply_cell_style(item, cell)

        self.blockSignals(False)

    def _apply_cell_style(self, item: QTableWidgetItem, cell) -> None:
        """
        Застосовує стиль до клітинки залежно від її стану.

        Args:
            item: Qt item для стилізації
            cell: Доменна модель клітинки
        """
        item.setBackground(QColor(255, 255, 255))
        item.setFont(QFont())

        # Помилка - найвищий пріоритет
        if cell.has_error():
            # Червоний фон для помилок
            item.setBackground(QColor(255, 205, 210))
            # Детальна підказка з типом та описом помилки
            tooltip = f"❌ ПОМИЛКА\n\n{cell.error}"
            # Додаємо підказку для виправлення
            if "Синтаксична помилка" in cell.error:
                tooltip += "\n\n💡 Порада: Перевірте правильність синтаксису виразу."
                tooltip += "\nФормули повинні починатися з символу ="
            elif "Циклічне посилання" in cell.error:
                tooltip += "\n\n💡 Порада: Клітинка не може посилатися сама на себе"
                tooltip += "\nабо створювати цикл посилань."
            elif "Ділення на нуль" in cell.error:
                tooltip += "\n\n💡 Порада: Переконайтеся, що дільник не дорівнює нулю."
            elif "не числове значення" in cell.error:
                tooltip += "\n\n💡 Порада: Клітинка містить текст, але очікується число."

            item.setToolTip(tooltip)

            # Жирний шрифт для помилок
            font = item.font()
            font.setBold(True)
            item.setForeground(QColor(198, 40, 40))
            item.setFont(font)
            return

        # Порожня клітинка
        if cell.is_empty():
            item.setToolTip("")
            return

        if cell.is_formula():
            if not self.show_values:
                item.setBackground(QColor(232, 245, 233))

            tooltip = f"📊 Формула\n\nВираз: {cell.expression}"
            if cell.cached_value is not None:
                tooltip += f"\nЗначення: {cell.cached_value}"
            item.setToolTip(tooltip)

            if not self.show_values:
                font = item.font()
                font.setItalic(True)
                item.setFont(font)
            return

        if cell.is_literal():
            if not self.show_values:
                item.setBackground(QColor(255, 249, 196))

            tooltip = f"📝 Літерал\n\nЗначення: {cell.expression}"
            item.setToolTip(tooltip)
            return

        item.setToolTip("")

    def toggle_display_mode(self) -> None:
        """Перемикає режим відображення між виразами та значеннями."""
        self.show_values = not self.show_values
        self.refresh_display()

    def resize_table(self, rows: int, columns: int) -> None:
        """
        Змінює розмір таблиці.

        Args:
            rows: Нова кількість рядків
            columns: Нова кількість стовпчиків
        """
        self.table_service.resize_table(rows, columns)

        self.setRowCount(rows)
        self.setColumnCount(columns)

        headers = [CellReference.from_indices(0, col).column for col in range(columns)]
        self.setHorizontalHeaderLabels(headers)

        row_headers = [str(i + 1) for i in range(rows)]
        self.setVerticalHeaderLabels(row_headers)

        for row in range(rows):
            self.setRowHeight(row, 40)

        # Recalculate all cells to detect errors from deleted cell references
        self.table_service.calculate_all()

        self.refresh_display()

    def clear_table(self) -> None:
        """Очищає всю таблицю."""
        self.table_service.clear_all()
        self.refresh_display()
