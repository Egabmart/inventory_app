from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
)

from .base import BaseWindow
try:  # Maintain compatibility with frozen builds lacking package parents
    from .. import storage
    from ..forms import EditProductDialog
    from ..models import Product
except ImportError:  # pragma: no cover - fallback for frozen build
    import storage  # type: ignore[import-not-found]
    from forms import EditProductDialog  # type: ignore[import-not-found]
    from models import Product  # type: ignore[import-not-found]


class SearchWindow(BaseWindow):
    def __init__(self) -> None:
        super().__init__("Search - Inventory App", "Search")
        self.set_page_title("Search Products")

        main_layout = self.content_layout

        search_row = QHBoxLayout()
        search_row.setContentsMargins(0, 0, 0, 0)
        search_row.setSpacing(12)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search by product id or name")
        self.search_button = QPushButton("Search")

        search_row.addWidget(self.search_edit)
        search_row.addWidget(self.search_button)
        search_row.addStretch(1)

        main_layout.insertLayout(1, search_row)

        self.results_table = QTableWidget(0, 5)
        self.results_table.setHorizontalHeaderLabels([
            "Id",
            "Name",
            "$ Price",
            "C$ Price",
            "Quantity",
        ])
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.results_table.verticalHeader().setVisible(False)

        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        main_layout.addWidget(self.results_table)

        self._results: list[Product] = []


        self.search_button.clicked.connect(self.search_product)
        self.search_edit.returnPressed.connect(self.search_product)
        self.results_table.cellDoubleClicked.connect(lambda *_: self.open_selected_product())

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        self.search_edit.setFocus(Qt.FocusReason.OtherFocusReason)
        self.search_edit.selectAll()

    def search_product(self) -> None:
        query = self.search_edit.text().strip()
        if not query:
            self._results = []
            self.results_table.setRowCount(0)
            return

        rate = storage.get_conversion_rate()
        self._results = storage.search_products(query)
        self.results_table.setRowCount(0)

        for product in self._results:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)

            price_usd = float(product.price)
            price_c = price_usd * float(rate)
            qty = int(product.quantity)

            id_item = QTableWidgetItem(product.prod_id)
            id_item.setData(Qt.ItemDataRole.UserRole, product.prod_id)
            name_item = QTableWidgetItem(product.name)
            usd_item = QTableWidgetItem(f"{price_usd:.2f}")
            usd_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            cad_item = QTableWidgetItem(f"{price_c:.2f}")
            cad_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            qty_item = QTableWidgetItem(str(qty))
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            self.results_table.setItem(row, 0, id_item)
            self.results_table.setItem(row, 1, name_item)
            self.results_table.setItem(row, 2, usd_item)
            self.results_table.setItem(row, 3, cad_item)
            self.results_table.setItem(row, 4, qty_item)

    def open_selected_product(self) -> None:
        row = self.results_table.currentRow()
        if row < 0 or row >= len(self._results):
            return
        
        product = self._results[row]
        dialog = EditProductDialog(product, self, readonly=True)
        dialog.exec()