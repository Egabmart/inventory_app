from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLineEdit, QMessageBox, QPushButton

from .base import BaseWindow
from .. import storage
from ..forms import EditProductDialog


class SearchWindow(BaseWindow):
    def __init__(self) -> None:
        super().__init__("Search - My App", "Search")
        self.set_page_title("Search Products")

        main_layout = self.content_layout

        search_row = QHBoxLayout()
        search_row.setContentsMargins(0, 0, 0, 0)
        search_row.setSpacing(12)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Enter product id")
        self.search_button = QPushButton("Search")

        search_row.addWidget(self.search_edit)
        search_row.addWidget(self.search_button)
        search_row.addStretch(1)

        main_layout.insertLayout(1, search_row)

        self.search_button.clicked.connect(self.search_product)
        self.search_edit.returnPressed.connect(self.search_product)

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        self.search_edit.setFocus(Qt.FocusReason.OtherFocusReason)
        self.search_edit.selectAll()

    def search_product(self) -> None:
        code = self.search_edit.text().strip()
        if not code:
            return

        product = storage.get_product_by_id(code)
        if not product:
            QMessageBox.information(self, "Not found", "Product isn't listed")
            return

        dialog = EditProductDialog(product, self, readonly=True)
        dialog.exec()