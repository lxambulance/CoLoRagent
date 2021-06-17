# coding=utf-8
''' docstring: CoLoR拓扑图窗口 '''

from PyQt5.QtWidgets import QMainWindow
from GraphicPage import Ui_MainWindow

from PyQt5.QtCore import (pyqtSignal, QObject)

class GraphicSignal(QObject):
    ''' docstring: 拓扑图专用信号返回 '''
    hide_window_signal = pyqtSignal(bool)

class GraphicWindow(QMainWindow, Ui_MainWindow):
    ''' docstring: CoLoR拓扑图窗口类 '''

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        self.GS = GraphicSignal()
    
    def closeEvent(self, event):
        self.GS.hide_window_signal.emit(False)
