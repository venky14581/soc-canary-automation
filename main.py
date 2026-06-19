import sys
from PySide6.QtWidgets import QApplication
from app.gui import SOCDeployerWindow

def main():
    app = QApplication(sys.argv)
    window = SOCDeployerWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()