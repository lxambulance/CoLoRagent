# coding=utf-8
''' docstring: scene/view模型框架的两个基类 '''

from PyQt5.QtWidgets import (
    QGraphicsPixmapItem, QGraphicsSimpleTextItem, QGraphicsLineItem)
from PyQt5.QtGui import QPen, QColor, QPixmap, QColor
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
            nodenid = ''
            for i in range(32):
                nodenid += f"{qrand()%16:x}"
        self.nid = nodenid

        # 设置图像大小和偏移量
        self.setPixmap(QPixmap(NodeImageStr[nodetype]).scaled(self.size, self.size))
        self.setOffset(-self.size/2, -self.size/2)

        # 添加一个子文本类显示名字
        self.label = QGraphicsSimpleTextItem(f"{self.name}<{self.nid}>", self)
        self.label.setPos(-self.size/2, self.size/2)
        self.label.setBrush(QColor(Qt.red))

        # 设置点可选中可移动
        self.setFlags(self.ItemIsSelectable | self.ItemIsMovable)
        # 设置高度信息
        self.setZValue(NodeZValue[nodetype])
        self.label.setZValue(NodeZValue[nodetype])

    def mouseMoveEvent(self, event):
        # AS选中时选中其中所有点
        if self.isSelected() and not self.type:
            for node in self.scene().ASinfo[self.nid]:
                node.setSelected(True)
        super().mouseMoveEvent(event)
        # 选中移动时更新所连边类
        for item in self.scene().selectedItems():
            tmplist = self.scene().nextedges.get(item.nid, [])
            for nextnode, nextedge in tmplist:
                nextedge.changeLine(item.scenePos(), nextnode.scenePos())


class Edge(QGraphicsLineItem):
    ''' docstring: 边类'''

    def __init__(self, n1, n2, *, linetype=0):
        super().__init__()
        # 虚线1或实线0
        self.type = None
        self.changeType(linetype)
        
        # print(f"new edge<({n1.x()},{n1.y()}),({n2.x()},{n2.y()})>")
        self.setLine(QLineF(n1, n2))
        self.setFlags(self.ItemIsSelectable)
        
        # 设置高度信息
        self.setZValue(0)

    def changeLine(self, n1, n2):
        self.setLine(QLineF(n1, n2))
        self.update()

    def changeType(self, linetype):
        self.type = linetype
        if linetype == 0:
            self.setPen(QPen(QColor("#0099ff"), 4))
        else:
            self.setPen(QPen(QColor("#00cc00"), 4, Qt.DashDotDotLine))
        self.update()

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        