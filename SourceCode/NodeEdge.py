# coding=utf-8
''' docstring: scene/view模型框架的两个基类 '''

from math import fabs
from PyQt5.QtWidgets import (
    QGraphicsPixmapItem, QGraphicsSimpleTextItem, QGraphicsLineItem)
from PyQt5.QtGui import QPen, QColor, QPixmap, QColor, QFont
from PyQt5.QtCore import QObject, pyqtSignal, QRectF, QPointF, QLineF, Qt, qsrand, qrand, QTime

import resource_rc

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
            nodenid = '142857'
            for i in range(26):
                nodenid += f"{qrand()%16:x}"
        self.nid = nodenid

        # 设置图像大小和偏移量
        self.setPixmap(QPixmap(NodeImageStr[nodetype]).scaled(self.size, self.size))
        self.setOffset(-self.size/2, -self.size/2)

        # 添加一个子文本类显示名字
        tmps = f"{self.name}<{self.nid}>"
        if self.type:
            tmps = '\n'.join([tmps[x:x+12] for x in range(0,len(tmps),12)])
            # print(tmps)
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
    
    def updateLabel(self, *, name = None, nid = None):
        if name:
            self.name = name
        if nid:
            self.nid = nid
        tmps = f"{self.name}<{self.nid}>"
        if self.type:
            tmps = '\n'.join([tmps[x:x+12] for x in range(0,len(tmps),12)])
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

    def updateLabel(self, linePX):
        self.PX = linePX
        self.label.setText(f"PX:{self.PX}")
        self.label.update()

    def midpoint(self, n1, n2):
        if n1.x()>n2.x() or fabs(n1.x()-n2.x())<1e-8 and n1.y()>n2.y():
            n1, n2 = n2, n1
        x = (n1.x()*3 + n2.x()*2) / 5
        y = (n1.y()*3 + n2.y()*2) / 5
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
        