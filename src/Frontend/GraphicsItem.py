# coding=utf-8
""" docstring: scene/view模型框架的几个基类 """


from math import fabs, atan2, pi, sin, cos, sqrt
from PyQt5.QtWidgets import (
    QGraphicsPixmapItem, QGraphicsLineItem, QGraphicsSimpleTextItem,
    QStyle, QGraphicsTextItem, QFontDialog, QColorDialog)
from PyQt5.QtGui import (
    QPen, QColor, QPixmap,
    QFont, QPainter, QPolygonF)
from PyQt5.QtCore import (
    QRectF, QPointF, QLineF, Qt)
import resource_rc


class Node(QGraphicsPixmapItem):
    """ docstring: 图形点类 """
    NodeTypeLen = 6
    NodeImageStr = [
        ':/topo/cloud', ':/topo/RM', ':/topo/BR',
        ':/topo/router', ':/topo/switching', ':/topo/PC'
    ]
    NodeZValue = [1, 10, 10, 10, 10, 10]
    NodeName = ['cloud', 'RM', 'BR', 'router', 'switch', 'agent']
    NodeSize = [256, 96, 96, 96, 96, 96]
    NodeNum = 0

    def __init__(self, nodetype=0, nodename=None, nodesize=0, nodenid=None, font=None, color=None, tfont=None, tcolor = None):
        super().__init__()
        self.myType = nodetype
        if not self.myType:
            self.childCount = 0
            self.clicktime = 0
        self.name = nodename or Node.NodeName[nodetype]
        self.size = nodesize or Node.NodeSize[nodetype]
        self.nid = nodenid or ""
        # 采用统一计数器，全局id唯一
        self.id = Node.NodeNum
        Node.NodeNum += 1
        # AS收发包数据统计量
        if not self.myType:
            self.getnum = 0
            self.getsize = 0
            self.datanum = 0
            self.datasize = 0
            self.setThroughputLabel(tfont, tcolor)
        
        # 设置图像大小和偏移量
        self.setPixmap(QPixmap(Node.NodeImageStr[self.myType]).scaled(self.size, self.size))
        self.setOffset(-self.size/2, -self.size/2) # 图像中点为物体坐标原点
        # 设置点可选中可移动
        self.setFlags(self.ItemIsSelectable | self.ItemIsMovable)
        self.setZValue(Node.NodeZValue[self.myType])

        # 添加一个子文本类显示名字
        color = QColor(color or '#ff8000')
        self.label = Text(self.name, self, font=font, color=color)
        self.label.hide()
        self.label.setZValue(Node.NodeZValue[self.myType]+1)
        # 设置文本位置
        if not self.myType:
            self.label.setTextWidth(self.size*2//3)
            self.label.setPos(-self.size/3, self.size/6)
        else:
            self.label.setTextWidth(self.size)
            self.label.setPos(-self.size/2, self.size/2)

        if self.myType == 5:
            self.addStarMark()

    def addStarMark(self):
        """ docstring: 给代理节点添加了一个醒目星标记，颜色在绘制时确定 """
        self.polygon = QPolygonF()
        myconst = sin(pi*7/10)/sin(pi/10)
        for i in range(10):
            alpha = i*pi/5 + pi/10
            r = self.size/3
            x = r*cos(alpha)
            y = r*sin(alpha)
            if (i&1):
                x *= myconst
                y *= myconst
            self.polygon.append(QPointF(x,y))

    def addClickTimes(self):
        """ docstring: 添加点击数，选择AS路径时使用 """
        self.clicktime += 1
        # print(self.name, self.clicktime)
        if self.clicktime & 1:
            self.setPixmap(QPixmap(':/topo/cloud-o').scaled(self.size, self.size))
        else:
            self.setPixmap(QPixmap(Node.NodeImageStr[self.myType]).scaled(self.size, self.size))

    def updateLabel(self, name = None, nid = None, getsize = 0, datasize = 0):
        """ docstring: 更新标签 """
        if name:
            self.name = name
            self.label.changeText(self.name)
        if nid:
            self.nid = nid
        if getsize:
            self.getnum += 1
            self.getsize += getsize
        if datasize:
            self.datanum += 1
            self.datasize += datasize
        if self.getsize or self.datasize:
            tmps = f"<div><p>发送数据包统计<br/>(数量，大小[字节]):</p>" + \
                   f"<p>get包 ({self.getnum},{self.getsize})</p>" + \
                   f"<p>data包 ({self.datanum},{self.datasize})</p></div>"
            self.throughputlabel.changeText(tmps)
        self.update()

    def setThroughputLabel(self, tfont, tcolor):
        tmps = f"<div><p>发送数据包统计<br/>(数量，大小[字节]):</p>" + \
               f"<p>get包 ({self.getnum},{self.getsize})</p>" + \
               f"<p>data包 ({self.datanum},{self.datasize})</p></div>"
        self.throughputlabel = Text(tmps, self, font=tfont, color=QColor("#0f0f0f" if not tcolor else tcolor))
        self.throughputlabel.hide()
        self.setZValue(Node.NodeZValue[self.myType]+1)
        self.throughputlabel.setTextWidth(self.size)
        self.throughputlabel.setPos(-self.size/2, self.size/2)

    def modifyCount(self, value):
        """ docstring: 用于云动态改变大小 """
        # TODO：修改得更精细化
        if self.myType:
            return
        self.childCount += value
        if value > 0:
            self.size += 32
        else:
            self.size -= 32
        self.setOffset(-self.size/2, -self.size/2)
        self.update()

    def mousePressEvent(self, event):
        """ docstring: 鼠标按下事件 """
        super().mousePressEvent(event)
        # AS选中时选中其中所有点
        if self.isSelected() and not self.myType:
            # print(self.id, self.name)
            for node in self.scene().ASinfo[self.id]:
                node.setSelected(True)

    def mouseMoveEvent(self, event):
        """ docstring: 鼠标移动事件 """
        super().mouseMoveEvent(event)
        # 选中移动时更新所连边类
        for item in self.scene().selectedItems():
            if isinstance(item, Node):
                tmplist = self.scene().nextedges.get(item.id, [])
                for nextnode, nextedge in tmplist:
                    nextedge.updateEdge()

    def paint(self, painter, option, widget):
        """ docstring: 绘制类，重构了部分图形选中时轮廓和背景 """
        if not self.myType:
            if not self.clicktime:
                if self.isSelected():
                    self.setPixmap(QPixmap(':/topo/cloud-o').scaled(self.size, self.size))
                else:
                    self.setPixmap(QPixmap(Node.NodeImageStr[self.myType]).scaled(
                        self.size, self.size))
        else:
            if self.isSelected():
                p = painter
                p.setRenderHint(QPainter.Antialiasing)
                p.setPen(QPen(QColor("#ff8000"), 4))
                bRect = QRectF(-self.size/2, -self.size/2, self.size, self.size)
                p.drawRect(bRect)
            elif self.myType == 5:
                p = painter
                # 决定星标记颜色 
                p.setPen(QPen(QColor("#ff8000"), 4))
                p.setBrush(QColor("#ff8000"))
                p.drawPolygon(self.polygon)
        option.state = QStyle.State_None
        super().paint(painter, option, widget)


class Edge(QGraphicsLineItem):
    """ docstring: 边类 """

    def __init__(self, node1, node2, linetype=0, linePX=None, font=None, color=None):
        super().__init__()
        # 实线0或虚线1或背景线2
        self.myType = linetype
        self.node1 = node1
        self.node2 = node2
        if linetype == 0:
            self.setPen(QPen(QColor("#6c62d0"), 4))
            self.setZValue(5)
            self.setFlags(self.ItemIsSelectable)
        elif linetype == 1:
            self.setPen(QPen(QColor("#6c62d0"), 4, Qt.DashDotDotLine))
            self.setZValue(5)
            self.setFlags(self.ItemIsSelectable)
        else:
            self.setPen(QPen(QColor("#111111"), 1, Qt.DotLine))
            self.setZValue(0)

        # 添加一个子文本类显示名字
        self.PX = linePX
        tmpname = ""
        if linePX:
            tmpname = f"PX:{self.PX}"
        font = font or QFont("Times New Roman", 12)
        color = QColor(color or '#ff0000')
        self.label = Text(tmpname, self if not linetype else None, font=font, color=color)
        self.label.hide()
        self.label.setZValue(11) # 没有效果，因为先比父节点Z值
        # 计算label位置坐标
        self.updateEdge()

    def calcLabelPos(self):
        """ docstring: 用于计算标签位置 """
        n1 = self.node1.scenePos()
        n2 = self.node2.scenePos()
        if n1.x()>n2.x() or fabs(n1.x()-n2.x())<1e-8 and n1.y()>n2.y():
            n1, n2 = n2, n1
        alpha = atan2(n2.y()-n1.y(), n2.x()-n1.x())
        len = sqrt((n1.x()-n2.x())*(n1.x()-n2.x())+(n1.y()-n2.y())*(n1.y()-n2.y()))
        if len > 200:
            self.label.setTextWidth(len*2/3)
            x = (n1.x()*5 + n2.x()) / 6
            y = (n1.y()*5 + n2.y()) / 6
        else:
            self.label.setTextWidth(len)
            x = n1.x()
            y = n1.y()
        self.label.setPos(x, y)
        self.label.setRotation(alpha/pi*180)

    def updateLabel(self, linePX):
        """ docstring: 更新标签内容 """
        self.PX = linePX
        self.label.setText(f"PX:{self.PX}")
        self.label.update()

    def updateEdge(self):
        """ docstring: 由于外部相关点修改导致边坐标需要重新计算 """
        n1 = self.node1.scenePos()
        n2 = self.node2.scenePos()
        self.setLine(QLineF(n1, n2))
        self.calcLabelPos()
        self.update()

    def paint(self, painter, option, widget):
        """ docstring: 用于显示被选中的变化，并且去掉外边框 """
        if self.node1 and self.node2 and \
            (self.node1.isSelected() and self.node2.isSelected() or self.isSelected()):
            painter.setPen(QPen(QColor('#3e9405'), 6)) #85f83a ff99e5 66ff33
            painter.drawLine(self.node1.scenePos(), self.node2.scenePos())
        else:
            # 设置绘图属性，去掉外边框，妥协的做法
            option.state = QStyle.State_None
            super().paint(painter, option, widget)


class Text(QGraphicsTextItem):
    """docstring: 文本类 """

    def __init__(self, content, parent = None, font = None, color = None, setAutoResize = False):
        super().__init__(parent=parent)
        self.parent = parent
        self.currentfont = font or QFont("Times New Roman", 25, QFont.Normal)
        self.currentcolor = color or QColor("#000000")
        self.setFont(self.currentfont)

        self.content = f"""<p align="center">{content}</p>"""
        self.setHtml(f"""<font color="{self.currentcolor.name()}">{self.content}</font>""")
        if setAutoResize:
            self.adjustSize()
        
        # self.setFlag(self.ItemIgnoresTransformations) # 设置文字忽略缩放
        # self.setFlags(self.ItemIsMovable | self.ItemIsSelectable) # 设置文字对象可移动和选中
        # self.setTextInteractionFlags(Qt.TextEditorInteraction) # 设置可交互

    def changeFont(self):
        """ docstring: 修改字体 """
        font, ok = QFontDialog.getFont(self.currentfont, caption="选择字体")
        if ok:
            self.setFont(font)
            self.currentfont = font
            self.adjustSize()

    def changeColor(self):
        """ docstring: 修改颜色 """
        color = QColorDialog.getColor(self.currentcolor)
        self.setHtml(f"""<font color="{color.name()}">{self.content}</font>""")
        self.currentcolor = color

    def changeText(self, content):
        """ docstring: 修改内容 """
        self.content = f"""<p align="center">{content}</p>"""
        self.setHtml(f"""<font color="{self.currentcolor.name()}">{self.content}</font>""")
