import sys
from PyQt6.QtWidgets import QApplication
from .windows.home import HomeWindow
from . import storage

def main():
    storage.init_db()
    app = QApplication(sys.argv)
    win = HomeWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
