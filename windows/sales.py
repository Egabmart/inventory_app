from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from .base import BaseWindow
from .. import storage
from ..forms import RegisterSaleDialog
from ..forms import CreateInvoiceDialog, RegisterSaleDialog

class SaleDetailsDialog(QDialog):
    def __init__(self, sale: dict, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Sale Details")
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Field", "Value"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setWordWrap(True)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.table)

        rows = [
            ("Product ID", sale.get("prod_id", "")),
            ("Product name", sale.get("name", "")),
            ("Product description", sale.get("description", "")),
            ("Quantity", str(sale.get("qty", ""))),
            ("Price in C$", sale.get("price_cad", "")),
            ("Price in $", sale.get("price_usd", "")),
            ("Date", sale.get("sold_on", "")),
            ("Location", sale.get("location", "")),
            ("Client name", sale.get("client", "")),
        ]

        for label, value in rows:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            label_item = QTableWidgetItem(label)
            label_item.setFlags(label_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            value_item = QTableWidgetItem(str(value))
            value_item.setFlags(value_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, 0, label_item)
            self.table.setItem(row_idx, 1, value_item)

        actions = QHBoxLayout()
        actions.addStretch(1)
        back_button = QPushButton("Back")
        back_button.clicked.connect(self.accept)
        actions.addWidget(back_button)

        layout.addLayout(actions)



class SalesWindow(BaseWindow):
    def __init__(self) -> None:
        super().__init__("Sales - My App", "Sales")
        self.set_page_title("Register Sales")

        main_layout = self.content_layout

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(12)

        self.register_button = QPushButton("Register sales")
        actions.addWidget(self.register_button)
        
        self.create_invoice_button = QPushButton("Create Invoice")
        actions.addWidget(self.create_invoice_button)
        actions.addStretch(1)

        main_layout.insertLayout(1, actions)

        self.sales_table = QTableWidget(0, 7)
        self.sales_table.setHorizontalHeaderLabels(
            ["Date", "Id", "Name", "Location", "Qty", "$ Price", "C$ Price"]
        )
        self.sales_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.sales_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.sales_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.sales_table.verticalHeader().setVisible(False)

        header = self.sales_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        main_layout.addWidget(self.sales_table)

        self.register_button.clicked.connect(self.open_register_sales_dialog)
        self.create_invoice_button.clicked.connect(self.open_create_invoice_dialog)
        self.sales_table.cellClicked.connect(self._open_sale_details)
        self.refresh_sales_table()

    def open_register_sales_dialog(self) -> None:
        dialog = RegisterSaleDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_sales_table()

    def open_create_invoice_dialog(self) -> None:
        dialog = CreateInvoiceDialog(self)
        dialog.exec()

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        self.refresh_sales_table()

    def refresh_sales_table(self) -> None:
        sales = storage.list_sold_products()
        rate = float(storage.get_conversion_rate())

        self.sales_table.setRowCount(0)

        for sale in sales:
            row = self.sales_table.rowCount()
            self.sales_table.insertRow(row)

            date_item = QTableWidgetItem(sale.get("sold_on") or "")
            id_item = QTableWidgetItem(sale["prod_id"])
            name_item = QTableWidgetItem(sale["name"])

            location = self._format_location(sale)
            qty = int(sale["qty"])
            price_usd = float(sale["price"])
            price_cad = price_usd * rate

            sale_details = {
                "sale_id": sale["sale_id"],
                "prod_id": sale["prod_id"],
                "name": sale["name"],
                "description": sale.get("description") or "",
                "qty": str(qty),
                "price_usd": f"{price_usd:.2f}",
                "price_cad": f"{price_cad:.2f}",
                "sold_on": sale.get("sold_on") or "",
                "location": location,
                "client": sale.get("client") or "",
            }

            date_item.setData(Qt.ItemDataRole.UserRole, sale_details)

            location_item = QTableWidgetItem(location)

            qty_item = QTableWidgetItem(str(qty))
            qty_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )

            usd_item = QTableWidgetItem(f"{price_usd:.2f}")
            usd_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )

            cad_item = QTableWidgetItem(f"{price_cad:.2f}")
            cad_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )

            self.sales_table.setItem(row, 0, date_item)
            self.sales_table.setItem(row, 1, id_item)
            self.sales_table.setItem(row, 2, name_item)
            self.sales_table.setItem(row, 3, location_item)
            self.sales_table.setItem(row, 4, qty_item)
            self.sales_table.setItem(row, 5, usd_item)
            self.sales_table.setItem(row, 6, cad_item)

    def _format_location(self, sale: dict) -> str:
        location_type = (sale.get("location_type") or "").strip().lower()
        if location_type == "local":
            local_name = sale.get("local_name") or "Local"
            return local_name
        if location_type == "online":
            return "Online"
        return location_type.capitalize() if location_type else ""

    def _open_sale_details(self, row: int, column: int) -> None:
        del column
        item = self.sales_table.item(row, 0)
        if not item:
            return
        sale = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(sale, dict):
            return
        dialog = SaleDetailsDialog(sale, self)
        dialog.exec()