from __future__ import annotations

from typing import Callable, ClassVar, Dict, List
from html import escape
from pathlib import Path

from PyQt6.QtCore import QMarginsF,Qt
from PyQt6.QtGui import QTextDocument, QPageLayout, QIcon
from PyQt6.QtWidgets import (
    QButtonGroup,
    QGridLayout,
    QFileDialog,
    QLabel,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtPrintSupport import QPrinter

from .. import storage


class NavButton(QPushButton):
    """Navigation button styled to match the refreshed layout."""

    def __init__(self, text: str, *, checkable: bool = True, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setCheckable(checkable)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(40)
        self.setStyleSheet(
            """
            QPushButton {
                color: #e9f2ef;
                background: transparent;
                border: none;
                text-align: left;
                padding: 10px 12px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
            }
            QPushButton:checked {
                background: #67b7aa;
                color: #ffffff;
            }
        """
        )


APP_NAME = "Inventory App"
APP_ICON_PATH = Path(__file__).resolve().parent.parent / "Assets" / "Inventory_app_logo.png"
APP_ICON = QIcon(str(APP_ICON_PATH))

class BaseWindow(QMainWindow):
    """Shared application window layout with top navigation."""

    _open_windows: ClassVar[List["BaseWindow"]] = []

    def __init__(self, title: str, current_section: str) -> None:
        super().__init__()
        self.setWindowTitle(title)
        if not APP_ICON.isNull():
            self.setWindowIcon(APP_ICON)
        self.resize(1100, 720)
        self._current_section = current_section

        storage.init_db()

        central = QWidget()
        central.setObjectName("MainBackground")
        grid = QGridLayout(central)
        grid.setContentsMargins(16, 16, 16, 16)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        # ---- Top bar ------------------------------------------------------
        topbar = QWidget()
        topbar.setObjectName("TopBar")
        top_layout = QHBoxLayout(topbar)
        top_layout.setContentsMargins(16, 8, 16, 8)
        top_layout.setSpacing(12)

        self._brand_label = QLabel(APP_NAME)
        self._brand_label.setStyleSheet(
            "background: transparent; color: white; font-weight: 600; font-size: 18px;"
        )
        top_layout.addWidget(self._brand_label)
        top_layout.addStretch(1)

        grid.addWidget(topbar, 0, 0, 1, 2)

        # ---- Sidebar -----------------------------------------------------
        sidebar = QWidget()
        sidebar.setObjectName("SideBar")
        sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 12, 12, 12)
        sidebar_layout.setSpacing(8)

    
        self.depts_btn = NavButton("Departments")
        self.locals_btn = NavButton("Locals")
        self.sales_btn = NavButton("Sales")
        self.search_btn = NavButton("Search")
        sidebar_layout.addWidget(self.depts_btn)
        sidebar_layout.addWidget(self.locals_btn)
        sidebar_layout.addWidget(self.sales_btn)
        sidebar_layout.addWidget(self.search_btn)
        sidebar_layout.addStretch(1)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self._nav_buttons: Dict[str, NavButton] = {
            "Departments": self.depts_btn,
            "Locals": self.locals_btn,
            "Sales": self.sales_btn,
            "Search": self.search_btn,
        }
        for button in self._nav_buttons.values():
            self.nav_group.addButton(button)

        self.depts_btn.clicked.connect(self.open_departments)
        self.locals_btn.clicked.connect(self.open_locals)
        self.sales_btn.clicked.connect(self.open_sales)
        self.search_btn.clicked.connect(self.open_search)

        grid.addWidget(sidebar, 1, 0)

        # ---- Content area ------------------------------------------------
        content = QWidget()
        content.setObjectName("Content")
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(24, 24, 24, 24)
        self._content_layout.setSpacing(16)

        self._page_title = QLabel()
        self._page_title.setStyleSheet("background: transparent; font-size: 26px; font-weight: 700; color: #1a1a1a;")
        self._page_title.setContentsMargins(0, 0, 0, 8)
        self._content_layout.addWidget(self._page_title)

        grid.addWidget(content, 1, 1)

        grid.setRowStretch(0, 0)
        grid.setRowStretch(1, 1)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)

        self.setCentralWidget(central)
        self.setStyleSheet(
            """
            QWidget#MainBackground { background: #f5f6f8; }

            #TopBar {
                background: #4ca797;
                border-radius: 10px;
            }

            #SideBar {
                background: #2f7f75;
                border-radius: 10px;
            }

            #Content {
                background: #ffffff;
                border-radius: 10px;
            }
        """
        )

        self.set_page_title(current_section)
        self._apply_section_state()
        self._register_window(self)

    # ---- navigation helpers -------------------------------------------------
    def _apply_section_state(self) -> None:
        for name, button in self._nav_buttons.items():
            button.setChecked(name == self._current_section)

    @classmethod
    def _register_window(cls, window: "BaseWindow") -> None:
        cls._open_windows.append(window)

        def _on_destroyed(*_: object) -> None:
            try:
                cls._open_windows.remove(window)
            except ValueError:
                pass

        window.destroyed.connect(_on_destroyed)
        
    def _open_window(self, factory: Callable[[], "BaseWindow"]) -> None:
        next_window = factory()
        next_window.show()
        self.close()

    def open_departments(self) -> None:
        if self._current_section == "Departments":
            return
        from .departments import DepartmentsWindow

        self._open_window(DepartmentsWindow)

    def open_locals(self) -> None:
        if self._current_section == "Locals":
            return
        from .locals import LocalsWindow

        self._open_window(LocalsWindow)

    def open_sales(self) -> None:
        if self._current_section == "Sales":
            return
        from .sales import SalesWindow

        self._open_window(SalesWindow)

    def open_search(self) -> None:
        if self._current_section == "Search":
            return
        from .search import SearchWindow

        self._open_window(SearchWindow)

        # ---- exposed helpers ------------------------------------------------
    @property
    def content_layout(self) -> QVBoxLayout:
        return self._content_layout

    def set_page_title(self, text: str) -> None:
        self._page_title.setText(text)


