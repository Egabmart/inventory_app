from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QHBoxLayout,
    QMessageBox,
    QInputDialog,
    QLabel,
    QStackedWidget,
)
from PyQt6.QtCore import Qt
from .base import BaseWindow, export_table_to_xlsx, export_table_to_pdf
try:  # Allow running when package layout is flattened by PyInstaller
    from ..forms import (
        AddDepartmentForm,
        AddSubDepartmentForm,
        AddProductForm,
        EditProductDialog,
        EditSubDepartmentNameDialog,
    )
    from ..models import Department, SubDepartment, Product
    from .. import storage
except ImportError:  # pragma: no cover - fallback for frozen build
    from forms import (  # type: ignore[import-not-found]
        AddDepartmentForm,
        AddSubDepartmentForm,
        AddProductForm,
        EditProductDialog,
        EditSubDepartmentNameDialog,
    )
    from models import Department, SubDepartment, Product  # type: ignore[import-not-found]
    import storage  # type: ignore[import-not-found]

class DepartmentsWindow(BaseWindow):
    def __init__(self):
        super().__init__("Departments - Inventory App", "Departments")
        self.set_page_title("Departments")
        main_layout = self.content_layout
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        # --- Departments page -------------------------------------------------
        self.dept_page = QWidget()
        dept_layout = QVBoxLayout(self.dept_page)
        dept_layout.setContentsMargins(0, 0, 0, 0)
        dept_layout.setSpacing(16)
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(12)
        self.add_button = QPushButton("Create Department")
        self.rename_button = QPushButton("Rename Department")
        self.delete_button = QPushButton("Delete Department")
        self.export_xlsx_btn = QPushButton("Export XLSX"); self.export_pdf_btn = QPushButton("Export PDF")
        btn_row.addWidget(self.add_button); btn_row.addWidget(self.rename_button); btn_row.addWidget(self.delete_button)
        btn_row.addStretch(1); btn_row.addWidget(self.export_xlsx_btn); btn_row.addWidget(self.export_pdf_btn)
        dept_layout.addLayout(btn_row)
        self.add_button.clicked.connect(self.show_add_form)
        self.rename_button.clicked.connect(self.rename_selected_dept)
        self.delete_button.clicked.connect(self.delete_selected_dept)
        self.export_xlsx_btn.clicked.connect(lambda: export_table_to_xlsx(self.table, self))
        self.export_pdf_btn.clicked.connect(lambda: export_table_to_pdf(self.table, self))
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Name", "Number of items"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        dept_layout.addWidget(self.table)

        self.stack.addWidget(self.dept_page)

        # --- Sub-departments page --------------------------------------------
        self.sub_page = QWidget()
        sub_layout = QVBoxLayout(self.sub_page)
        sub_layout.setContentsMargins(0, 0, 0, 0)
        sub_layout.setSpacing(16)

        sub_top = QHBoxLayout()
        sub_top.setContentsMargins(0, 0, 0, 0)
        sub_top.setSpacing(12)
        self.back_button = QPushButton("Back")
        self.add_sub_button = QPushButton("Add Sub Department")
        sub_top.addWidget(self.back_button)
        sub_top.addStretch(1)
        sub_top.addWidget(self.add_sub_button)
        sub_layout.addLayout(sub_top)

        self.sub_table = QTableWidget(0, 2)
        self.sub_table.setHorizontalHeaderLabels(["Name", "Number of items"])
        self.sub_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.sub_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sub_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.sub_table.verticalHeader().setVisible(False)
        sub_header = self.sub_table.horizontalHeader()
        sub_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        sub_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        sub_layout.addWidget(self.sub_table)

        self.stack.addWidget(self.sub_page)

         # --- Products page ---------------------------------------------------
        self.detail_page = SubDepartmentDetailWindow(self)
        self.stack.addWidget(self.detail_page)
        storage.init_db()
        self.active_department: Department | None = None
        self.refresh_departments()
        self.stack.setCurrentWidget(self.dept_page)
        self.table.cellDoubleClicked.connect(self.open_department_detail)
        self.back_button.clicked.connect(self.show_departments_page)
        self.add_sub_button.clicked.connect(self.show_add_sub_form)
        self.sub_table.cellDoubleClicked.connect(self.open_sub_detail)

    def refresh_departments(self):
        self.depts = storage.list_departments(); self.table.setRowCount(0)
        for d in self.depts:
            row = self.table.rowCount(); self.table.insertRow(row)
            name_item = QTableWidgetItem(d.name); name_item.setData(Qt.ItemDataRole.UserRole, d.dept_id)
            cnt = len(storage.list_subdepartments(d))
            cnt_item = QTableWidgetItem(str(cnt)); cnt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 0, name_item); self.table.setItem(row, 1, cnt_item)

    def current_department(self):
        row = self.table.currentRow()
        if row < 0: return None
        dept_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        return next((x for x in self.depts if x.dept_id == dept_id), None)

    def show_add_form(self):
        dlg = AddDepartmentForm(self); dlg.exec()

    def rename_selected_dept(self):
        d = self.current_department()
        if not d: return
        new, ok = QInputDialog.getText(self, "Rename Department", "New name:", text=d.name)
        if ok and new.strip(): storage.rename_department(d, new.strip()); self.refresh_departments()

    def delete_selected_dept(self):
        d = self.current_department()
        if not d: return
        if not storage.delete_department_if_empty(d):
            confirm = QMessageBox.question(
                self,
                "Delete Department",
                f"'{d.name}' still has sub departments or products. Delete everything?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return
            storage.delete_department(d)
            QMessageBox.information(self, "Deleted", "Department and all of its data deleted.")
            if self.active_department and self.active_department.dept_id == d.dept_id:
                self.active_department = None
            self.refresh_departments(); self.stack.setCurrentWidget(self.dept_page)
            return
        if self.active_department and self.active_department.dept_id == d.dept_id:
            self.active_department = None
        self.refresh_departments()

    def show_departments_page(self):
        self.active_department = None
        self.set_page_title("Departments")
        self.refresh_departments()
        self.stack.setCurrentWidget(self.dept_page)

    def show_subdepartments_page(self):
        if not self.active_department:
            self.show_departments_page()
            return
        self.set_page_title(f"{self.active_department.name} - Sub Departments")
        self.refresh_subdepartments()
        self.stack.setCurrentWidget(self.sub_page)

    def open_department_detail(self, row: int, _col: int):
        dept_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        d = next((x for x in self.depts if x.dept_id == dept_id), None)
        if not d:
            return
        self.active_department = d
        self.set_page_title(f"{d.name} - Sub Departments")
        self.refresh_subdepartments()
        self.show_subdepartments_page()

    def refresh_subdepartments(self):
        if not self.active_department:
            self.sub_table.setRowCount(0)
            return
        self.subs = storage.list_subdepartments(self.active_department)
        self.sub_table.setRowCount(0)
        for s in self.subs:
            row = self.sub_table.rowCount(); self.sub_table.insertRow(row)
            name_item = QTableWidgetItem(s.name); name_item.setData(Qt.ItemDataRole.UserRole, s.sub_id)
            cnt = storage.count_products(s)
            cnt_item = QTableWidgetItem(str(cnt)); cnt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.sub_table.setItem(row, 0, name_item); self.sub_table.setItem(row, 1, cnt_item)

    def show_add_sub_form(self):
        if not self.active_department:
            return
        dlg = AddSubDepartmentForm(self.active_department, self); dlg.exec()

    def open_sub_detail(self, row: int, _col: int):
        if not self.active_department:
            return
        sub_id = self.sub_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        s = next((x for x in self.subs if x.sub_id == sub_id), None)
        if s:
            self.detail_page.set_subdepartment(s)
            self.stack.setCurrentWidget(self.detail_page)

class SubDepartmentDetailWindow(QWidget):
    def __init__(self, parent_window: DepartmentsWindow):
        super().__init__()
        self.parent_window = parent_window
        self.subdepartment: SubDepartment | None = None
        self.products: list[Product] = []

        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        self.back_button = QPushButton("Back"); self.rate_button = QPushButton("Conversion rate")
        self.rename_sub_btn = QPushButton("Rename Sub Department"); self.delete_sub_btn = QPushButton("Delete Sub Department")
        self.export_xlsx_btn = QPushButton("Export XLSX"); self.export_pdf_btn = QPushButton("Export PDF")
        top.addWidget(self.back_button)
        top.addStretch(1)
        top.addWidget(self.rate_button)
        top.addWidget(self.rename_sub_btn)
        top.addWidget(self.delete_sub_btn)
        top.addStretch(1)
        top.addWidget(self.export_xlsx_btn)
        top.addWidget(self.export_pdf_btn)
        layout.addLayout(top)
        self.back_button.clicked.connect(self.go_back); self.rate_button.clicked.connect(self.change_conversion_rate)
        self.rename_sub_btn.clicked.connect(self.rename_subdepartment); self.delete_sub_btn.clicked.connect(self.delete_subdepartment)
        self.export_xlsx_btn.clicked.connect(lambda: export_table_to_xlsx(self.prod_table, self))
        self.export_pdf_btn.clicked.connect(lambda: export_table_to_pdf(self.prod_table, self))
        actions = QHBoxLayout()
        self.add_product_button = QPushButton("Add Product"); self.edit_product_button = QPushButton("Edit Product"); self.delete_product_button = QPushButton("Delete Product")
        actions.addWidget(self.add_product_button); actions.addStretch(1); actions.addWidget(self.edit_product_button); actions.addWidget(self.delete_product_button)
        layout.addLayout(actions)
        self.add_product_button.clicked.connect(self.show_add_product_form); self.edit_product_button.clicked.connect(self.edit_selected_product); self.delete_product_button.clicked.connect(self.delete_selected_product)
        self.prod_table = QTableWidget(0, 7)
        self.prod_table.setHorizontalHeaderLabels(["Id", "Name", "Price $", "Price C$", "Quantity", "Subtotal $", "Subtotal C$"])
        self.prod_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.prod_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.prod_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.prod_table.verticalHeader().setVisible(False)
        header = self.prod_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents); header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for i in range(2,7): header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.prod_table)
        totals = QHBoxLayout()
        self.total_items_lbl = QLabel("Items: 0"); self.total_qty_lbl = QLabel("Total quantity: 0")
        self.total_usd_lbl = QLabel("Total price $: 0.00"); self.total_c_lbl = QLabel("Total price C$: 0.00")
        self.sum_sub_usd_lbl = QLabel("Subtotal $ (sum): 0.00"); self.sum_sub_c_lbl = QLabel("Subtotal C$ (sum): 0.00")
        totals.addWidget(self.total_items_lbl); totals.addStretch(1); totals.addWidget(self.total_qty_lbl); totals.addStretch(1)
        totals.addWidget(self.total_usd_lbl); totals.addWidget(self.total_c_lbl); totals.addWidget(self.sum_sub_usd_lbl); totals.addWidget(self.sum_sub_c_lbl)
        layout.addLayout(totals)
        self.prod_table.cellDoubleClicked.connect(lambda *_: self.edit_selected_product())
    
    def set_subdepartment(self, subdepartment: SubDepartment):
        self.subdepartment = subdepartment
        self.parent_window.set_page_title(f"{subdepartment.name} - Products")
        self.refresh_products()

    def refresh_products(self):
        if not self.subdepartment:
            self.prod_table.setRowCount(0)
            self.products = []
            return
        rate = storage.get_conversion_rate(); self.products = storage.list_products(self.subdepartment)
        self.prod_table.setRowCount(0); items = len(self.products); total_qty=0; total_usd=0.0; total_c=0.0
        for p in self.products:
            row = self.prod_table.rowCount(); self.prod_table.insertRow(row)
            price_usd = float(p.price); price_c = price_usd * float(rate); qty = int(p.quantity)
            subtotal_usd = price_usd * qty; subtotal_c = price_c * qty
            total_qty += qty; total_usd += subtotal_usd; total_c += subtotal_c
            id_item = QTableWidgetItem(p.prod_id); id_item.setData(Qt.ItemDataRole.UserRole, p.prod_id)
            name_item = QTableWidgetItem(p.name)
            usd_item = QTableWidgetItem(f"{price_usd:.2f}"); usd_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            cord_item = QTableWidgetItem(f"{price_c:.2f}"); cord_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            qty_item = QTableWidgetItem(str(qty)); qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            sub_usd_item = QTableWidgetItem(f"{subtotal_usd:.2f}"); sub_usd_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            sub_c_item = QTableWidgetItem(f"{subtotal_c:.2f}"); sub_c_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.prod_table.setItem(row, 0, id_item); self.prod_table.setItem(row, 1, name_item)
            self.prod_table.setItem(row, 2, usd_item); self.prod_table.setItem(row, 3, cord_item)
            self.prod_table.setItem(row, 4, qty_item); self.prod_table.setItem(row, 5, sub_usd_item); self.prod_table.setItem(row, 6, sub_c_item)
        self.total_items_lbl.setText(f"Items: {items}"); self.total_qty_lbl.setText(f"Total quantity: {total_qty}")
        self.total_usd_lbl.setText(f"Total price $: {total_usd:.2f}"); self.total_c_lbl.setText(f"Total price C$: {total_c:.2f}")
        self.sum_sub_usd_lbl.setText(f"Subtotal $ (sum): {total_usd:.2f}"); self.sum_sub_c_lbl.setText(f"Subtotal C$ (sum): {total_c:.2f}")

    def current_product(self):
        row = self.prod_table.currentRow()
        if row < 0: return None
        prod_id = self.prod_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        return next((p for p in self.products if p.prod_id == prod_id), None)

    def go_back(self):
        self.subdepartment = None
        self.products = []
        self.parent_window.show_subdepartments_page()

    def rename_subdepartment(self):
        dlg = EditSubDepartmentNameDialog(self.subdepartment, self)
        if dlg.exec():
            new_name = dlg.new_name()
            if new_name:
                storage.rename_subdepartment(self.subdepartment, new_name)
                self.subdepartment.name = new_name
                self.parent_window.set_page_title(f"{self.subdepartment.name} - Products")
                self.parent_window.refresh_subdepartments()

    def delete_subdepartment(self):
        if not self.subdepartment:
            return
        prod_count = storage.count_products(self.subdepartment)
        if prod_count > 0:
            question = QMessageBox.question(
                self,
                "Delete Sub Department",
                f"'{self.subdepartment.name}' has {prod_count} product(s). Delete everything?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if question != QMessageBox.StandardButton.Yes:
                return
            storage.delete_subdepartment(self.subdepartment)
            QMessageBox.information(self, "Deleted", "Sub department and its products deleted.")
            self.parent_window.refresh_subdepartments(); self.parent_window.refresh_departments()
            self.go_back()
            return
        confirm = QMessageBox.question(
            self,
            "Delete Sub Department",
            f"Delete '{self.subdepartment.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        storage.delete_subdepartment(self.subdepartment)
        QMessageBox.information(self, "Deleted", "Sub department deleted.")
        self.parent_window.refresh_subdepartments(); self.parent_window.refresh_departments()
        self.go_back()

    def change_conversion_rate(self):
        from PyQt6.QtWidgets import QInputDialog
        current = storage.get_conversion_rate()
        value, ok = QInputDialog.getDouble(self, "Conversion Rate", "1 USD = ? C$:", float(current), 0.0001, 1_000_000.0, 4)
        if ok:
            storage.set_conversion_rate(float(value))
            self.refresh_products()

    def show_add_product_form(self):
        if not self.subdepartment:
            return
        form = AddProductForm(self); form.exec()

    def add_product(self, product: Product):
        storage.add_product(product); self.refresh_products(); self.parent_window.refresh_subdepartments()

    def edit_selected_product(self):
        prod = self.current_product()
        if not prod: return
        dlg = EditProductDialog(prod, self)
        if dlg.exec():
            name, desc, price, qty = dlg.edited_values()
            if not name or not desc or not price or not qty: return
            try:
                prod.name = name; prod.description = desc; prod.price = float(price); prod.quantity = int(qty)
            except ValueError:
                QMessageBox.warning(self, "Invalid", "Price must be a number and Quantity must be an integer."); return
            storage.update_product(prod); self.refresh_products()

    def delete_selected_product(self):
        prod = self.current_product()
        if not prod: return
        confirm = QMessageBox.question(self, "Delete Product", f"Delete product '{prod.name}'?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            storage.delete_product(prod); self.refresh_products(); self.parent_window.refresh_subdepartments()
