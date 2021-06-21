# coding=utf-8
''' docstring: CoLoR拓扑图窗口 '''

from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import pyqtSignal, QObject, Qt

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

        # 暂时隐藏拓扑修改按钮
        self.actionb.setVisible(False)
    
    def closeEvent(self, event):
        ''' docstring: 自定义关闭事件信号 '''
        self.GS.hide_window_signal.emit(False)

    def keyPressEvent(self, event):
        ''' docstring: 自定义键盘按事件 '''
        key = event.key()
        if key == Qt.Key_:
            self.scaleView(1.2)


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
