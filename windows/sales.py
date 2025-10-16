from PyQt6.QtWidgets import QHBoxLayout, QPushButton

from .base import BaseWindow
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

        self.register_button.clicked.connect(self.open_register_sales_dialog)

    def open_register_sales_dialog(self) -> None:
        dialog = RegisterSaleDialog(self)
        dialog.exec()