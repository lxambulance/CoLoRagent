# coding=utf-8
''' docstring: Graphics/View模型框架的两个基类 '''

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import resource_rc

class nlSignals(QObject):
    ''' docstring: 用于Node与Line通信 '''
    nl = pyqtSignal()

class Node(QGraphicsItem):
    ''' docstring: Node类 '''
    def __init__(self, parent = None):
        super().__init__(parent)
        self.n2l = nlSignals()
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.setZValue(1)
        # todo: 通过记号决定画的图片类型

    def boundingRect(self):
        adjust = 2.0
        return QRectF(QPointF(-32 - adjust, -32 - adjust),
                      QPointF(32 + adjust, 32 + adjust))

    def paint(self, painter, option, widget):
        painter.setPen(QPen(Qt.green, 0))
        painter.setBrush(Qt.red)
        painter.drawImage(-32,-32,QImage(':/icon/router'))
        self.n2l.nl.emit()

class Line(QGraphicsItem):
    ''' docstring: 直线类，包含两个Node的指针，通过信号与槽更新 '''
    def __init__(self, n1, n2, parent):
        super().__init__()
        self.n1 = n1
        self.n2 = n2
        self.n1.n2l.nl.connect(parent.update)
        self.n2.n2l.nl.connect(parent.update)
        self.setZValue(0)
        # todo: 通过记号决定画得线的类型，虚线或实线

    def boundingRect(self):
        adjust = 2.0
        mx = min(self.n1.scenePos().x(), self.n2.scenePos().x())
        Mx = max(self.n1.scenePos().x(), self.n2.scenePos().x())
        my = min(self.n1.scenePos().y(), self.n2.scenePos().y())
        My = max(self.n1.scenePos().y(), self.n2.scenePos().y())
        return QRectF(QPointF(mx - adjust, my - adjust),
                      QPointF(Mx + adjust, My + adjust))

    def paint(self, painter, option, widget):
        painter.setPen(QPen(Qt.red, 2))
        painter.drawLine(self.n1.scenePos(), self.n2.scenePos())
