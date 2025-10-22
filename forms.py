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
