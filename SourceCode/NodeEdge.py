# coding=utf-8
''' docstring: Graphics/View模型框架的两个基类 '''

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import resource_rc

class nlSignals(QObject):
    ''' docstring: 用于Node与Line通信 '''
    nl = pyqtSignal()

NodeTypeLen = 4
NodeName = ['router', 'BR', 'RM', 'cloud']
NodeBRectLen = [32, 32, 32, 256]
NodeImageStr = [':/icon/router', ':/icon/BR', ':/icon/RM', ':/icon/cloud']
NodeZValue = [1, 2, 3, -1]

class Node(QGraphicsItem):
    ''' docstring: Node类 '''
    def __init__(self, *, myType = 0, name = None, nid = -1):
        super().__init__()
        self.n2l = nlSignals()

        self.setFlag(self.ItemIsSelectable)
        self.setFlag(self.ItemIsMovable)
        self.setCacheMode(self.DeviceCoordinateCache)
        self.type = myType
        self.name = name or NodeName[myType]
        self.setZValue(NodeZValue[myType])
        self.nid = nid
        self.AS = []

    def addAS(self, node):
        self.AS.append(node)

    def boundingRect(self):
        adjust = 2.0
        length = NodeBRectLen[self.type]
        return QRectF(QPointF(-length - adjust, -length - adjust),
                      QPointF(length + adjust, length + adjust))

    def paint(self, painter, option, widget):
        length = NodeBRectLen[self.type]
        qimagestr = NodeImageStr[self.type]
        painter.drawImage(-length, -length, QImage(qimagestr))

        font = painter.font()
        font.setPixelSize(20)
        painter.setFont(font)
        painter.setPen(QPen(Qt.red, 2))
        painter.drawText(-length, length-15, self.name)
        self.n2l.nl.emit()

class Edge(QGraphicsItem):
    ''' docstring: 边类，包含两个Node的指针，通过信号与槽更新 '''
    def __init__(self, n1, n2, *, myType = 0):
        super().__init__()
        self.n1 = n1
        self.n2 = n2
        self.n1.n2l.nl.connect(self.update)
        self.n2.n2l.nl.connect(self.update)
        self.setZValue(0)
        # TODO: 通过记号决定画得线的类型，虚线或实线
        self.type = myType

    def boundingRect(self):
        adjust = 2.0
        mx = min(self.n1.scenePos().x(), self.n2.scenePos().x())
        Mx = max(self.n1.scenePos().x(), self.n2.scenePos().x())
        my = min(self.n1.scenePos().y(), self.n2.scenePos().y())
        My = max(self.n1.scenePos().y(), self.n2.scenePos().y())
        return QRectF(QPointF(mx - adjust, my - adjust),
                      QPointF(Mx + adjust, My + adjust))

    def paint(self, painter, option, widget):
        if (self.type == 1):
            pen = QPen(QColor('#cc3399'), 2)
            pen.setStyle(Qt.DashDotDotLine)
        else:
            pen = QPen(Qt.black, 2)
        painter.setPen(pen)
        painter.drawLine(self.n1.scenePos(), self.n2.scenePos())
