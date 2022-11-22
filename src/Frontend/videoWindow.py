# coding=utf-8
""" docstring: 视频窗口 """

from PyQt5.QtWidgets import QMainWindow

from ui_VideoPage import Ui_MainWindow


class videoWindow(QMainWindow, Ui_MainWindow):
    """ docstring: 视频类 """
    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = videoWindow()
    window.show()
    sys.exit(app.exec_())
