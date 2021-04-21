# coding=utf-8
''' docstring: scene/view模型框架 '''

from NodeEdge import Node, Edge
from PyQt5.QtWidgets import QGraphicsView
from PyQt5.QtCore import Qt, qrand, QRectF
from PyQt5.QtGui import QPainter, QColor


class topoGraphView(QGraphicsView):
    ''' docstring: 视图显示类 '''

    def __init__(self, scene, parent=None):
        super().__init__(parent)
        # 设置场景坐标
        self.setScene(scene)
        scene.setSceneRect(-5000, -5000, 10000, 10000)
        # 设置视图更新模式，可以只更新矩形框，也可以全部更新 TODO: 更新效率
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        # 设置渲染属性
        self.setRenderHints(
            QPainter.Antialiasing |
            QPainter.HighQualityAntialiasing |
            QPainter.TextAntialiasing |
            QPainter.SmoothPixmapTransform |
            QPainter.LosslessImageRendering)
        # 设置缩放锚定点
        self.setTransformationAnchor(self.AnchorUnderMouse)
        # 设置窗口拖动锚定点
        self.setResizeAnchor(self.AnchorViewCenter)
        # 设置水平竖直滚动条不显示
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setDragMode(self.RubberBandDrag)
        # 设置背景色
        self._color_background = QColor('#eee5ff')
        self.setBackgroundBrush(self._color_background)

    def getItemAtClick(self, event):
        ''' docstring: 返回点击的物体 '''
        pos = event.pos()
        item = self.itemAt(pos)
        return item

    def removeNode(self, item):
        ''' docstring: 删除节点 '''
        tmplist = self.scene().nextedges.get(item.nid, [])
        for nextnode, nextedge in tmplist:
            self.scene().nextedges[nextnode.nid].remove((item, nextedge))
            self.scene().removeItem(nextedge)
        self.scene().removeItem(item)

    def mousePressEvent(self, event):
        ''' docstring: 鼠标按压事件 '''
        # print('check accessrouterenable', self.parent().accessrouterenable)
        item = self.getItemAtClick(event)
        if event.button() == Qt.RightButton:
            if isinstance(item, Node):
                self.removeNode(item)
        elif self.parent().addedgeenable:
            if event.button() == Qt.LeftButton and isinstance(item, Node) and item.type:
                self.scene().tmpnode = item
                pos = self.mapToScene(event.pos())
                self.scene().tmpedge = Edge(item.scenePos(), pos)
                self.scene().addItem(self.scene().tmpedge)
        elif self.parent().accessrouterenable:
            if event.button() == Qt.LeftButton and isinstance(item, Node) and item.type in range(2,5):
                self.parent().signal_ret.choosenid.emit(f"{item.name}<{item.nid}>")
                if not self.scene().node_me:
                    self.scene().node_me = Node(nodetype=5, nodenid=self.scene().nid_me)
                    self.scene().addItem(self.scene().node_me)
                mynode = self.scene().node_me
                # 删除原有连边
                tmplist = self.scene().nextedges.get(mynode.nid, [])
                if len(tmplist):
                    for nextnode, edge in tmplist:
                        self.scene().delEdge(mynode, nextnode, edge)
                        self.scene().removeItem(edge)
                # 添加新连边
                newedge = Edge(mynode.scenePos(), item.scenePos(), linetype=0)
                self.scene().addItem(newedge)
                self.scene().addEdge(mynode, item, newedge)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        ''' docstring: 鼠标移动事件 '''
        if self.parent().addedgeenable and self.scene().tmpedge:
            pos = self.mapToScene(event.pos())
            self.scene().tmpedge.changeLine(self.scene().tmpnode.scenePos(), pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        ''' docstring: 鼠标回弹事件 '''
        if self.parent().addedgeenable:
            self.parent().addedgeenable = False
            item = self.getItemAtClick(event)
            if self.scene().tmpedge:
                if isinstance(item, Node) and item.type and item is not self.scene().tmpnode:
                    self.scene().tmpedge.changeLine(self.scene().tmpnode.scenePos(), item.scenePos())
                    tmpa = self.scene().belongAS.get(self.scene().tmpnode.nid, None)
                    tmpb = self.scene().belongAS.get(item.nid, None)
                    if tmpa and tmpb and tmpa is not tmpb:
                        self.scene().tmpedge.changeType(1)
                    self.scene().addEdge(self.scene().tmpnode, item, self.scene().tmpedge)
                else:
                    self.scene().removeItem(self.scene().tmpedge)
            self.scene().tmpedge = None
            self.scene().tmpnode = None
        elif self.parent().accessrouterenable:
            self.parent().accessrouterenable = False
        else:
            super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        ''' docstring: 键盘按事件 '''
        key = event.key()
        if key == Qt.Key_Plus:
            self.scaleView(1.2)
        elif key == Qt.Key_Minus:
            self.scaleView(1/1.2)
        elif key == Qt.Key_Space:
            # 按到空格或回车时随机排布场景中物体
            for item in self.scene().items():
                if isinstance(item, Node):
                    item.setPos(-1000 + qrand() % 2000, -1000 + qrand() % 2000)
        elif key == Qt.Key_N:
            s = ''
            for i in range(8):
                s += f'{qrand()%16:x}'
            newnode = Node(nodetype=qrand() %
                           6, nodename='test-only', nodenid=s)
            self.scene().addItem(newnode)
        elif key == Qt.Key_E:
            self.parent().addedgeenable = True
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event):
        ''' docstring: 鼠标滚轮事件 '''
        self.scaleView(pow(2.0, event.angleDelta().y() / 240.0))

    def scaleView(self, scaleFactor):
        ''' docstring: 调整视图大小 '''
        factor = self.transform().scale(
            scaleFactor, scaleFactor).mapRect(QRectF(0, 0, 1, 1)).width()
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
