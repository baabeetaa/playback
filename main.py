import sys

from PyQt6.QtWidgets import QApplication

import ui_mainwindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = ui_mainwindow.MainWindow()
    win.show()
    app.exec()

