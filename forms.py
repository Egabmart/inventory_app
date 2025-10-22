import base64
from html import escape
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QPushButton, QHBoxLayout, QPlainTextEdit,
    QFileDialog, QFrame, QLabel, QVBoxLayout, QScrollArea, QWidget, QComboBox, QMessageBox,
    QDateEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QMarginsF
from PyQt6.QtGui import QPixmap, QIntValidator, QTextDocument, QPageLayout
from PyQt6.QtPrintSupport import QPrinter
from sqlite3 import IntegrityError
from .models import Department, Product, SubDepartment, Local
from . import storage
from pathlib import Path

class ImageDropArea(QFrame):
    def __init__(self, on_files_added, parent=None):
        super().__init__(parent)
        self.on_files_added = on_files_added
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("QFrame { border: 2px dashed #999; border-radius: 6px; }")
        self.setAcceptDrops(True)
        self.setMinimumHeight(180)
        lay = QVBoxLayout(self)
        self.label = QLabel("Drop images here (or use Browse…)")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.label)
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls(): e.acceptProposedAction()
        else: e.ignore()
    def dropEvent(self, e):
        paths = [u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]
        if paths:
            self.on_files_added(paths)
            self.label.setText(f"{len(paths)} file(s) added (drop more or use Browse…)")

class ClickableThumbLabel(QLabel):
    doubleClicked = pyqtSignal(str)
    def __init__(self, abs_path: str, parent=None):
        super().__init__(parent); self.abs_path = abs_path
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit(self.abs_path); super().mouseDoubleClickEvent(event)

