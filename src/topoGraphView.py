# coding=utf-8
""" docstring: scene/view模型框架 """

from GraphicsItem import Node, Edge, Text
from PyQt5.QtWidgets import QGraphicsView
from PyQt5.QtCore import (Qt, QRectF, QPointF, QPoint)
from PyQt5.QtGui import QPainter, QColor


class topoGraphView(QGraphicsView):
    """ docstring: 视图显示类 """

    def __init__(self, scene, parent=None):
        super().__init__(parent)
        self.signal_to_mainwindow = None
        self.allmove = False
        self.tmppos = None
        self.selectedItem = None
        self.selectedText = None

        # 设置场景坐标
        self.setScene(scene)
        self.scene().setSceneRect(-5000, -5000, 10000, 10000)
        # 设置视图更新模式，可以只更新矩形框，也可以全部更新
        # TODO: 更新效率
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        # 设置渲染属性
        self.setRenderHints(
            # QPainter.Antialiasing |
            # QPainter.HighQualityAntialiasing |
            # QPainter.TextAntialiasing |
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
        self._color_background = QColor('#ffffff')
        self.setBackgroundBrush(self._color_background)

    def getItemAtClick(self, event):
        """ docstring: 返回点击的物体 """
        pos = event.pos()
        item = self.itemAt(pos)
        tmppos = self.mapToScene(pos)
        self.signal_to_mainwindow.emit(1, f"点击位置<{tmppos.x():.1f},{tmppos.y():.1f}>")
        return item

    def removeNode(self, item):
        """ docstring: 删除节点，步骤较繁琐，主要要考虑对所有参数的影响 """
        # print(item.name, item.id)
        if not isinstance(item, Node) or item.myType == 0 and len(self.scene().ASinfo[item.id]) > 1: # 内部含有东西的AS不能直接删除
            # print([x.id for x in self.scene().ASinfo[item.id]])
            return
        tmpas = self.scene().belongAS.pop(item.id, None) # 获取所属AS节点列表，修改belongAS
        if tmpas:
            tmpas.modifyCount(-1)
            tmpnodelist = self.scene().ASinfo[tmpas.id]
            # print('before', [tmpnodelist[x].name for x in range(len(tmpnodelist))])
            tmpnodelist.remove(item)
            if len(tmpnodelist) == 0:
                self.scene().ASinfo.pop(tmpas.id)
        tmplist = self.scene().nextedges.pop(item.id, []) # 获取所在边表，修改nextedges
        for nextnode, nextedge in tmplist:
            self.scene().nextedges[nextnode.id].remove((item, nextedge))
            self.scene().removeItem(nextedge)
        if item in self.scene().waitlist: # 查看是否在等待列表中
            self.scene().waitlist.remove(item)
        self.scene().removeItem(item)
        if item is self.scene().node_me:
            self.scene().node_me = None

    def removeEdge(self, item):
        if not isinstance(item, Edge):
            return
        self.scene().delEdge(item.node1, item.node2, item)
        self.scene().removeItem(item)

    def mousePressEvent(self, event):
        """ docstring: 鼠标按下事件 """
        item = self.getItemAtClick(event)
        if event.button() == Qt.RightButton:
            if isinstance(item, Text) and item.parent:
                item = item.parent
            if isinstance(item, Node):
                self.removeNode(item)
            elif isinstance(item, Edge):
                self.removeEdge(item)
            else:
                self.tmppos = self.mapToScene(event.pos())
                self.allmove = True
        elif self.parent().addedgeenable:
            if event.button() == Qt.LeftButton and isinstance(item, Node) \
                    and item not in self.scene().waitlist \
                    and (self.parent().addedgetype!=0 or item.myType == 2 or item.myType == 0):
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
            if event.button() == Qt.LeftButton and isinstance(item, Node) and item.myType:
                # TODO: 多线程处理
                nidlist = self.scene().findPath(item)
                print(nidlist)
        else:
            # 设置点到文字等于点到对应物体
            flag = False
            if isinstance(item, Text):
                flag = True
                if item.parent:
                    self.selectedText = item
                    item = item.parent
            if event.button() == Qt.LeftButton:
                if isinstance(item, Node):
                    if flag:
                        tmppos = self.mapToScene(event.pos())
                        self.signal_to_mainwindow.emit(1, f"点击位置<{tmppos.x():.1f},{tmppos.y():.1f}> 已选中Node文本")
                        flag = False
                    self.parent().chooseItem = item
                    asitem = self.scene().belongAS.get(item.id, None)
                    asstr = f"{asitem.name}" if asitem else ""
                    if item.myType:
                        message = "节点名称:"+item.name+"<br/>" \
                            + "nid:"+item.nid+"<br/>" \
                            + "所属AS:"+asstr
                    else:
                        message = "名称:"+item.name
                    self.signal_to_mainwindow.emit(2, message)
                    self.selectedItem = item
                    if item.myType == 0 and self.parent().chooseASenable:
                        item.addClickTimes()
                elif isinstance(item, Edge) and item.myType < 2:
                    if flag:
                        tmppos = self.mapToScene(event.pos())
                        self.signal_to_mainwindow.emit(1, f"点击位置<{tmppos.x():.1f},{tmppos.y():.1f}> 已选中Edge文本")
                        flag = False
                    self.parent().chooseItem = item
                    n1 = f"{item.node1.name}"
                    n2 = f"{item.node2.name}"
                    message = "边类型:"+('域内' if item.myType else '跨域')+"<br/>" \
                        + "端点:"+f"{n1}-----{n2}"
                    if item.PX:
                        message = message + "<br/>PX: " + item.PX
                    self.signal_to_mainwindow.emit(2, message)
                    self.selectedItem = item
                else:
                    self.parent().chooseItem = None
                    self.signal_to_mainwindow.emit(2, "信息显示框")
                    self.selectedItem = None
            super().mousePressEvent(event)
            if flag:
                self.selectedText = None

    def mouseMoveEvent(self, event):
        """ docstring: 鼠标移动事件 """
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
        """ docstring: 鼠标释放事件 """
        if self.parent().addedgeenable:
            self.parent().addedgeenable = False
            item = self.getItemAtClick(event)
            # print('check', item.myType, self.scene().tmpnode.myType)
            if self.scene().tmpedge:
                if isinstance(item, Node) and item is not self.scene().tmpnode \
                        and item not in self.scene().waitlist \
                        and (self.parent().addedgetype!=0 or item.myType == 2 or \
                            (item.myType == 0 and self.scene().tmpnode.myType == 0)) \
                        and (self.parent().addedgetype!=1 or self.scene().belongAS[item.id] \
                        ==self.scene().belongAS[self.scene().tmpnode.id]):
                    if item.myType == 0:
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
                        if self.scene().tmpedge.myType == 0:
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
        """ docstring: 键盘按下事件 """
        key = event.key()
        if key == Qt.Key_Plus: # 键盘加，作用同鼠标滚轮
            self.scaleView(1.2)
        elif key == Qt.Key_Minus: # 键盘减，作用同鼠标滚轮
            self.scaleView(1/1.2)
        elif key == Qt.Key_E: # 加边快捷键
            self.parent().addedgeenable = True
        elif key == Qt.Key_F: # 寻路快捷键
            self.parent().findpathenable = True
        elif key == Qt.Key_S: # 隐藏所有文字快捷键
            self.parent().labelenable = not self.parent().labelenable
            for item in self.items():
                if isinstance(item, Node) or isinstance(item, Edge):
                    if self.parent().labelenable:
                        item.label.show()
                    else:
                        item.label.hide()
        else: # 非上述事件由基类负责响应
            super().keyPressEvent(event)

    def wheelEvent(self, event):
        """ docstring: 鼠标滚轮事件，缩放 """
        self.scaleView(pow(2.0, event.angleDelta().y() / 240.0))

    def scaleView(self, scaleFactor):
        """ docstring: 按比例调整视图大小 """
        factor = self.transform().scale(scaleFactor, scaleFactor).mapRect(QRectF(0, 0, 1, 1)).width()
        # 对于单位矩阵宽度超出阈值的缩放行为不与响应
        if factor > 0.05 and factor < 20:
            if factor > 4:
                keynum = 1
            elif factor > 1:
                keynum = 2
            elif factor > 0.5:
                keynum = 4
            elif factor > 0.17:
                keynum = 8
            else:
                keynum = 16
            for i, line in enumerate(self.scene().backgroundLines):
                if i % (keynum * 2) < 2:
                    line.show()
                else:
                    line.hide()
            self.scale(scaleFactor, scaleFactor)
            self.resetNodeInfoPos()

    def resetNodeInfoPos(self):
        h = self.viewport().height()
        h0 = self.scene().baseinfo.document().size().height()
        pos = self.mapToScene(QPoint(0, h-h0))
        self.scene().baseinfo.setPos(pos)
