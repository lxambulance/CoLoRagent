# coding=utf-8
''' docstring: CoLoR拓扑图窗口 '''

from PyQt5.QtWidgets import QMainWindow, QPushButton
from PyQt5.QtCore import pyqtSignal, QObject, Qt
from PyQt5.QtGui import *

from GraphicPage import Ui_MainWindow


class GraphicSignal(QObject):
    ''' docstring: 拓扑图专用信号返回 '''
    hide_window_signal = pyqtSignal(bool)

class GraphicWindow(QMainWindow, Ui_MainWindow):
    ''' docstring: CoLoR拓扑图窗口类 '''

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.GS = GraphicSignal()
        self.flag_actionb = False

        # 暂时隐藏拓扑修改按钮
        self.actionb.setVisible(False)

        # 设置信号槽连接
        self.actionReopenToolbar.triggered.connect(self.resetToolbar) # 设置按钮还原工具栏

    def resetToolbar(self):
        ''' docstring: 还原工具栏位置，采用删除后重填加的方式 '''
        self.removeDockWidget(self.Toolbar)
        if not self.Toolbar.isVisible(): # visible是自身属性，可以直接修改
            self.Toolbar.toggleViewAction().trigger()
        self.addDockWidget(Qt.DockWidgetArea(Qt.LeftDockWidgetArea), self.Toolbar)
        if self.Toolbar.isFloating(): # floating属性涉及到外部dock位置，需要先确定父widget
            self.Toolbar.setFloating(False)

    def closeEvent(self, event):
        ''' docstring: 自定义关闭事件信号 '''
        self.GS.hide_window_signal.emit(False)
        super().closeEvent(event)

    def keyPressEvent(self, event):
        ''' docstring: 自定义键盘按事件 '''
        key = event.key()
        if key == Qt.Key_M:
            if self.flag_actionb:
                self.flag_actionb = False
                self.actionb.setVisible(False)
            else:
                self.flag_actionb = True
                self.actionb.setVisible(True)


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    window = GraphicWindow()
    DATAPATH = "D:/CodeHub/CoLoRagent/data.db"
    window.graphics_global.loadTopo(DATAPATH)
    window.show()
    ret = app.exec_()
    window.graphics_global.saveTopo(DATAPATH)
    sys.exit(ret)