def _table_headers(table: QTableWidget) -> List[str]:
    headers: List[str] = []
    for col in range(table.columnCount()):
        header_item = table.horizontalHeaderItem(col)
        headers.append(header_item.text() if header_item else f"Column {col + 1}")
    return headers


def _table_rows(table: QTableWidget) -> List[List[str]]:
    rows: List[List[str]] = []
    for row in range(table.rowCount()):
        row_data: List[str] = []
        for col in range(table.columnCount()):
            item: QTableWidgetItem | None = table.item(row, col)
            row_data.append(item.text() if item else "")
        rows.append(row_data)
    return rows


def export_table_to_xlsx(table: QTableWidget, parent: QWidget | None = None) -> None:
    """Export a QTableWidget to an Excel workbook (.xlsx)."""

    path, _ = QFileDialog.getSaveFileName(parent, "Export to Excel", "", "Excel Workbook (*.xlsx)")
    if not path:
        return
    if not path.lower().endswith(".xlsx"):
        path += ".xlsx"

    headers = _table_headers(table)
    rows = _table_rows(table)

    try:
        from openpyxl import Workbook
    except ImportError:
        QMessageBox.warning(
            parent,
            "Export failed",
            "The 'openpyxl' package is required to export to Excel. "
            "Install it with:\n\npip install openpyxl",
        )
        return

    try:
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(headers)
        for row in rows:
            sheet.append(row)
        for column_cells in sheet.columns:
            max_length = max(len(str(cell.value or "")) for cell in column_cells)
            column_letter = column_cells[0].column_letter
            sheet.column_dimensions[column_letter].width = min(60, max(12, max_length + 2))
        workbook.save(path)
    except Exception as exc:  # pragma: no cover - GUI warning
        QMessageBox.critical(parent, "Export failed", f"Could not export to Excel:\n{exc}")
        return

    QMessageBox.information(parent, "Export successful", f"Table exported to:\n{path}")


_PDF_TABLE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset=\"utf-8\">
    <style>
        body {{ font-family: Arial, Helvetica, sans-serif; font-size: 11pt; margin: 0; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #444; padding: 6px 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; font-weight: 600; }}
        tbody tr:nth-child(even) {{ background-color: #fafafa; }}
    </style>
</head>
<body>
    <table>
        <thead>
            <tr>{header}</tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
</body>
</html>
""".strip()


def _table_to_pdf_html(table: QTableWidget) -> str:
    """Build an HTML representation of a table suitable for PDF export."""

    headers = _table_headers(table)
    if headers:
        header_html = "".join(f"<th>{escape(text)}</th>" for text in headers)
    else:
        header_html = "<th>Table</th>"

    rows = _table_rows(table)
    if rows:
        row_html = [
            "<tr>" + "".join(f"<td>{escape(cell)}</td>" for cell in row) + "</tr>"
            for row in rows
        ]
    else:
        colspan = max(len(headers), 1)
        row_html = [f"<tr><td colspan=\"{colspan}\">No data available</td></tr>"]

    return _PDF_TABLE_TEMPLATE.format(header=header_html, rows="\n".join(row_html))


def export_table_to_pdf(table: QTableWidget, parent: QWidget | None = None) -> None:
    """Render a QTableWidget to a PDF file."""

    path, _ = QFileDialog.getSaveFileName(parent, "Export to PDF", "", "PDF Files (*.pdf)")
    if not path:
        return
    if not path.lower().endswith(".pdf"):
        path += ".pdf"

    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(path)
    printer.setPageMargins(QMarginsF(12, 12, 12, 12), QPageLayout.Unit.Millimeter)

    document = QTextDocument()
    document.setDocumentMargin(12)
    document.setHtml(_table_to_pdf_html(table))

    try:
        document.print(printer)
    except Exception as exc:  # pragma: no cover - GUI warning
        QMessageBox.critical(parent, "Export failed", f"Could not export to PDF:\n{exc}")
        return

    QMessageBox.information(parent, "Export successful", f"Table exported to:\n{path}")
