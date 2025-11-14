from PyQt6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget, QMessageBox
from PyQt6.QtCore import Qt
from .base import BaseWindow
try:  # Support frozen PyInstaller builds where package parents differ
    from .. import storage
    from ..forms import EditProductDialog, RegisterSaleDialog
except ImportError:  # pragma: no cover - fallback for frozen build
    import storage  # type: ignore[import-not-found]
    from forms import EditProductDialog, RegisterSaleDialog  # type: ignore[import-not-found]

class HomeWindow(BaseWindow):
    def __init__(self):
        super().__init__("Home - Inventory App", "Home")
        self.set_page_title("Home")
        main_layout = self.content_layout

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.setSpacing(12)
        self.btn_open_search = QPushButton("Search Products")
        self.btn_register_sales = QPushButton("Register sales")
        toolbar.addWidget(self.btn_open_search); toolbar.addWidget(self.btn_register_sales); toolbar.addStretch(1)
        main_layout.insertLayout(1, toolbar)
        self.search_container = QWidget(); self.search_container.setVisible(False)
        search_row = QHBoxLayout(self.search_container); search_row.setContentsMargins(0,0,0,0)
        self.search_edit = QLineEdit(); self.search_edit.setPlaceholderText("Enter product id")
        self.search_btn = QPushButton("Search")
        search_row.addWidget(self.search_edit); search_row.addWidget(self.search_btn)
        main_layout.insertWidget(2, self.search_container)
        self.btn_open_search.clicked.connect(self.toggle_search_bar)
        self.btn_register_sales.clicked.connect(self.open_register_sales)
        self.search_btn.clicked.connect(self.search_product)
        self.search_edit.returnPressed.connect(self.search_product)

    def toggle_search_bar(self):
        showing = self.search_container.isVisible()
        self.search_container.setVisible(not showing)
        if not showing:
            self.search_edit.setFocus(Qt.FocusReason.OtherFocusReason)
            self.search_edit.selectAll()

    def search_product(self):
        code = self.search_edit.text().strip()
        if not code: return
        prod = storage.get_product_by_id(code)
        if not prod:
            QMessageBox.information(self, "Not found", "Product isn't listed"); return
        dlg = EditProductDialog(prod, self, readonly=True); dlg.exec()

    def open_register_sales(self):
        dlg = RegisterSaleDialog(self); dlg.exec()
