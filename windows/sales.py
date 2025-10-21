from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
)

from .base import BaseWindow
from .. import storage
from ..forms import RegisterSaleDialog


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
        actions.addStretch(1)

        main_layout.insertLayout(1, actions)

        self.sales_table = QTableWidget(0, 6)
        self.sales_table.setHorizontalHeaderLabels(
            ["Date", "Id", "Name", "Qty", "$ Price", "C$ Price"]
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

        main_layout.addWidget(self.sales_table)

        self.register_button.clicked.connect(self.open_register_sales_dialog)
        self.refresh_sales_table()

    def open_register_sales_dialog(self) -> None:
        dialog = RegisterSaleDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_sales_table()

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
            id_item.setData(Qt.ItemDataRole.UserRole, sale["sale_id"])
            name_item = QTableWidgetItem(sale["name"])

            qty = int(sale["qty"])
            price_usd = float(sale["price"])
            price_cad = price_usd * rate

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
            self.sales_table.setItem(row, 3, qty_item)
            self.sales_table.setItem(row, 4, usd_item)
            self.sales_table.setItem(row, 5, cad_item)