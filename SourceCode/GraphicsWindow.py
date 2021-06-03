# coding=utf-8
''' docstring: CoLoR拓扑图窗口 '''

from PyQt5.QtWidgets import QMainWindow
from GraphicsPage import Ui_MainWindow

class GraphicsWindow(QMainWindow, Ui_MainWindow):
    ''' docstring: CoLoR拓扑图窗口类 '''

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
