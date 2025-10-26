
def get_application_stylesheet() -> str:
    """
    Повертає загальну таблицю стилів для застосунку.

    Returns:
        QSS stylesheet
    """
    return """
    /* Загальні налаштування */
    QMainWindow {
        background-color: #f5f5f5;
    }

    /* Меню */
    QMenuBar {
        background-color: #ffffff;
        border-bottom: 1px solid #e0e0e0;
        padding: 4px;
    }

    QMenuBar::item {
        background-color: transparent;
        padding: 6px 12px;
        border-radius: 4px;
    }

    QMenuBar::item:selected {
        background-color: #e3f2fd;
        color: #1976d2;
    }

    QMenuBar::item:pressed {
        background-color: #bbdefb;
    }

    QMenu {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        padding: 4px;
    }

    QMenu::item {
        padding: 6px 24px 6px 12px;
        border-radius: 3px;
    }

    QMenu::item:selected {
        background-color: #e3f2fd;
        color: #1976d2;
    }

    QMenu::separator {
        height: 1px;
        background-color: #e0e0e0;
        margin: 4px 8px;
    }

    /* Панель інструментів */
    QToolBar {
        background-color: #ffffff;
        border: none;
        border-bottom: 1px solid #e0e0e0;
        spacing: 4px;
        padding: 4px;
    }

    QToolButton {
        background-color: transparent;
        border: 1px solid transparent;
        border-radius: 4px;
        padding: 6px 12px;
        color: #424242;
    }

    QToolButton:hover {
        background-color: #e3f2fd;
        border-color: #bbdefb;
        color: #1976d2;
    }

    QToolButton:pressed {
        background-color: #bbdefb;
        border-color: #90caf9;
    }

    /* Таблиця */
    QTableWidget {
        background-color: #ffffff;
        alternate-background-color: #fafafa;
        gridline-color: #e0e0e0;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        selection-background-color: #e3f2fd;
        selection-color: #212121;
        font-size: 13px;
    }

    QTableWidget::item {
        border: none;
    }

    QTableWidget::item:selected {
        background-color: #e3f2fd;
        color: #212121;
    }

    QTableWidget::item:focus {
        background-color: #bbdefb;
        border: 2px solid #1976d2;
    }

    /* Редактор клітинок таблиці */
    QTableWidget QLineEdit {
        background-color: #ffffff;
        border: 2px solid #1976d2;
        border-radius: 3px;
        padding: 8px;
        font-size: 13px;
        selection-background-color: #bbdefb;
    }

    /* Заголовки таблиці */
    QHeaderView::section {
        background-color: #f5f5f5;
        color: #616161;
        padding: 10px;
        border: none;
        border-right: 1px solid #e0e0e0;
        border-bottom: 1px solid #e0e0e0;
        font-weight: bold;
        font-size: 13px;
        min-height: 35px;
    }

    QHeaderView::section:hover {
        background-color: #eeeeee;
    }

    QHeaderView::section:pressed {
        background-color: #e0e0e0;
    }

    /* Рядок стану */
    QStatusBar {
        background-color: #ffffff;
        border-top: 1px solid #e0e0e0;
        color: #616161;
        padding: 4px;
    }

    /* Кнопки */
    QPushButton {
        background-color: #1976d2;
        color: #ffffff;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: bold;
        min-width: 80px;
    }

    QPushButton:hover {
        background-color: #1565c0;
    }

    QPushButton:pressed {
        background-color: #0d47a1;
    }

    QPushButton:disabled {
        background-color: #e0e0e0;
        color: #9e9e9e;
    }

    /* Вторинні кнопки */
    QPushButton[buttonStyle="secondary"] {
        background-color: #ffffff;
        color: #1976d2;
        border: 1px solid #1976d2;
    }

    QPushButton[buttonStyle="secondary"]:hover {
        background-color: #e3f2fd;
    }

    QPushButton[buttonStyle="secondary"]:pressed {
        background-color: #bbdefb;
    }

    /* Діалоги */
    QDialog {
        background-color: #ffffff;
    }

    /* Поля вводу */
    QLineEdit, QSpinBox {
        background-color: #ffffff;
        border: 1px solid #bdbdbd;
        border-radius: 4px;
        selection-background-color: #bbdefb;
    }

    QLineEdit:focus, QSpinBox:focus {
        border-color: #1976d2;
        border-width: 2px;
    }

    QLineEdit:disabled, QSpinBox:disabled {
        background-color: #f5f5f5;
        color: #9e9e9e;
    }

    /* Мітки */
    QLabel {
        color: #424242;
    }

    /* Текстовий браузер */
    QTextBrowser {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        selection-background-color: #bbdefb;
    }

    /* Прокрутка */
    QScrollBar:vertical {
        background-color: #f5f5f5;
        width: 12px;
        border-radius: 6px;
    }

    QScrollBar::handle:vertical {
        background-color: #bdbdbd;
        border-radius: 6px;
        min-height: 20px;
    }

    QScrollBar::handle:vertical:hover {
        background-color: #9e9e9e;
    }

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }

    QScrollBar:horizontal {
        background-color: #f5f5f5;
        height: 12px;
        border-radius: 6px;
    }

    QScrollBar::handle:horizontal {
        background-color: #bdbdbd;
        border-radius: 6px;
        min-width: 20px;
    }

    QScrollBar::handle:horizontal:hover {
        background-color: #9e9e9e;
    }

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px;
    }
    """


def get_table_cell_error_style() -> str:
    """
    Повертає стиль для клітинок з помилками.

    Returns:
        CSS стиль для background
    """
    return "background-color: #ffcdd2;"  # Світло-червоний


def get_table_cell_normal_style() -> str:
    """
    Повертає стиль для нормальних клітинок.

    Returns:
        CSS стиль для background
    """
    return "background-color: #ffffff;"  # Білий


def get_table_cell_formula_style() -> str:
    """
    Повертає стиль для клітинок з формулами (у режимі виразів).

    Returns:
        CSS стиль для background
    """
    return "background-color: #e8f5e9;"  # Світло-зелений


def get_table_cell_literal_style() -> str:
    """
    Повертає стиль для клітинок з літералами.

    Returns:
        CSS стиль для background
    """
    return "background-color: #fff9c4;"  # Світло-жовтий