class ImageViewerDialog(QDialog):
    def __init__(self, abs_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(Path(abs_path).name); self.setMinimumSize(900,700); self.setSizeGripEnabled(True)
        scroll = QScrollArea(self); scroll.setWidgetResizable(True)
        container = QWidget(); lay = QVBoxLayout(container); lay.setContentsMargins(10,10,10,10)
        self.img_label = QLabel(); self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(self.img_label)
        scroll.setWidget(container); outer = QVBoxLayout(self); outer.addWidget(scroll)
        pix = QPixmap(abs_path); 
        if not pix.isNull(): self.img_label.setPixmap(pix)

class ThumbCard(QWidget):
    def __init__(self, image_id: str, abs_path: str, on_delete, on_open, parent=None):
        super().__init__(parent)
        v = QVBoxLayout(self); v.setContentsMargins(0,0,0,0); v.setSpacing(6)
        pix = QPixmap(abs_path)
        thumb = pix.scaled(240,240, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        lbl = ClickableThumbLabel(abs_path); lbl.setPixmap(thumb); lbl.setFixedSize(250,250)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("QLabel { background: #fafafa; border: 1px solid #ddd; border-radius: 8px; }")
        lbl.doubleClicked.connect(on_open); v.addWidget(lbl)
        del_btn = QPushButton("Delete"); del_btn.clicked.connect(lambda: on_delete(image_id)); v.addWidget(del_btn)

class AddDepartmentForm(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("Add Department"); self.setFixedSize(320,160); self.parent = parent
        form = QFormLayout(self)
        self.input_name = QLineEdit(); self.input_abbrev = QLineEdit()
        form.addRow("Name:", self.input_name); form.addRow("Abbreviation:", self.input_abbrev)
        self.create_btn = QPushButton("Create"); self.create_btn.clicked.connect(self.create_department); form.addRow(self.create_btn)
    def create_department(self):
        name = self.input_name.text().strip(); ab = self.input_abbrev.text().strip()
        if not name or not ab: return
        try:
            storage.add_department(ab, name)
        except IntegrityError:
            QMessageBox.warning(self, "Duplicate", "A department with this abbreviation already exists.")
            return
        self.parent.refresh_departments(); self.close()

class AddSubDepartmentForm(QDialog):
    def __init__(self, department, parent=None):
        super().__init__(parent); self.setWindowTitle("Add Sub Department"); self.setFixedSize(320,160)
        self.department = department; self.parent = parent
        form = QFormLayout(self); self.input_name = QLineEdit(); self.input_abbrev = QLineEdit()
        form.addRow("Name:", self.input_name); form.addRow("Abbreviation:", self.input_abbrev)
        self.create_btn = QPushButton("Create"); self.create_btn.clicked.connect(self.create_subdepartment); form.addRow(self.create_btn)
    def create_subdepartment(self):
        name = self.input_name.text().strip(); ab = self.input_abbrev.text().strip()
        if not name or not ab: return
        dept = self.department if isinstance(self.department, Department) else None
        if not dept or getattr(dept, "dept_id", None) is None:
            QMessageBox.warning(self, "Missing department", "The selected department could not be found. Please refresh and try again.")
            return
        try:
            storage.add_subdepartment(dept, ab, name)
        except IntegrityError:
            QMessageBox.warning(self, "Duplicate", "A sub department with this abbreviation already exists for this department.")
            return
        self.parent.refresh_subdepartments();
        try:
            self.parent.refresh_departments()
        except AttributeError:
            pass
        self.close()

class AddProductForm(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("Add Product"); self.setMinimumSize(420,460); self.setSizeGripEnabled(True)
        self.parent = parent; self._image_paths = []
        form = QFormLayout(self)
        self.input_name = QLineEdit(); self.input_name.setMinimumWidth(255)
        self.input_desc = QPlainTextEdit(); self.input_desc.setMinimumHeight(120); self.input_desc.setTabChangesFocus(True)
        self.input_price = QLineEdit(); self.input_qty = QLineEdit()
        form.addRow("Name:", self.input_name); form.addRow("Description:", self.input_desc)
        form.addRow("Price:", self.input_price); form.addRow("Quantity:", self.input_qty)
        drop_row = QVBoxLayout(); self.drop = ImageDropArea(self._add_images); drop_row.addWidget(self.drop)
        browse_btn = QPushButton("Browse images…"); browse_btn.clicked.connect(self._browse_images); drop_row.addWidget(browse_btn)
        container = QWidget(); container.setLayout(drop_row); form.addRow("Pictures:", container)
        self.create_btn = QPushButton("Create Product"); self.create_btn.clicked.connect(self.create_product); form.addRow(self.create_btn)
    def _add_images(self, paths): self._image_paths.extend(paths); self.drop.label.setText(f"{len(self._image_paths)} image(s) queued")
    def _browse_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select images", "", "Images (*.png *.jpg *.jpeg *.webp *.bmp *.gif)")
        if files: self._add_images(files)
    def create_product(self):
        name = self.input_name.text().strip(); desc = self.input_desc.toPlainText().strip()
        price = self.input_price.text().strip(); qty = self.input_qty.text().strip()
        if not name or not desc or not price or not qty: return
        sub = getattr(self.parent, "subdepartment", None)
        if not isinstance(sub, SubDepartment) or getattr(sub, "sub_id", None) is None:
            QMessageBox.warning(self, "Missing sub department", "Please select a sub department before adding a product.")
            return
        try:
            prod_id = storage.generate_next_product_id(sub)
        except ValueError:
            QMessageBox.warning(self, "Missing sub department", "The selected sub department could not be found in storage.")
            return
        try:
            price_val = float(price); qty_val = int(qty)
        except ValueError:
            QMessageBox.warning(self, "Invalid values", "Price must be a number and Quantity must be a whole number.")
            return
        product = Product(prod_id, sub, name, desc, price_val, qty_val)
        self.parent.subdepartment = sub
        try:
            self.parent.add_product(product)
        except IntegrityError:
            QMessageBox.warning(self, "Duplicate", "A product with the generated ID already exists. Please try again.")
            return
        try: storage.add_product_images(product, self._image_paths)
        except Exception: pass
        self.close()

class EditSubDepartmentNameDialog(QDialog):
    def __init__(self, subdepartment: SubDepartment, parent=None):
        super().__init__(parent); self.subdepartment = subdepartment; self._name = subdepartment.name
        self.setWindowTitle("Rename Sub Department"); self.setFixedSize(360, 150)
        form = QFormLayout(self); self.input_name = QLineEdit(subdepartment.name)
        form.addRow("Name:", self.input_name)
        btn_row = QHBoxLayout(); self.save_btn = QPushButton("Save"); self.cancel_btn = QPushButton("Cancel")
        btn_row.addStretch(1); btn_row.addWidget(self.save_btn); btn_row.addWidget(self.cancel_btn); form.addRow(btn_row)
        self.save_btn.clicked.connect(self._save); self.cancel_btn.clicked.connect(self.reject)

    def _save(self):
        name = self.input_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid name", "Please enter a name."); return
        self._name = name; self.accept()

    def new_name(self) -> str:
        return self._name

class LocalPickerDialog(QDialog):
    def __init__(self, product: Product, parent=None):
        super().__init__(parent); self.setWindowTitle("Add to Local"); self.setFixedSize(360,180); self.product = product
        self.total_qty = storage.get_product_total_quantity(self.product)
        self.allocated = storage.get_allocated_qty_for_product(self.product)
        self.available = max(0, self.total_qty - self.allocated)
        layout = QFormLayout(self); self.combo = QComboBox()
        self.locals = storage.list_locals()
        if not self.locals: self.combo.addItem("No Locals yet"); self.combo.setEnabled(False)
        else:
            for loc in self.locals: self.combo.addItem(loc.name, loc.local_id)
        layout.addRow("Choose Local:", self.combo)
        qty_row = QHBoxLayout(); self.input_qty = QLineEdit(); self.input_qty.setPlaceholderText("Qty"); self.input_qty.setFixedWidth(80)
        self.input_qty.setValidator(QIntValidator(1, 1_000_000, self)); self.left_lbl = QLabel(f"Left in inventory: {self.available}")
        qty_row.addWidget(self.input_qty); qty_row.addSpacing(8); qty_row.addWidget(self.left_lbl); qty_row.addStretch(1)
        qty_wrap = QWidget(); qty_wrap.setLayout(qty_row); layout.addRow("Amount:", qty_wrap)
        row = QHBoxLayout(); self.add_btn = QPushButton("Add"); self.cancel_btn = QPushButton("Cancel")
        row.addStretch(1); row.addWidget(self.add_btn); row.addWidget(self.cancel_btn); layout.addRow(row)
        self.add_btn.clicked.connect(self.do_add); self.cancel_btn.clicked.connect(self.reject)
        if not self.locals or self.available <= 0: self.add_btn.setEnabled(False)
    def do_add(self):
        if not self.locals: return
        text = self.input_qty.text().strip()
        if not text: QMessageBox.warning(self, "Missing amount", "Please enter the quantity to add."); return
        try: qty = int(text)
        except: QMessageBox.warning(self, "Invalid amount", "Quantity must be a whole number."); return
        if qty <= 0: QMessageBox.warning(self, "Invalid amount", "Quantity must be at least 1."); return
        if qty > self.available: QMessageBox.warning(self, "Too many", f"Only {self.available} left in inventory."); return
        idx = self.combo.currentIndex(); local = self.locals[idx]; storage.add_product_to_local(local, self.product, qty); self.accept()

class RegisterSaleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("Register Sale"); self.setFixedSize(420,260)
        form = QFormLayout(self); self.input_code = QLineEdit(); self.input_code.setPlaceholderText("e.g., COVE1")
        self.input_qty = QLineEdit(); self.input_qty.setValidator(QIntValidator(1, 1_000_000, self)); self.loc_combo = QComboBox()
        self.loc_combo.addItem("Online", {"type":"online", "id": None})
        for loc in storage.list_locals(): self.loc_combo.addItem(loc.name, {"type":"local", "id": loc.local_id})
        self.input_client = QLineEdit(); self.input_client.setPlaceholderText("Optional")
        self.date_edit = QDateEdit(); self.date_edit.setCalendarPopup(True); self.date_edit.setDisplayFormat("yyyy-MM-dd"); self.date_edit.setDate(QDate.currentDate())
        form.addRow("Product ID:", self.input_code); form.addRow("Quantity:", self.input_qty); form.addRow("Location:", self.loc_combo)
        form.addRow("Client:", self.input_client); form.addRow("Sale date:", self.date_edit)
        row = QHBoxLayout(); self.ok_btn = QPushButton("Register"); self.cancel_btn = QPushButton("Cancel")
        row.addStretch(1); row.addWidget(self.ok_btn); row.addWidget(self.cancel_btn); form.addRow(row)
        self.ok_btn.clicked.connect(self.register); self.cancel_btn.clicked.connect(self.reject)
    def register(self):
        code = self.input_code.text().strip(); qty_txt = self.input_qty.text().strip()
        if not code or not qty_txt: return
        try: qty = int(qty_txt)
        except: return
        prod = storage.get_product_by_id(code)
        if not prod: QMessageBox.information(self, "Not found", "Product isn't listed"); return
        data = self.loc_combo.currentData(); loc = None
        if data["type"] == "local":
            for l in storage.list_locals():
                if l.local_id == data["id"]: loc = l; break
        client = self.input_client.text().strip()
        sale_date = self.date_edit.date().toString("yyyy-MM-dd")
        ok = storage.register_sale(prod, qty, data["type"], loc, client if client else None, sale_date)
        if not ok:
            QMessageBox.warning(self, "Not enough quantity", "Requested quantity is not available (or not allocated in the chosen local).")
            return
        QMessageBox.information(self, "Sale registered", "Sale recorded successfully."); self.accept()


class CreateInvoiceDialog(QDialog):
    _LOGO_SVG = """
    <svg xmlns='http://www.w3.org/2000/svg' width='180' height='70' viewBox='0 0 180 70'>
        <defs>
            <linearGradient id='g' x1='0%' y1='0%' x2='100%' y2='0%'>
                <stop offset='0%' stop-color='#7bc4b2'/>
                <stop offset='100%' stop-color='#1c6b66'/>
            </linearGradient>
        </defs>
        <rect x='0' y='10' width='180' height='50' rx='25' fill='url(#g)'/>
        <text x='90' y='45' font-family="Segoe UI, Arial, sans-serif" font-size='28' text-anchor='middle' fill='#f5fbfa'>Ciao</text>
        <text x='132' y='45' font-family="Segoe UI, Arial, sans-serif" font-size='16' text-anchor='start' fill='#f5fbfa'>a Mano</text>
    </svg>
    """.strip()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Invoice")
        self.setMinimumWidth(540)
        self.setSizeGripEnabled(True)

        self._logo_cache: str | None = None
        self.product_rows: list[dict[str, QWidget]] = []

        outer = QVBoxLayout(self)
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        self.products_container = QWidget()
        self.products_layout = QVBoxLayout(self.products_container)
        self.products_layout.setContentsMargins(0, 0, 0, 0)
        self.products_layout.setSpacing(8)

        form.addRow("Products:", self.products_container)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate())
        form.addRow("Date:", self.date_edit)

        self.client_name_edit = QLineEdit()
        self.client_name_edit.setPlaceholderText("Client name")
        form.addRow("Client name:", self.client_name_edit)

        self.client_address_edit = QPlainTextEdit()
        self.client_address_edit.setPlaceholderText("Client address")
        self.client_address_edit.setFixedHeight(70)
        self.client_address_edit.setTabChangesFocus(True)
        form.addRow("Client address:", self.client_address_edit)

        outer.addLayout(form)

        self._add_product_row()

        outer.addStretch(1)
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self.generate_btn = QPushButton("Generate PDF")
        self.generate_btn.setDefault(True)
        btn_row.addWidget(self.generate_btn)
        outer.addLayout(btn_row)

        self.generate_btn.clicked.connect(self._generate_pdf)

    def _logo_data_uri(self) -> str:
        if not self._logo_cache:
            encoded = base64.b64encode(self._LOGO_SVG.encode("utf-8")).decode("ascii")
            self._logo_cache = f"data:image/svg+xml;base64,{encoded}"
        return self._logo_cache

    def _add_product_row(self) -> None:
        row_widget = QWidget()
        layout = QHBoxLayout(row_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        code_edit = QLineEdit()
        code_edit.setPlaceholderText("Product ID")
        code_edit.setMinimumWidth(140)

        qty_edit = QLineEdit()
        qty_edit.setPlaceholderText("Qty")
        qty_edit.setValidator(QIntValidator(1, 1_000_000, self))
        qty_edit.setFixedWidth(80)

        add_btn = QPushButton("+")
        add_btn.setFixedWidth(32)
        add_btn.clicked.connect(self._add_product_row)

        remove_btn = QPushButton("-")
        remove_btn.setFixedWidth(32)
        remove_btn.clicked.connect(lambda: self._remove_product_row(row_widget))

        layout.addWidget(code_edit, 1)
        layout.addWidget(qty_edit)
        layout.addWidget(add_btn)
        layout.addWidget(remove_btn)

        self.products_layout.addWidget(row_widget)
        self.product_rows.append(
            {
                "container": row_widget,
                "code": code_edit,
                "qty": qty_edit,
                "remove_btn": remove_btn,
            }
        )
        self._update_remove_buttons()
        code_edit.setFocus()

    def _remove_product_row(self, row_widget: QWidget) -> None:
        for idx, row in enumerate(self.product_rows):
            if row["container"] is row_widget:
                self.product_rows.pop(idx)
                break
        self.products_layout.removeWidget(row_widget)
        row_widget.deleteLater()
        if not self.product_rows:
            self._add_product_row()
            return
        self._update_remove_buttons()

    def _update_remove_buttons(self) -> None:
        show_remove = len(self.product_rows) > 1
        for row in self.product_rows:
            row["remove_btn"].setVisible(show_remove)

    def _format_currency(self, value: float) -> str:
        return f"C${value:,.2f}"

    def _generate_pdf(self) -> None:
        items: list[tuple[Product, int]] = []
        for row in self.product_rows:
            code = row["code"].text().strip()
            qty_text = row["qty"].text().strip()
            if not code or not qty_text:
                QMessageBox.warning(self, "Missing information", "Please fill in the product ID and quantity for each item.")
                return
            try:
                qty = int(qty_text)
            except ValueError:
                QMessageBox.warning(self, "Invalid quantity", "Quantity must be a whole number.")
                row["qty"].setFocus()
                return
            if qty <= 0:
                QMessageBox.warning(self, "Invalid quantity", "Quantity must be at least 1.")
                row["qty"].setFocus()
                return
            product = storage.get_product_by_id(code)
            if not product:
                QMessageBox.warning(self, "Product not found", f"Product with ID '{code}' was not found.")
                row["code"].setFocus()
                return
            items.append((product, qty))

        if not items:
            QMessageBox.warning(self, "No products", "Please add at least one product to create an invoice.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Save Invoice PDF", "", "PDF Files (*.pdf)")
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"

        invoice_date = self.date_edit.date().toString("yyyy-MM-dd")
        client_name = self.client_name_edit.text().strip()
        client_address = self.client_address_edit.toPlainText().strip()

        html = self._build_invoice_html(items, invoice_date, client_name, client_address)

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(path)
        printer.setPageMargins(QMarginsF(12, 12, 12, 12), QPageLayout.Unit.Millimeter)

        document = QTextDocument()
        document.setDocumentMargin(12)
        document.setHtml(html)

        try:
            document.print(printer)
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", f"Could not create PDF:\n{exc}")
            return

        QMessageBox.information(self, "Invoice created", f"Invoice saved to:\n{path}")
        self.accept()

    def _build_invoice_html(
        self,
        items: list[tuple[Product, int]],
        invoice_date: str,
        client_name: str,
        client_address: str,
    ) -> str:
        rate = float(storage.get_conversion_rate())

        rows: list[str] = []
        total = 0.0
        for product, qty in items:
            unit_c = float(product.price) * rate
            line_total = unit_c * qty
            total += line_total

            description_parts: list[str] = []
            if product.description:
                description_parts = [escape(part) for part in product.description.splitlines() if part.strip()]
            desc_html = f"<div class='prod-name'>{escape(product.name)}</div>"
            if description_parts:
                desc_html += "<div class='prod-desc'>" + "<br>".join(description_parts) + "</div>"

            rows.append(
                "<tr>"
                f"<td class='qty'>{qty}</td>"
                f"<td class='desc'>{desc_html}</td>"
                f"<td class='unit'>{self._format_currency(unit_c)}</td>"
                f"<td class='total'>{self._format_currency(line_total)}</td>"
                "</tr>"
            )

        if client_name:
            client_name_html = escape(client_name)
        else:
            client_name_html = "<span class='placeholder'>Cliente no especificado</span>"

        if client_address:
            address_html = "<br>".join(
                escape(line.strip()) for line in client_address.splitlines() if line.strip()
            )
        else:
            address_html = "<span class='placeholder'>Sin dirección proporcionada</span>"

        rows_html = "\n".join(rows)

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset='utf-8'>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; background: #f4f7f6; }}
        .invoice {{ background: #ffffff; margin: 0 auto; padding: 36px; width: 100%; box-sizing: border-box; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 4px solid #7bc4b2; padding-bottom: 18px; }}
        .title {{ font-size: 28px; letter-spacing: 2px; color: #1c6b66; font-weight: 700; }}
        .logo img {{ height: 70px; }}
        .meta {{ display: flex; justify-content: space-between; margin-top: 24px; gap: 48px; }}
        .meta .section-title {{ font-weight: 600; text-transform: uppercase; color: #1c6b66; margin-top: 12px; font-size: 12px; letter-spacing: 0.8px; }}
        .meta .value {{ font-size: 13px; color: #2f3a3a; margin-top: 6px; }}
        .meta .address {{ white-space: pre-line; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 28px; }}
        th {{ text-transform: uppercase; font-size: 11px; letter-spacing: 1px; text-align: left; padding: 10px; background: #e8f5f2; color: #1c6b66; }}
        td {{ padding: 12px 10px; border-bottom: 1px solid #d8e6e1; font-size: 13px; vertical-align: top; }}
        td.qty {{ width: 70px; text-align: center; font-weight: 600; color: #1c3d3b; }}
        td.unit, td.total {{ width: 120px; text-align: right; font-weight: 600; color: #1c6b66; }}
        .prod-name {{ font-weight: 600; color: #1c3d3b; margin-bottom: 4px; }}
        .prod-desc {{ color: #4c5b59; font-size: 12px; line-height: 1.5; }}
        tfoot td {{ font-size: 14px; font-weight: 700; padding-top: 16px; border-bottom: none; }}
        tfoot td.label {{ text-align: right; text-transform: uppercase; color: #1c6b66; }}
        .footer-bar {{ margin-top: 32px; height: 6px; background: linear-gradient(90deg, #7bc4b2, #1c6b66); border-radius: 6px; }}
        .placeholder {{ color: #92a5a1; font-style: italic; }}
    </style>
</head>
<body>
    <div class='invoice'>
        <div class='header'>
            <div class='title'>PROFORMA</div>
            <div class='logo'><img src='{self._logo_data_uri()}' alt='Ciao a Mano logo'></div>
        </div>
        <div class='meta'>
            <div class='left'>
                <div class='section-title'>Fecha</div>
                <div class='value'>{escape(invoice_date)}</div>
                <div class='section-title'>Enviado a</div>
                <div class='value'>{client_name_html}</div>
                <div class='value address'>{address_html}</div>
            </div>
            <div class='right'>
                <div class='section-title'>Enviado por</div>
                <div class='value'>Ciao a Mano</div>
                <div class='value'>Km 10.5 Carretera Sur</div>
                <div class='value'>Del Colegio Aleman</div>
                <div class='value'>750 MTS Oeste</div>
                <div class='value'>ciaoamano@gmail.com</div>
            </div>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Cantidad</th>
                    <th>Descripción</th>
                    <th>P. Unitario</th>
                    <th>Total Línea</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
            <tfoot>
                <tr>
                    <td colspan='3' class='label'>Total</td>
                    <td class='total'>{self._format_currency(total)}</td>
                </tr>
            </tfoot>
        </table>
        <div class='footer-bar'></div>
    </div>
</body>
</html>
""".strip()

class EditProductDialog(QDialog):
    def __init__(self, product: Product, parent=None, readonly: bool = False):
        super().__init__(parent); self.setWindowTitle("Edit Product"); self.setMinimumSize(640,720); self.setSizeGripEnabled(True)
        self.product = product; self.readonly = readonly
        form = QFormLayout(self)
        self.input_name = QLineEdit(); self.input_name.setMinimumWidth(255)
        self.input_desc = QPlainTextEdit(); self.input_desc.setMinimumHeight(140); self.input_desc.setTabChangesFocus(True)
        self.input_price = QLineEdit(); self.input_qty = QLineEdit()
        self.input_name.setText(product.name); self.input_desc.setPlainText(product.description)
        self.input_price.setText(str(product.price)); self.input_qty.setText(str(product.quantity))
        form.addRow("Name:", self.input_name); form.addRow("Description:", self.input_desc)
        form.addRow("Price:", self.input_price); form.addRow("Quantity:", self.input_qty)
        if self.readonly:
            self.input_name.setReadOnly(True); self.input_desc.setReadOnly(True)
            self.input_price.setReadOnly(True); self.input_qty.setReadOnly(True)
        pics_row = QWidget(); pics_layout = QHBoxLayout(pics_row); pics_layout.setContentsMargins(0,0,0,0); pics_layout.setSpacing(12)
        self.gallery_scroll = QScrollArea(); self.gallery_scroll.setWidgetResizable(True); self.gallery_scroll.setMinimumHeight(360)
        self.gallery_container = QWidget(); self.gallery_layout = QHBoxLayout(self.gallery_container)
        self.gallery_layout.setContentsMargins(6,6,6,6); self.gallery_layout.setSpacing(12)
        self.gallery_scroll.setWidget(self.gallery_container); pics_layout.addWidget(self.gallery_scroll, 1)
        if not self.readonly:
            self.side_panel = QWidget(); side_layout = QVBoxLayout(self.side_panel); side_layout.setContentsMargins(0,0,0,0); side_layout.setSpacing(8)
            self.drop_more = ImageDropArea(self._add_more_images); self.drop_more.setMinimumWidth(260); self.drop_more.setMinimumHeight(220)
            self.browse_more_btn = QPushButton("Browse images…"); self.browse_more_btn.clicked.connect(self._browse_more_images)
            side_layout.addWidget(self.drop_more); side_layout.addWidget(self.browse_more_btn); side_layout.addStretch(1)
            self.side_panel.setFixedWidth(280); pics_layout.addWidget(self.side_panel, 0)
        form.addRow("Pictures:", pics_row)
        btns = QHBoxLayout(); self.save_btn = QPushButton("Save"); self.add_to_local_btn = QPushButton("Add to Local"); self.cancel_btn = QPushButton("Cancel")
        btns.addStretch(1); btns.addWidget(self.save_btn); btns.addWidget(self.add_to_local_btn); btns.addWidget(self.cancel_btn); form.addRow(btns)
        self.save_btn.clicked.connect(self.accept); self.cancel_btn.clicked.connect(self.reject); self.add_to_local_btn.clicked.connect(self._open_add_to_local)
        if self.readonly: self.save_btn.setVisible(False); self.add_to_local_btn.setVisible(False); self.cancel_btn.setText("Close")
        self._load_gallery()

    def _load_gallery(self):
        while self.gallery_layout.count():
            item = self.gallery_layout.takeAt(0); w = item.widget()
            if w: w.deleteLater()
        imgs = storage.list_product_images(self.product)
        if not imgs:
            lbl = QLabel("No pictures for this product."); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter); self.gallery_layout.addWidget(lbl); return
        for rec in imgs:
            abs_path = str(storage.get_image_abspath(rec["rel_path"]))
            if self.readonly:
                pix = QPixmap(abs_path)
                if pix.isNull(): continue
                thumb = pix.scaled(240,240, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                img_lbl = ClickableThumbLabel(abs_path); img_lbl.setPixmap(thumb); img_lbl.setFixedSize(250,250)
                img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                img_lbl.setStyleSheet("QLabel { background: #fafafa; border: 1px solid #ddd; border-radius: 8px; }")
                img_lbl.doubleClicked.connect(self._open_big_viewer); self.gallery_layout.addWidget(img_lbl)
            else:
                from .forms import ThumbCard as _TC  # avoid circular name clash during type checking
                card = _TC(rec["image_id"], abs_path, self._delete_image, self._open_big_viewer); self.gallery_layout.addWidget(card)

    def _open_big_viewer(self, abs_path: str):
        dlg = ImageViewerDialog(abs_path, self); dlg.exec()

    def _delete_image(self, image_id: str):
        storage.delete_product_image(image_id); self._load_gallery()

    def _add_more_images(self, paths: list[str]):
        storage.add_product_images(self.product, paths); self.drop_more.label.setText(f"Added {len(paths)} image(s)."); self._load_gallery()

    def _browse_more_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select images", "", "Images (*.png *.jpg *.jpeg *.webp *.bmp *.gif)")
        if files: self._add_more_images(files)

    def _open_add_to_local(self):
        dlg = LocalPickerDialog(self.product, self); dlg.exec()

    def edited_values(self):
        return (self.input_name.text().strip(), self.input_desc.toPlainText().strip(), self.input_price.text().strip(), self.input_qty.text().strip())
