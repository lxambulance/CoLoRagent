# coding=utf-8
''' docstring: scene/view模型框架的两个基类 '''

from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtCore import QObject, pyqtSignal, QRectF, QPointF, Qt, qsrand, qrand, QTime
from PyQt5.QtGui import QPen, QColor, QImage

import resource_rc

NodeTypeLen = 6
NodeImageStr = [':/icon/cloud', ':/icon/RM', ':/icon/BR', 
    ':/icon/router', ':/icon/switching', ':/icon/PC']
NodeZValue = [-1, 10, 10, 10, 10, 10]
NodeName = ['cloud', 'RM', 'BR', 'router', 'switch', 'PC']
NodeSize = [512, 64, 64, 64, 64, 64]

class nlSignal(QObject):
    ''' docstring: 用于Node触发Line更新的信号 '''
    nl = pyqtSignal()

class Node(QGraphicsItem):
    ''' docstring: 点类 '''
    def __init__(self, *, nodetype = 0, nodename = None, nodesize = 0, nodenid = None):
        super().__init__()
        self.n2l = nlSignal()

        # 设置点可选中可移动
        self.setFlags(self.ItemIsSelectable | self.ItemIsMovable)
        # 设置缓存类型，与渲染速度有关。TODO：更有效的渲染方式
        # self.setCacheMode(self.DeviceCoordinateCache)

        self.edgenext = {}
        self.type = nodetype
        self.name = nodename or NodeName[nodetype]
        self.size = nodesize or NodeSize[nodetype]
        if not nodenid:
            nodenid = ''
            for i in range(32):
                nodenid += f"{qrand()%16:x}"
        self.nid = nodenid

        self.setZValue(NodeZValue[nodetype])

    def boundingRect(self):
        if self.type < 0:
            return QRectF(0,0,0,0)
        adjust = 4.0
        length = self.size / 2
        return QRectF(QPointF(-length - adjust, -length - adjust),
                      QPointF(length + adjust, length + adjust))

    def paint(self, painter, option, widget):
        if self.type < 0:
            return
        length = self.size / 2
        qimagestr = NodeImageStr[self.type]
        if self.isSelected():
            painter.setPen(QPen(Qt.yellow, 4))
            painter.drawRect(self.boundingRect())
            # print(self.type, self.size)
        img = QImage(qimagestr).scaled(self.size, self.size)
        painter.drawImage(-length, -length, img)

        font = painter.font()
        font.setPixelSize(20)
        painter.setFont(font)
        painter.setPen(QPen(Qt.red, 2))
        painter.drawText(-length, length-15, self.name)
        self.n2l.nl.emit()

class Edge(QGraphicsItem):
    ''' docstring: 边类，包含两个Node的指针，通过信号槽更新 '''
    def __init__(self, n1, n2 = None, *, linetype = 0):
        super().__init__()
        self.n1 = n1
        self.n1.n2l.nl.connect(self.update)
        if n2 is not None:
            self.n2 = n2
            self.n2.n2l.nl.connect(self.update)
        else:
            self.n2 = n1
        self.setZValue(0)
        # TODO: 通过记号决定画的线的类型，虚线1或实线0
        self.type = linetype

    def setEdgeDst(self, dst):
        ''' docstring: 设置边n2点位置，初始化时允许为None '''
        self.n2 = dst
        self.n2.n2l.nl.connect(self.update)
        self.update()

    def changeType(self, newType):
        ''' docstring: 边类型改变，触发更新 '''
        self.type = newType
        self.update()

    def boundingRect(self):
        # TODO: 修改边选中框为线条
        adjust = 2.0
        mx = min(self.n1.scenePos().x(), self.n2.scenePos().x())
        Mx = max(self.n1.scenePos().x(), self.n2.scenePos().x())
        my = min(self.n1.scenePos().y(), self.n2.scenePos().y())
        My = max(self.n1.scenePos().y(), self.n2.scenePos().y())
        return QRectF(QPointF(mx - adjust, my - adjust),
                      QPointF(Mx + adjust, My + adjust))

    def paint(self, painter, option, widget):
        if self.n1.isSelected() or self.n2.isSelected():
            painter.setPen(QPen(QColor('#99ff99'), 12))
            painter.drawLine(self.n1.scenePos(), self.n2.scenePos())
        if (self.type == 1):
            pen = QPen(QColor('#00cc00'), 4)
            pen.setStyle(Qt.DashDotDotLine)
        else:
            pen = QPen(QColor('#0099ff'), 4)
        painter.setPen(pen)
        painter.drawLine(self.n1.scenePos(), self.n2.scenePos())
