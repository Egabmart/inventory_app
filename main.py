import os
import sys
from PyQt6.QtWidgets import QApplication

if __package__ in (None, ""):
    package_root = os.path.dirname(os.path.abspath(__file__))
    if package_root not in sys.path:
        sys.path.insert(0, package_root)
    from windows.home import HomeWindow
    import storage
else:
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
