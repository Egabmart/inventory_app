from __future__ import annotations

from typing import Callable, ClassVar, List
from html import escape
from PyQt6.QtCore import QMarginsF
from PyQt6.QtGui import QTextDocument, QPageLayout
from PyQt6.QtWidgets import (
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


class BaseWindow(QMainWindow):
    """Shared application window layout with top navigation."""

    _open_windows: ClassVar[List["BaseWindow"]] = []

    def __init__(self, title: str, current_section: str) -> None:
        super().__init__()
        self.setWindowTitle(title)
        self.resize(1024, 720)
        self._current_section = current_section

        storage.init_db()

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        nav = QHBoxLayout()
        nav.setSpacing(8)

        title_lbl = QLabel("Inventory Manager")
        title_font = title_lbl.font()
        title_font.setPointSize(title_font.pointSize() + 2)
        title_font.setBold(True)
        title_lbl.setFont(title_font)
        nav.addWidget(title_lbl)
        nav.addStretch(1)

        self.home_btn = QPushButton("Home")
        self.depts_btn = QPushButton("Departments")
        self.locals_btn = QPushButton("Locals")

        self.home_btn.clicked.connect(self.open_home)
        self.depts_btn.clicked.connect(self.open_departments)
        self.locals_btn.clicked.connect(self.open_locals)

        nav.addWidget(self.home_btn)
        nav.addWidget(self.depts_btn)
        nav.addWidget(self.locals_btn)

        layout.addLayout(nav)
        self.setCentralWidget(central)

        self._apply_section_state()
        self._register_window(self)

    # ---- navigation helpers -------------------------------------------------
    def _apply_section_state(self) -> None:
        buttons = {
            "Home": self.home_btn,
            "Departments": self.depts_btn,
            "Locals": self.locals_btn,
        }
        for name, button in buttons.items():
            is_current = name == self._current_section
            button.setEnabled(not is_current)
            button.setStyleSheet("font-weight: 600;" if is_current else "")

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

    def open_home(self) -> None:
        if self._current_section == "Home":
            return
        from .home import HomeWindow

        self._open_window(HomeWindow)

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
