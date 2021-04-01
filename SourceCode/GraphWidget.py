# coding=utf-8
''' docstring: Graphics/View模型框架 '''

from NodeEdge import Node, Edge
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import math
import json

class GraphWidget(QGraphicsView):
    ''' docstring: 视图显示类 '''
    def __init__(self, parent = None):
        super().__init__(parent)
        scene = QGraphicsScene(self)
        self.setScene(scene)
        self.node = []
        self.edge = []
        self.AS = {}
        self.topo = {}
        self.data = {}
        qsrand(QTime(0,0,0).secsTo(QTime.currentTime()))

        # 设置大小和坐标
        scene.setSceneRect(-200, -200, 400, 400)
        self.setMinimumSize(400, 400)
        # 设置视图更新模式，可以只更新矩形框，也可以全部更新 TODO: 更新效率
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        # 设置渲染属性
        self.setRenderHints(
            QPainter.Antialiasing |
            QPainter.HighQualityAntialiasing |
            QPainter.TextAntialiasing |
            QPainter.SmoothPixmapTransform |
            QPainter.LosslessImageRendering
            )
        self.setTransformationAnchor(self.AnchorUnderMouse) # 设置缩放锚定点
        self.setResizeAnchor(self.AnchorViewCenter) # 设置窗口拖动锚定点
        # 设置水平竖直滚动条不显示
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setDragMode(self.RubberBandDrag)

        self._color_background = QColor('#ffffe5')
        self.setBackgroundBrush(self._color_background)
    
    def getItemAtClick(self, event):
        ''' docstring: 返回点击的物体 '''
        pos = event.pos()
        item = self.itemAt(pos)
        return item

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            item = self.getItemAtClick(event)
            if isinstance(item, Node):
                print(f"Node[{item.type}]")

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
        if factor < 0.1 or factor > 20:
            return
        self.scale(scaleFactor, scaleFactor)

    def initTopo(self):
        pass

    def initTopo_old(self):
        ''' docstring: 测试topu显示功能，画一个五角星 '''
        for i in range(5):
            self.node.append(Node)
            if (i == 4):
                self.node[i] = Node(myType = 2, nid = i)
            elif (i & 1):
                self.node[i] = Node(myType = 0, nid = i)
            else:
                self.node[i] = Node(myType = 1, nid = i)
            self.scene().addItem(self.node[i])
            a = math.pi * 2 / 5
            R = 200
            x, y = round(math.cos(a*3/4+a*i) * R), round(math.sin(a*3/4+a*i) * R)
            self.node[i].setPos(x, y)
        self.node.append(Node(myType = 3, nid = 5))
        self.scene().addItem(self.node[5])

        for i in range(5):
            self.node[5].addAS(self.node[i])
            j = (i + 2) % 5
            self.edge.append(Edge(self.node[i], self.node[j], myType = 1))
            self.scene().addItem(self.edge[i])
        self.scaleView(0.6)
    
    def loadTopo(self, path):
        with open(path, 'r') as f:
            self.data = json.load(f)
            self.topo = self.data.get('topo map', {})
        if len(self.topo) == 0:
            return
        nodetype = self.topo['node type']
        nodename = self.topo['node name']
        for i in range(len(nodetype)):
            if len(nodename[i]):
                self.node.append(Node(myType = nodetype[i], name = nodename[i], nid = i))
            else:
                self.node.append(Node(myType = nodetype[i], nid = i))
            self.scene().addItem(self.node[i])
        edges = self.topo['edge']
        for edge in edges:
            x = edge[0]
            y = edge[1]
            self.edge.append(Edge(self.node[x], self.node[y], myType = 1))
            self.scene().addItem(self.edge[-1])
        self.AS = self.topo['AS']
        for (k,v) in self.AS.items():
            for nid in v:
                self.node[int(k)].addAS(self.node[nid])
        for item in self.scene().items():
                if isinstance(item, Node):
                    item.setPos(-200 + qrand() % 400, -200 + qrand() % 400)

    def saveTopo(self, path):
        with open(path, 'r') as f:
            self.data = json.load(f)
            self.topo = self.data.get('topo map', {})
        nodetype = []
        nodename = []
        AS = {}
        for i in range(len(self.node)):
            nodename.append(self.node[i].name)
            nodetype.append(self.node[i].type)
            if self.node[i].type == 3:
                list_nid = []
                for node in self.node[i].AS:
                    list_nid.append(node.nid)
                AS[i] = list_nid
        edge = []
        for i in range(len(self.edge)):
            x = self.edge[i].n1.nid
            y = self.edge[i].n2.nid
            edge.append([x, y])

        with open(path, 'w') as f:
            self.topo['node type'] = nodetype
            self.topo['node name'] = nodename
            self.topo['edge'] = edge
            self.topo['AS'] = AS
            self.data['topo map'] = self.topo
            json.dump(self.data, f)

if __name__ == "__main__":
    # 测试了如何在外部添加物体
    import sys
    import json
    app = QApplication(sys.argv)
    widget = GraphWidget()

    widget.loadTopo('d:/CodeHub/CoLoRagent/test/datatest.db')
    # widget.initTopo_old()
    widget.show()
    sys.exit(app.exec_())

    widget.saveTopo('d:/CodeHub/CoLoRagent/test/datatest.db')
