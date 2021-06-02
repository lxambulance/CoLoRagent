# coding=utf-8
''' docstring: scene/view模型框架 '''

from NodeEdge import Node, Edge
from PyQt5.QtWidgets import QGraphicsView
from PyQt5.QtCore import (QParallelAnimationGroup, Qt, qrand, QRectF, QPointF, 
    QEasingCurve, QPropertyAnimation, pyqtProperty)
from PyQt5.QtGui import QPainter, QColor


class topoGraphView(QGraphicsView):
    ''' docstring: 视图显示类 '''

    def __init__(self, scene, parent=None):
        super().__init__(parent)
        self.allmove = False
        self.tmppos = None

        # 设置场景坐标
        self.setScene(scene)
        self.scene().setSceneRect(-5000, -5000, 10000, 10000)
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
        self.setTransformationAnchor(self.AnchorViewCenter)
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
        # print(item.name, item.id)
        if item.type == 0 and len(self.scene().ASinfo[item.id]) > 1:
            # print([x.id for x in self.scene().ASinfo[item.id]])
            return
        tmpas = self.scene().belongAS.pop(item.id, None)
        if tmpas:
            tmpas.modifyCount(-1)
            tmpnodelist = self.scene().ASinfo[tmpas.id]
            # print('before', [tmpnodelist[x].name for x in range(len(tmpnodelist))])
            tmpnodelist.remove(item)
            if len(tmpnodelist) == 0:
                self.scene().ASinfo.pop(tmpas.id)
        tmplist = self.scene().nextedges.pop(item.id, [])
        for nextnode, nextedge in tmplist:
            self.scene().nextedges[nextnode.id].remove((item, nextedge))
            self.scene().removeItem(nextedge)
        if item in self.scene().waitlist:
            self.scene().waitlist.remove(item)
        self.scene().removeItem(item)

    def mousePressEvent(self, event):
        ''' docstring: 鼠标按压事件 '''
        item = self.getItemAtClick(event)
        if event.button() == Qt.RightButton:
            # print(item.name, item.id)
            if isinstance(item, Node):
                if item is self.scene().node_me:
                    self.scene().node_me = None
                self.removeNode(item)
            elif isinstance(item, Edge):
                self.scene().delEdge(item.node1, item.node2, item)
                self.scene().removeItem(item)
            else:
                self.tmppos = self.mapToScene(event.pos())
                self.allmove = True
        elif self.parent().addedgeenable:
            if event.button() == Qt.LeftButton and isinstance(item, Node) \
                    and item not in self.scene().waitlist \
                    and (self.parent().addedgetype!=0 or item.type == 2 or item.type == 0):
                self.scene().tmpnode = item
                self.tmppos = item.scenePos()
                # 增加一个虚拟点用于建边的时候移动
                self.scene().tmpnode_transparent = Node()
                self.scene().tmpnode_transparent.hide()
                self.scene().tmpnode_transparent.setPos(item.scenePos())
                self.scene().tmpedge = Edge(item, self.scene().tmpnode_transparent, linetype=self.parent().addedgetype)
                self.scene().addItem(self.scene().tmpnode_transparent)
                self.scene().addItem(self.scene().tmpedge)
        elif self.parent().findpathenable:
            if event.button() == Qt.LeftButton and isinstance(item, Node) and item.type:
                # TODO: 多线程处理
                nidlist = self.scene().findPath(item)
                print(nidlist)
        else:
            if event.button() == Qt.LeftButton:
                if isinstance(item, Node):
                    asitem = self.scene().belongAS.get(item.id, None)
                    if not asitem:
                        asstr = '???<???>(???)'
                    else:
                        asstr = f"{asitem.name}<{asitem.nid}>({asitem.id})"
                    self.parent().chooseItem = item
                    self.parent().signal_ret.chooseitem.emit(item.name, item.nid, asstr)
                    if item.type == 0 and self.parent().chooseASenable:
                        item.addClickTimes()
                elif isinstance(item, Edge):
                    n1 = f"{item.node1.name}<{item.node1.nid}>"
                    n2 = f"{item.node2.name}<{item.node2.nid}>"
                    linename = f"Edge<{item.type}>({n1},{n2})"
                    linePX = f"PX:{item.PX}"
                    self.parent().chooseItem = item
                    self.parent().signal_ret.chooseitem.emit(linename, linePX, "")
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        ''' docstring: 鼠标移动事件 '''
        pos = self.mapToScene(event.pos())
        if self.parent().addedgeenable and self.scene().tmpedge:
            newpos = QPointF((pos.x()*99+self.tmppos.x())/100,(pos.y()*99+self.tmppos.y())/100)
            self.scene().tmpnode_transparent.setPos(newpos)
            self.scene().tmpedge.updateEdge()
        if self.allmove:
            for item in self.scene().items():
                if isinstance(item, Node):
                    itempos = item.scenePos()
                    x = itempos.x() + (pos.x() - self.tmppos.x())
                    y = itempos.y() + (pos.y() - self.tmppos.y())
                    item.setPos(QPointF(x, y))
            for item in self.scene().items():
                if isinstance(item, Edge):
                    item.updateEdge()
            self.tmppos = pos
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        ''' docstring: 鼠标回弹事件 '''
        if self.parent().addedgeenable:
            self.parent().addedgeenable = False
            item = self.getItemAtClick(event)
            # print('check', item.type, self.scene().tmpnode.type)
            if self.scene().tmpedge:
                if isinstance(item, Node) and item is not self.scene().tmpnode \
                        and item not in self.scene().waitlist \
                        and (self.parent().addedgetype!=0 or item.type == 2 or \
                            (item.type == 0 and self.scene().tmpnode.type == 0)) \
                        and (self.parent().addedgetype!=1 or self.scene().belongAS[item.id] \
                        ==self.scene().belongAS[self.scene().tmpnode.id]):
                    if item.type == 0:
                        # 连边对象是两个AS，需要新建两个BR
                        node1 = Node(2)
                        node2 = Node(2)
                        self.scene().addItem(node1)
                        self.scene().addItem(node2)
                        if self.parent().labelenable:
                            node1.label.show()
                            node2.label.show()
                        pos1 = item.scenePos()
                        pos2 = self.scene().tmpnode.scenePos()
                        node1.setPos(QPointF((pos1.x()*78+pos2.x()*22)/100,
                            (pos1.y()*78+pos2.y()*22)/100))
                        node2.setPos(QPointF((pos1.x()*22+pos2.x()*78)/100,
                            (pos1.y()*22+pos2.y()*78)/100))
                        self.scene().ASinfo[item.id].append(node1)
                        self.scene().belongAS[node1.id] = item
                        item.modifyCount(1)
                        self.scene().ASinfo[self.scene().tmpnode.id].append(node2)
                        self.scene().belongAS[node2.id] = self.scene().tmpnode
                        self.scene().tmpnode.modifyCount(1)
                        self.scene().waitlist.append(self.scene().tmpedge)
                        self.scene().addEdge(node1, node2, self.scene().tmpedge)
                        self.scene().tmpedge.updateEdge()
                    else:
                        # 正常连边，虚实都有
                        if self.scene().tmpedge.type == 0:
                            self.scene().waitlist.append(self.scene().tmpedge)
                        self.scene().addEdge(self.scene().tmpnode, item, self.scene().tmpedge)
                        self.scene().tmpedge.updateEdge()
                else:
                    self.scene().removeItem(self.scene().tmpedge)
                self.scene().removeItem(self.scene().tmpnode_transparent)
            self.scene().tmpedge = None
            self.scene().tmpnode = None
            self.scene().tmpnode_transparent = None
        if self.parent().findpathenable:
            self.parent().findpathenable = False
        if self.allmove:
            self.allmove = False
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
        # elif key == Qt.Key_N:
        #     s = ''
        #     for i in range(6):
        #         s += f'{qrand()%16:x}'
        #     newnode = Node(nodetype=qrand() %
        #                    6, nodename='test-only', nodenid=s)
        #     if self.parent().labelenable:
        #         newnode.label.show()
        #     self.scene().addItem(newnode)
        elif key == Qt.Key_E:
            self.parent().addedgeenable = True
        elif key == Qt.Key_F:
            self.parent().findpathenable = True
        elif key == Qt.Key_S:
            self.parent().labelenable = not self.parent().labelenable
            for item in self.items():
                if isinstance(item, Node) or isinstance(item, Edge):
                    if self.parent().labelenable:
                        item.label.show()
                    else:
                        item.label.hide()
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
    pass
