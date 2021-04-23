# coding=utf-8
''' docstring: scene/view模型框架的两个基类 '''

from re import compile
from PyQt5.QtWidgets import (
    QGraphicsPixmapItem, QGraphicsSimpleTextItem, QGraphicsLineItem)
from PyQt5.QtGui import QPen, QColor, QPixmap, QColor, QFont
from PyQt5.QtCore import QObject, pyqtSignal, QRectF, QPointF, QLineF, Qt, qsrand, qrand, QTime

import resource_rc

pattern = compile('.{12}')
NodeTypeLen = 6
NodeImageStr = [':/icon/cloud', ':/icon/RM', ':/icon/BR',
                ':/icon/router', ':/icon/switching', ':/icon/PC']
NodeZValue = [-1, 10, 10, 10, 10, 10]
NodeName = ['cloud', 'RM', 'BR', 'router', 'switch', 'PC']
NodeSize = [512, 64, 64, 64, 64, 64]


class Node(QGraphicsPixmapItem):
    ''' docstring: 图形点类 '''

    def __init__(self, *, nodetype=0, nodename=None, nodesize=0, nodenid=None):
        super().__init__()
        self.type = nodetype
        self.name = nodename or NodeName[nodetype]
        self.size = nodesize or NodeSize[nodetype]
        if not nodenid:
            nodenid = ''
            for i in range(32):
                nodenid += f"{qrand()%16:x}"
        self.nid = nodenid

        # 设置图像大小和偏移量
        self.setPixmap(QPixmap(NodeImageStr[nodetype]).scaled(self.size, self.size))
        self.setOffset(-self.size/2, -self.size/2)

        # 添加一个子文本类显示名字
        tmps = f"{self.name}<{self.nid}>"
        if self.type:
            tmps = '\n'.join(pattern.findall(tmps))
        self.label = QGraphicsSimpleTextItem(tmps, self)
        # self.label.setFont(QFont("Times", 8))
        self.label.setPos(-self.size/2, self.size/2)
        self.label.setBrush(QColor(Qt.red))
        self.label.hide()

        # 设置点可选中可移动
        self.setFlags(self.ItemIsSelectable | self.ItemIsMovable)
        # 设置高度信息
        self.setZValue(NodeZValue[nodetype])
        self.label.setZValue(NodeZValue[nodetype])
    
    def updateLabel(self, name, nid):
        print('lxsb', name, nid)
        self.name = name
        self.nid = nid
        tmps = f"{self.name}<{self.nid}>"
        if self.type:
            tmps = '\n'.join(pattern.findall(tmps))
        self.label.setText(tmps)
        self.update()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        # AS选中时选中其中所有点
        if self.isSelected() and not self.type:
            # print(self.nid, self.name)
            for node in self.scene().ASinfo[self.nid]:
                node.setSelected(True)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        # 选中移动时更新所连边类
        for item in self.scene().selectedItems():
            if isinstance(item, Node):
                tmplist = self.scene().nextedges.get(item.nid, [])
                for nextnode, nextedge in tmplist:
                    nextedge.changeLine(item.scenePos(), nextnode.scenePos())

class Edge(QGraphicsLineItem):
    ''' docstring: 边类'''

    def __init__(self, n1, n2, *, linetype=0, linePX=None):
        super().__init__()
        # 虚线1或实线0
        self.type = None
        self.changeType(linetype)
        self.node1 = None
        self.node2 = None
        
        # print(f"new edge<({n1.x()},{n1.y()}),({n2.x()},{n2.y()})>")
        self.setLine(QLineF(n1, n2))
        self.n1 = n1
        self.n2 = n2
        self.setFlags(self.ItemIsSelectable)

        # 添加一个子文本类显示名字
        self.PX = linePX
        if linePX:
            name = f"PX:{self.PX}"
        else:
            name = ""
        self.label = QGraphicsSimpleTextItem(name, self)
        self.label.setFont(QFont("Times", 20, QFont.Bold))
        self.label.setPos(self.midpoint(n1,n2))
        self.label.setBrush(QColor(Qt.red))
        self.label.setZValue(1)
        self.label.hide()
        
        # 设置高度信息
        self.setZValue(0)

    def midpoint(self, n1, n2):
        x = (n1.x() + n2.x()) / 2
        y = (n1.y() + n2.y()) / 2
        return QPointF(x, y)

    def changeLine(self, n1, n2):
        self.setLine(QLineF(n1, n2))
        self.label.setPos(self.midpoint(n1,n2))
        self.n1 = n1
        self.n2 = n2
        self.update()

    def changeType(self, linetype):
        self.type = linetype
        if linetype == 0:
            self.setPen(QPen(QColor("#0099ff"), 4))
        else:
            self.setPen(QPen(QColor("#00cc00"), 4, Qt.DashDotDotLine))
        self.update()

    def paint(self, painter, option, widget):
        if self.node1 and self.node2 and \
            (self.node1.isSelected() and self.node2.isSelected() or self.isSelected()):
            painter.setPen(QPen(QColor('#66ff66'), 12))
            painter.drawLine(self.n1, self.n2)
        super().paint(painter, option, widget)
        