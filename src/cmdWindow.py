# coding=utf-8
""" docstring: 控制台窗口 """

from PyQt5.QtWidgets import QMainWindow

from cmdPage import Ui_MainWindow


class cmdWindow(QMainWindow, Ui_MainWindow):
    """ docstring: 控制台类 """
    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = cmdWindow()
    window.show()
    sys.exit(app.exec_())
