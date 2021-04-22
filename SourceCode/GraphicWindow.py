# coding=utf-8
''' docstring: scene/view模型框架 '''

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtGui import QColor
from PyQt5.QtCore import qsrand, qrand, QTime, pyqtSignal, QObject

from topoGraphView import topoGraphView
from topoGraphScene import topoGraphScene


class GraphicMessage(QObject):
    ''' docstring: 拓扑图专用信号返回 '''
    choosenid = pyqtSignal(str)
    chooseitem = pyqtSignal(str, str)

class GraphicWindow(QWidget):
    ''' docstring: 拓扑图窗口类 '''

    def __init__(self, parent=None):
        super().__init__(parent)
        qsrand(QTime(0, 0, 0).secsTo(QTime.currentTime()))
        self.signal_ret = GraphicMessage()
        self.scene = topoGraphScene(self)
        self.view = topoGraphView(self.scene, self)
        self.addedgetype = 0
        self.addedgeenable = False
        self.accessrouterenable = False
        self.findpathenable = False
        self.labelenable = False
        self.chooseitem = None

        # 设置最小大小
        self.setMinimumSize(400, 400)
        # 设置垂直布局方式
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)

    def loadTopo(self, path):
        self.scene.initTopo_config(path)
        self.view.scaleView(0.35)

    def saveTopo(self, path):
        self.scene.saveTopo(path)

    def setBackground(self, colorstr):
        ''' docstring: 修改拓扑背景颜色以适配风格修改 '''
        self.view._color_background = QColor(colorstr)
        self.view.setBackgroundBrush(self.view._color_background)

    def setNid(self, nid):
        self.scene.nid_me = nid

    def changeItem(self, name, nid):
        if self.chooseitem in self.scene.items():
            self.chooseitem.updateLabel(name, nid)


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    window = GraphicWindow()
    window.scene.initTopo_config("D:/CodeHub/CoLoRagent/data.db")
    window.show()
    sys.exit(app.exec_())
