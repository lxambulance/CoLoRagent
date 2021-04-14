# coding=utf-8
''' docstring: scene/view模型框架 '''

from PyQt5.QtWidgets import QWidget, QVBoxLayout

from topoGraphView import topoGraphView
from topoGraphScene import topoGraphScene

class GraphicWindow(QWidget):
    ''' docstring: 拓扑图窗口类 '''
    def __init__(self, parent = None):
        super().__init__(parent)
        self.scene = topoGraphScene(self)
        self.view = topoGraphView(self.scene, self)

        # 设置最小大小
        self.setMinimumSize(400, 400)
        # 设置垂直布局方式
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)
    
    def initTopo_old(self):
        self.scene.initTopo_old()
        self.view.scaleView(0.6)
        self.scene.edge[0].changeType(0)
        
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    window = GraphicWindow()
    window.initTopo_old()
    window.show()
    sys.exit(app.exec_())
