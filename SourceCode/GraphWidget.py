# coding=utf-8
''' docstring: Graphics/View模型框架 '''

from PointLine import Node, Line
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import math

class GraphWidget(QGraphicsView):
    ''' docstring: 视图显示类 '''
    def __init__(self, parent = None):
        super().__init__(parent)

        # 设置边框边距
        self.setStyleSheet("padding:0px;border:0px;")
        self.setWindowTitle("Zoom and Move")
        scene = QGraphicsScene(self)
        scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        scene.setSceneRect(-350, -350, 700, 700)
        self.setMinimumSize(400, 400)
        self.setScene(scene)
        self.setCacheMode(QGraphicsView.CacheBackground)
        # 设置视图更新模式，可以只更新矩形框，也可以全部更新
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        # self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)

        # 用于接管scene的鼠标按下功能，测试使用，使用时不可移动
        # scene.mousePressEvent = self.myMousePressEvent
        
    def keyPressEvent(self, event):
        ''' docstring: 键盘事件 '''
        key = event.key()
        if key == Qt.Key_Plus:
            self.scaleView(1.2)
        elif key == Qt.Key_Minus:
            self.scaleView(1 / 1.2)
        elif key == Qt.Key_Space or key == Qt.Key_Enter:
            # 按到空格或回车时随机排布场景中物体
            for item in self.scene().items():
                if isinstance(item, Node):
                    item.setPos(-200 + qrand() % 400, -200 + qrand() % 400)
        else:
            super(GraphWidget, self).keyPressEvent(event)

    def wheelEvent(self, event):
        ''' docstring: 鼠标滚轮事件 '''
        self.scaleView(math.pow(2.0, -event.angleDelta().y() / 240.0))

    def scaleView(self, scaleFactor):
        ''' docstring: 调整视图大小 '''
        factor = self.transform().scale(scaleFactor, scaleFactor).mapRect(QRectF(0, 0, 1, 1)).width()
        # 对于单位矩阵宽度超出阈值的行为不与响应
        if factor < 0.07 or factor > 100:
            return
        self.scale(scaleFactor, scaleFactor)

    def myMousePressEvent(self, mouseEvent):
        ''' docstring: 自定义鼠标事件，测试使用 '''
        print("myMousePressEvent",mouseEvent.type(),mouseEvent.scenePos())

if __name__ == "__main__":
    # 测试了如何在外部添加物体
    import sys
    app = QApplication(sys.argv)
    widget = GraphWidget()

    widget.node = [0] * 5
    for i in range(5):
        widget.node[i] = Node()
        widget.scene().addItem(widget.node[i])
        a = math.pi * 2 / 5
        R = 300
        x, y = round(math.cos(a*3/4+a*i) * R), round(math.sin(a*3/4+a*i) * R)
        widget.node[i].setPos(x, y)
    
    widget.line = [0] * 5
    for i in range(5):
        j = (i + 2) % 5
        widget.line[i] = Line(widget.node[i],widget.node[j],widget)
        widget.scene().addItem(widget.line[i])

    widget.show()
    sys.exit(app.exec_())
