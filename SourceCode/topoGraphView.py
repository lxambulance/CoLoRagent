# coding=utf-8
''' docstring: scene/view模型框架 '''

from NodeEdge import Node, Edge
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class topoGraphView(QGraphicsView):
    ''' docstring: 视图显示类 '''
    def __init__(self, scene, parent = None):
        super().__init__(parent)
        qsrand(QTime(0,0,0).secsTo(QTime.currentTime()))

        # 设置场景坐标
        # self.scene = scene
        self.setScene(scene)
        scene.setSceneRect(-5000, -5000, 10000, 10000)
        self.newEdge = None
        self.dstNode = Node(nodetype = -1)
        self.scene().addItem(self.dstNode)

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
        # 设置缩放锚定点
        self.setTransformationAnchor(self.AnchorUnderMouse)
        # 设置窗口拖动锚定点
        self.setResizeAnchor(self.AnchorViewCenter)
        # 设置水平竖直滚动条不显示
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setDragMode(self.RubberBandDrag)
    
        self._color_background = QColor('#eee5ff')
        self.setBackgroundBrush(self._color_background)

    def getItemAtClick(self, event):
        ''' docstring: 返回点击的物体 '''
        pos = event.pos()
        item = self.itemAt(pos)
        return item

    def mousePressEvent(self, event):
        ''' docstring: 鼠标按压事件 '''
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            item = self.getItemAtClick(event)
            if isinstance(item, Node):
                print(f"clicked {item.name}<{item.nid}>")
                if self.parent().addedgeenable and item.type < 3:
                    self.newEdge = Edge(item)
                    self.scene().addItem(self.newEdge)
                if item.type == 0:
                    print('AS', item.nid)
                    tmpitem, nodelist = self.scene().belongAS[item.nid]
                    for node in nodelist:
                        node.setSelected(True)
                if self.parent().accessrouterenable and item.type > 1 and item.type < 5:
                    if not self.scene().node_me:
                        self.scene().node_me = Node(nodetype=5, nodenid=self.scene().nid_me)
                        self.scene().addItem(self.scene().node_me)
                    if len(self.scene().node_me.edgenext) > 0:
                        for nextnode, nextedge in self.scene().node_me.edgenext.values():
                            del nextnode.edgenext[self.scene().node_me.nid]
                            self.scene().edges.remove(nextedge)
                            self.scene().removeItem(nextedge)
                        self.scene().node_me.edgenext.clear()
                    edgeitem = Edge(self.scene().node_me, item, linetype = 0)
                    self.scene().edges.append(edgeitem)
                    self.scene().addItem(edgeitem)
                    self.scene().node_me.edgenext[item.nid] = (item, edgeitem)
                    item.edgenext[self.scene().node_me.nid] = (self.scene().node_me, edgeitem)
                    
                    for tmpitem in self.scene().items():
                        if isinstance(tmpitem, Node):
                            print(tmpitem.nid, tmpitem.name)
                        if isinstance(tmpitem, Edge):
                            print('<', tmpitem.n1.nid, tmpitem.n2.nid, '>')

    def mouseMoveEvent(self, event):
        ''' docstring: 鼠标移动事件 '''
        super().mouseMoveEvent(event)
        if self.newEdge is not None and self.parent().addedgeenable:
            pos = event.pos()
            scenepos = self.mapToScene(pos)
            self.dstNode.setPos(scenepos)
            # TODO: 更好的EdgeDst更新方式
            self.newEdge.setEdgeDst(self.dstNode)
    
    def mouseReleaseEvent(self, event):
        ''' docstring: 鼠标回弹事件 '''
        super().mouseReleaseEvent(event)
        if self.parent().addedgeenable:
            self.parent().addedgeenable = False
            if self.newEdge is not None:
                item = self.getItemAtClick(event)
                if isinstance(item, Node):
                    self.newEdge.setEdgeDst(item)
                    self.scene().edge.append(self.newEdge)
                else:
                    self.scene().removeItem(self.newEdge)
                self.newEdge = None
        if self.parent().accessrouterenable:
            self.parent().accessrouterenable = False

    def keyPressEvent(self, event):
        ''' docstring: 键盘按压事件 '''
        key = event.key()
        if key == Qt.Key_Plus:
            self.scaleView(1.2)
        elif key == Qt.Key_Minus:
            self.scaleView(1 / 1.2)
        elif key == Qt.Key_Space or key == Qt.Key_Enter:
            # 按到空格或回车时随机排布场景中物体
            for item in self.scene().items():
                if isinstance(item, Node):
                    item.setPos(-1000 + qrand() % 2000, -1000 + qrand() % 2000)
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event):
        ''' docstring: 鼠标滚轮事件 '''
        self.scaleView(pow(2.0, -event.angleDelta().y() / 240.0))

    def scaleView(self, scaleFactor):
        ''' docstring: 调整视图大小 '''
        factor = self.transform().scale(scaleFactor, scaleFactor).mapRect(QRectF(0, 0, 1, 1)).width()
        # 对于单位矩阵宽度超出阈值的行为不与响应
        if factor < 0.05 or factor > 20:
            return
        self.scale(scaleFactor, scaleFactor)

if __name__ == "__main__":
    # 测试了如何在外部添加物体
    import sys
    import json
    app = QApplication(sys.argv)
    widget = topoGraphView()

    widget.loadTopo('d:/CodeHub/CoLoRagent/test/datatest.db')
    # widget.initTopo_old()
    widget.show()
    sys.exit(app.exec_())

    widget.saveTopo('d:/CodeHub/CoLoRagent/test/datatest.db')
