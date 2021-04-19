# coding=utf-8
''' docstring: scene/view模型框架 '''

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtGui import QColor

from topoGraphView import topoGraphView
from topoGraphScene import topoGraphScene

class GraphicWindow(QWidget):
    ''' docstring: 拓扑图窗口类 '''
    def __init__(self, parent = None):
        super().__init__(parent)
        self.scene = topoGraphScene(self)
        self.view = topoGraphView(self.scene, self)
        self.addedgeenable = False

        # 设置最小大小
        self.setMinimumSize(400, 400)
        # 设置垂直布局方式
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)
    
    def initTopo(self):
        self.scene.initTopo_startest()
        self.view.scaleView(0.6)
        # self.scene.edge[0].changeType(0) # 测试修改功能
    
    def loadTopo(self, path):
        self.scene._loadTopo(path)
        self.view.scaleView(0.5)

    def saveTopo(self, path):
        self.scene._saveTopo(path)

    def setBackground(self, colorstr):
        ''' docstring: 修改拓扑背景颜色以适配风格修改 '''
        self.view._color_background = QColor(colorstr)
        self.view.setBackgroundBrush(self.view._color_background)
        
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    window = GraphicWindow()
    window.loadTopo('D:/CodeHub/CoLoRagent/test/datatest_human.db')
    window.show()
    sys.exit(app.exec_())
