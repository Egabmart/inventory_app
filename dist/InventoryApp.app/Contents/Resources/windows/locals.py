from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QHBoxLayout, QMessageBox, QInputDialog, QLabel, QStackedWidget
from PyQt6.QtCore import Qt
from .base import BaseWindow, export_table_to_xlsx, export_table_to_pdf
try:  # Enable execution from frozen bundles where package context is lost
    from ..models import Local
    from .. import storage
except ImportError:  # pragma: no cover - fallback for frozen build
    from models import Local  # type: ignore[import-not-found]
    import storage  # type: ignore[import-not-found]

class LocalsWindow(BaseWindow):
    def __init__(self):
        super().__init__("Locals - Inventory App", "Locals")
        self.set_page_title("Locals")
        main_layout = self.content_layout

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        # --- Locals list page -------------------------------------------------
        self.list_page = QWidget()
        list_layout = QVBoxLayout(self.list_page)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(16)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(12)
        self.add_button = QPushButton("Create Local"); self.delete_button = QPushButton("Delete Local")
        self.export_xlsx_btn = QPushButton("Export XLSX"); self.export_pdf_btn = QPushButton("Export PDF")
        btn_row.addWidget(self.add_button); btn_row.addWidget(self.delete_button)
        btn_row.addStretch(1); btn_row.addWidget(self.export_xlsx_btn); btn_row.addWidget(self.export_pdf_btn)
        list_layout.addLayout(btn_row)
        main_layout.insertLayout(1, btn_row)
        self.add_button.clicked.connect(self.show_add_form); self.delete_button.clicked.connect(self.delete_selected_local)
        self.export_xlsx_btn.clicked.connect(lambda: export_table_to_xlsx(self.table, self))
        self.export_pdf_btn.clicked.connect(lambda: export_table_to_pdf(self.table, self))

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Name", "Number of items"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader(); header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch); header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        list_layout.addWidget(self.table)

        self.stack.addWidget(self.list_page)

        # --- Local detail page ------------------------------------------------
        self.detail_page = QWidget()
        detail_layout = QVBoxLayout(self.detail_page)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(16)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(12)
        self.back_btn = QPushButton("Back"); self.retail_btn = QPushButton("Retail Rate")
        top.addWidget(self.back_btn); top.addStretch(1); top.addWidget(self.retail_btn)
        detail_layout.addLayout(top)

        self.back_btn.clicked.connect(self.show_locals_page); self.retail_btn.clicked.connect(self.change_retail_rate)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(12)
        self.remove_btn = QPushButton("Remove Product from Local")
        actions.addWidget(self.remove_btn); actions.addStretch(1)
        detail_layout.addLayout(actions)

        self.remove_btn.clicked.connect(self.remove_selected_product)

        self.prod_table = QTableWidget(0, 7)
        self.prod_table.setHorizontalHeaderLabels(["Id", "Name", "Price $", "Price C$", "Quantity", "Subtotal $", "Subtotal C$"])
        self.prod_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.prod_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.prod_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.prod_table.verticalHeader().setVisible(False)
        header = self.prod_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents); header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for i in range(2,7): header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        detail_layout.addWidget(self.prod_table)

        totals = QHBoxLayout()
        totals.setContentsMargins(0, 0, 0, 0)
        totals.setSpacing(12)
        self.total_items_lbl = QLabel("Items: 0"); self.total_qty_lbl = QLabel("Total quantity: 0")
        self.total_usd_lbl = QLabel("Total price $: 0.00"); self.total_c_lbl = QLabel("Total price C$: 0.00")
        self.sum_sub_usd_lbl = QLabel("Subtotal $ (sum): 0.00"); self.sum_sub_c_lbl = QLabel("Subtotal C$ (sum): 0.00")
        totals.addWidget(self.total_items_lbl); totals.addStretch(1); totals.addWidget(self.total_qty_lbl); totals.addStretch(1)
        totals.addWidget(self.total_usd_lbl); totals.addWidget(self.total_c_lbl); totals.addWidget(self.sum_sub_usd_lbl); totals.addWidget(self.sum_sub_c_lbl)
        detail_layout.addLayout(totals)

        self.stack.addWidget(self.detail_page)

        storage.init_db()
        self.active_local: Local | None = None
        self.products: list = []
        self.refresh_locals()
        self.stack.setCurrentWidget(self.list_page)
        self.table.cellDoubleClicked.connect(self.open_local_detail)

    def refresh_locals(self):
        self.locals = storage.list_locals(); self.table.setRowCount(0)
        for loc in self.locals:
            row = self.table.rowCount(); self.table.insertRow(row)
            name_item = QTableWidgetItem(loc.name); name_item.setData(Qt.ItemDataRole.UserRole, loc.local_id)
            cnt = storage.count_local_products(loc); cnt_item = QTableWidgetItem(str(cnt)); cnt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 0, name_item); self.table.setItem(row, 1, cnt_item)

    def show_add_form(self):
        name, ok = QInputDialog.getText(self, "Create Local", "Local name:")
        if ok and name.strip(): storage.add_local(name.strip()); self.refresh_locals()

    def open_local_detail(self, row: int, _col: int):
        local_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        loc = next((l for l in self.locals if l.local_id == local_id), None)
        if not loc:
            return
        self.active_local = loc
        self.set_page_title(f"{loc.name} - Products")
        self.refresh_products()
        self.stack.setCurrentWidget(self.detail_page)

    def current_local(self):
        row = self.table.currentRow()
        if row < 0: return None
        local_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        return next((l for l in self.locals if l.local_id == local_id), None)

    def delete_selected_local(self):
        loc = self.current_local()
        if not loc: return
        confirm = QMessageBox.question(self, "Delete Local", f"Delete local '{loc.name}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            storage.delete_local(loc); self.refresh_locals()

    def show_locals_page(self):
        self.active_local = None
        self.set_page_title("Locals")
        self.refresh_locals()
        self.stack.setCurrentWidget(self.list_page)

    def refresh_products(self):
        if not self.active_local:
            self.products = []
            self.prod_table.setRowCount(0)
            self.total_items_lbl.setText("Items: 0"); self.total_qty_lbl.setText("Total quantity: 0")
            self.total_usd_lbl.setText("Total price $: 0.00"); self.total_c_lbl.setText("Total price C$: 0.00")
            self.sum_sub_usd_lbl.setText("Subtotal $ (sum): 0.00"); self.sum_sub_c_lbl.setText("Subtotal C$ (sum): 0.00")
            return
        conv = storage.get_conversion_rate(); retail_pct = storage.get_local_retail_rate(self.active_local)
        self.products = storage.list_products_for_local(self.active_local)
       
        self.prod_table.setRowCount(0); items = len(self.products); total_qty=0; total_usd=0.0; total_c=0.0
        for p in self.products:
            row = self.prod_table.rowCount(); self.prod_table.insertRow(row)
            base_usd = float(p.price); retail_usd = base_usd * (1.0 + float(retail_pct)/100.0); retail_c = retail_usd * float(conv)
            qty = int(p.quantity); subtotal_usd = retail_usd * qty; subtotal_c = retail_c * qty
            total_qty += qty; total_usd += subtotal_usd; total_c += subtotal_c
            id_item = QTableWidgetItem(p.prod_id); id_item.setData(Qt.ItemDataRole.UserRole, p.prod_id)
            name_item = QTableWidgetItem(p.name)
            usd_item = QTableWidgetItem(f"{retail_usd:.2f}"); usd_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            cord_item = QTableWidgetItem(f"{retail_c:.2f}"); cord_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            qty_item = QTableWidgetItem(str(qty)); qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            sub_usd_item = QTableWidgetItem(f"{subtotal_usd:.2f}"); sub_usd_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            sub_c_item = QTableWidgetItem(f"{subtotal_c:.2f}"); sub_c_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.prod_table.setItem(row, 0, id_item); self.prod_table.setItem(row, 1, name_item)
            self.prod_table.setItem(row, 2, usd_item); self.prod_table.setItem(row, 3, cord_item)
            self.prod_table.setItem(row, 4, qty_item); self.prod_table.setItem(row, 5, sub_usd_item); self.prod_table.setItem(row, 6, sub_c_item)
        self.total_items_lbl.setText(f"Items: {items}"); self.total_qty_lbl.setText(f"Total quantity: {total_qty}")
        self.total_usd_lbl.setText(f"Total price $: {total_usd:.2f}"); self.total_c_lbl.setText(f"Total price C$: {total_c:.2f}")
        self.sum_sub_usd_lbl.setText(f"Subtotal $ (sum): {total_usd:.2f}"); self.sum_sub_c_lbl.setText(f"Subtotal C$ (sum): {total_c:.2f}")
        try:
            pct = float(storage.get_local_retail_rate(self.active_local))
            self.set_page_title(f"{self.active_local.name} - Products (Retail {pct:.2f}%)")
        except Exception:
            self.set_page_title(f"{self.active_local.name} - Products")

    def current_product(self):
        row = self.prod_table.currentRow()
        if row < 0: return None
        prod_id = self.prod_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        return next((p for p in self.products if p.prod_id == prod_id), None)

    def remove_selected_product(self):
        if not self.active_local:
            return
        prod = self.current_product()
        if not prod: return
        confirm = QMessageBox.question(self, "Remove Product", f"Remove '{prod.name}' from local '{self.active_local.name}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            storage.remove_product_from_local(self.active_local, prod); self.refresh_products(); self.refresh_locals()

    def change_retail_rate(self):
        if not self.active_local:
            return
        current = storage.get_local_retail_rate(self.active_local)
        value, ok = QInputDialog.getDouble(self, "Retail Rate", "Add-on percentage (%)\n(e.g., 10 = +10%)", float(current), -1000.0, 1000.0, 2)
        if ok:
            storage.set_local_retail_rate(self.active_local, float(value)); self.refresh_products()
