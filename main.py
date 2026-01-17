import sys
from gui.main_window import MainWindow, DinoApp

def main():
    app = DinoApp(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
