from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from .base import BaseWindow
from .. import storage
from ..forms import RegisterSaleDialog

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
            ("Department", sale.get("department", "")),
            ("Subdepartment", sale.get("subdepartment", "")),
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
        super().__init__("Sales - Inventory App", "Sales")
        self.set_page_title("Register Sales")

        main_layout = self.content_layout

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(12)

        self._departments = []

        self.department_label = QLabel("Department:")
        self.department_filter = QComboBox()
        self.department_filter.setMinimumWidth(160)

        self.subdepartment_label = QLabel("Subdepartment:")
        self.subdepartment_filter = QComboBox()
        self.subdepartment_filter.setMinimumWidth(160)
        self.subdepartment_filter.setEnabled(False)

        self.location_label = QLabel("Location:")
        self.location_filter = QComboBox()
        self.location_filter.setMinimumWidth(140)

        actions.addWidget(self.department_label)
        actions.addWidget(self.department_filter)
        actions.addWidget(self.subdepartment_label)
        actions.addWidget(self.subdepartment_filter)
        actions.addWidget(self.location_label)
        actions.addWidget(self.location_filter)

        self.register_button = QPushButton("Register sales")
        actions.addWidget(self.register_button)
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

        self.department_filter.currentIndexChanged.connect(self._on_department_changed)
        self.subdepartment_filter.currentIndexChanged.connect(self.refresh_sales_table)
        self.location_filter.currentIndexChanged.connect(self.refresh_sales_table)
        self.register_button.clicked.connect(self.open_register_sales_dialog)
        self.sales_table.cellClicked.connect(self._open_sale_details)
        
        self._reload_filters()
        self.refresh_sales_table()

    def open_register_sales_dialog(self) -> None:
        dialog = RegisterSaleDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._reload_filters()
            self.refresh_sales_table()

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        self._reload_filters()
        self.refresh_sales_table()

    def refresh_sales_table(self) -> None:
        department_id = self.department_filter.currentData()
        if not isinstance(department_id, int):
            department_id = None

        subdepartment_id = self.subdepartment_filter.currentData()
        if not isinstance(subdepartment_id, int):
            subdepartment_id = None

        location_data = self.location_filter.currentData()
        location_type = None
        local_id = None
        if isinstance(location_data, tuple) and len(location_data) == 2:
            location_type, local_id = location_data
        elif isinstance(location_data, dict):
            location_type = location_data.get("type")
            local_id = location_data.get("id")

        if location_type is not None:
            location_type = str(location_type)

        local_id = int(local_id) if isinstance(local_id, int) else None

        sales = storage.list_sold_products(
            department_id=department_id,
            subdepartment_id=subdepartment_id,
            location_type=location_type,
            local_id=local_id,
        )
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
                "department": sale.get("department_name") or "",
                "subdepartment": sale.get("subdepartment_name") or "",
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

    def _reload_filters(self) -> None:
        self._reload_department_filter()
        self._reload_location_filter()

    def _reload_department_filter(self) -> None:
        selected_dept = self.department_filter.currentData()
        self._departments = storage.list_departments()

        self.department_filter.blockSignals(True)
        self.department_filter.clear()
        self.department_filter.addItem("All departments", None)

        selected_index = 0
        for idx, dept in enumerate(self._departments, start=1):
            self.department_filter.addItem(dept.name, dept.dept_id)
            if selected_dept == dept.dept_id:
                selected_index = idx

        self.department_filter.setCurrentIndex(selected_index)
        self.department_filter.blockSignals(False)

        current_dept = self.department_filter.currentData()
        if not isinstance(current_dept, int):
            current_dept = None
        self._reload_subdepartment_filter(current_dept)

    def _reload_subdepartment_filter(self, department_id: int | None) -> None:
        selected_sub = self.subdepartment_filter.currentData()

        self.subdepartment_filter.blockSignals(True)
        self.subdepartment_filter.clear()
        self.subdepartment_filter.addItem("All subdepartments", None)

        if department_id is None:
            self.subdepartment_filter.setEnabled(False)
            selected_index = 0
        else:
            dept = next(
                (d for d in self._departments if d.dept_id == department_id),
                None,
            )
            subs = storage.list_subdepartments(dept) if dept else []
            selected_index = 0
            for idx, sub in enumerate(subs, start=1):
                self.subdepartment_filter.addItem(sub.name, sub.sub_id)
                if selected_sub == sub.sub_id:
                    selected_index = idx
            self.subdepartment_filter.setEnabled(True)

        self.subdepartment_filter.setCurrentIndex(selected_index)
        self.subdepartment_filter.blockSignals(False)

    def _reload_location_filter(self) -> None:
        selected_location = self.location_filter.currentData()
        locations = storage.list_locals()

        self.location_filter.blockSignals(True)
        self.location_filter.clear()

        options: list[tuple[str, tuple[str | None, int | None]]] = [
            ("All locations", (None, None)),
            ("Online", ("online", None)),
        ]
        for loc in locations:
            options.append((loc.name, ("local", loc.local_id)))

        selected_index = 0
        for idx, (label, data) in enumerate(options):
            self.location_filter.addItem(label, data)
            if selected_location == data:
                selected_index = idx

        self.location_filter.setCurrentIndex(selected_index)
        self.location_filter.blockSignals(False)

    def _on_department_changed(self) -> None:
        current_dept = self.department_filter.currentData()
        if not isinstance(current_dept, int):
            current_dept = None
        self._reload_subdepartment_filter(current_dept)
        self.refresh_sales_table()
        
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