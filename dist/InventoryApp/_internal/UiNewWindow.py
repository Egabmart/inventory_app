import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QButtonGroup, QSizePolicy
)

# ---- Small helper: navigation button for sidebar
class NavButton(QPushButton):
    def __init__(self, text, *, checkable=True, height=40, parent=None):
        super().__init__(text, parent)
        self.setCheckable(checkable)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet("""
            QPushButton {
                color: #e9f2ef;
                background: transparent;
                border: none;
                text-align: left;
                padding: 10px 12px;
                border-radius: 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.08);
            }
            QPushButton:checked {
                background: #67b7aa;
                color: #ffffff;
            }
        """)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inventory App")
        self.resize(1100, 700)

        # ---- Central grid
        central = QWidget()
        grid = QGridLayout(central)
        grid.setContentsMargins(16, 16, 16, 16)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        self.setCentralWidget(central)

        # ---- Top bar (row 0, span 2 columns)
        topbar = QWidget()
        topbar.setObjectName("TopBar")
        topbar.setFixedHeight(48)

        topbar_layout = QHBoxLayout(topbar)
        topbar_layout.setContentsMargins(16, 8, 16, 8)
        topbar_layout.setSpacing(12)

        # 👇 Left: Title label
        title_label = QLabel("Inventory App")
        title_label.setStyleSheet("""
            background: transparent;
            color: white;
            font-weight: 600;
            font-size: 18px;    
        """)
        topbar_layout.addWidget(title_label)
        topbar_layout.addStretch()

        grid.addWidget(topbar, 0, 0, 1, 2)

        # ---- Sidebar (row 1, col 0)
        sidebar = QWidget()
        sidebar.setObjectName("SideBar")
        sidebar.setFixedWidth(200)
        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(12, 12, 12, 12)
        sb.setSpacing(8)

        # Sidebar buttons
        self.btn_dept   = NavButton("Departments")
        self.btn_locals = NavButton("Locals")
        self.btn_sales  = NavButton("Sales")
        self.btn_search = NavButton("Search")

        sb.addWidget(self.btn_dept)
        sb.addWidget(self.btn_locals)
        sb.addWidget(self.btn_sales)
        sb.addWidget(self.btn_search)
        sb.addStretch()

        self.btn_settings = NavButton("Settings", checkable=False)
        sb.addWidget(self.btn_settings)
        grid.addWidget(sidebar, 1, 0)

        # ---- Content (row 1, col 1)
        self.stack = QStackedWidget()
        self.stack.setObjectName("Content")

        self.page_dept   = self._make_page("Department Tab")
        self.page_locals = self._make_page("Locals Tab")
        self.page_sales  = self._make_page("Sales Tab")
        self.page_search = self._make_page("Search Tab")
        self.page_settings = self._make_page("Settings")

        self.stack.addWidget(self.page_dept)
        self.stack.addWidget(self.page_locals)
        self.stack.addWidget(self.page_sales)
        self.stack.addWidget(self.page_search)
        self.stack.addWidget(self.page_settings)

        grid.addWidget(self.stack, 1, 1)

        # ---- Grid stretch behavior
        grid.setRowStretch(0, 0)
        grid.setRowStretch(1, 1)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)

        # ---- Sidebar group logic
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        for i, b in enumerate([self.btn_dept, self.btn_locals, self.btn_sales, self.btn_search]):
            self.group.addButton(b, i)
        self.btn_dept.setChecked(True)
        self.stack.setCurrentIndex(0)

        self.group.idClicked.connect(self._switch_page)
        self.btn_settings.clicked.connect(lambda: self._show_settings())

        # ---- Styles
        self.setStyleSheet("""
            QWidget { background: #ffffff; }

            #TopBar {
                background: #4ca797;
                border-radius: 8px;
            }

            #SideBar {
                background: #2f7f75;
                color: #e9f2ef;
                border-radius: 8px;
            }

            #Content {
                background: #ffffff;
            }
        """)

    def _make_page(self, text: str):
        page = QWidget()
        layout = QVBoxLayout(page)
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 28px; font-weight: 700; color: #222;")
        layout.addWidget(lbl)
        return page

    def _switch_page(self, btn_id: int):
        self.stack.setCurrentIndex(btn_id)

    def _show_settings(self):
        for b in [self.btn_dept, self.btn_locals, self.btn_sales, self.btn_search]:
            b.setChecked(False)
        self.stack.setCurrentIndex(4)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
