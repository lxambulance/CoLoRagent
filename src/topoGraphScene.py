# coding=utf-8
''' docstring: scene/view模型框架 '''

from random import shuffle
from math import pi, fabs, sin, cos
from json import load, dump
from queue import Queue
from PyQt5.QtGui import QColor, QPen, QPixmap, QFont
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsPixmapItem, QGraphicsScene
from PyQt5.QtCore import qrand, Qt, QPoint
from GraphicsItem import Node, Edge, Text
import resource_rc


class topoGraphScene(QGraphicsScene):
    ''' docstring: 场景模型类 '''

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tmpnode = None
        self.tmpnode_transparent = None
        self.tmpedge = None
        self.signal_to_mainwindow = None

        # 添加特殊节点用于收包动画显示
        # TODO: 建立新的点类
        self.node_file = QGraphicsEllipseItem(-12,-12,24,24)
        self.node_file_img = QGraphicsPixmapItem(QPixmap(':/file/document').scaled(80, 72), self.node_file)
        self.node_file_img.setOffset(-40, -90)
        self.node_file.setPen(QPen(QColor('#ffff80'),2))
        self.node_file.setBrush(Qt.red)
        self.node_file.setZValue(20)
        self.addItem(self.node_file)
        self.node_file.hide()

        # 设置特殊文本类显示信息
        self.baseinfo = Text("信息显示框",
            font =QFont("SimHei", 10, QFont.Normal),
            color=QColor("#ff8000"))
        self.addItem(self.baseinfo)
        self.baseinfo.setFlag(self.baseinfo.ItemIgnoresTransformations)
        self.baseinfo.hide()

        # 观察节点特殊记录
        self.node_me = None
        self.nid_me = None
        self.waitlist = [] # 用于暂存添加到topo图中的新节点修改属性

        # 绘制背景线
        self.backgroundLines = []
        for i in range(-250, 250):
            j = i+250
            n1 = Node(nodetype=1)
            n2 = Node(nodetype=1)
            n1.setPos(i*20, -5000)
            n2.setPos(i*20, 5000)
            e = Edge(n1, n2, 2)
            e.setFlag(e.ItemIsSelectable, False)
            if j%8==0:
                e.setPen(QPen(QColor("#111111"), 2, Qt.DotLine))
            self.addItem(e)
            self.backgroundLines.append(e)
            n3 = Node(nodetype=1)
            n4 = Node(nodetype=1)
            n3.setPos(-5000, i*20)
            n4.setPos(5000, i*20)
            e = Edge(n3, n4, 2)
            e.setFlag(e.ItemIsSelectable, False)
            if j%8==0:
                e.setPen(QPen(QColor("#111111"), 2, Qt.DotLine))
            self.addItem(e)
            self.backgroundLines.append(e)

        # 拓扑图主要参数
        self.ASinfo = {} # AS所含节点信息，格式：id:[node,...]
        self.belongAS = {} # 节点所属AS，格式：id:ASitem
        self.nextedges = {} # 边表，邻接表存储，格式：id:[(nextnode, edge),...]
        self.R = 0 # 布局中大圆半径

        # json格式转换时临时保存参数
        self.topo = {}
        self.data = {}

    def addEdge(self, n1, n2, edge):
        ''' docstring: 向nextedges字典中添加点-边映射（无向边） '''
        tmplist = self.nextedges.get(n1.id, [])
        tmplist.append((n2, edge))
        self.nextedges[n1.id] = tmplist
        tmplist = self.nextedges.get(n2.id, [])
        tmplist.append((n1, edge))
        self.nextedges[n2.id] = tmplist
        # 绑定对应点，便于边操作
        edge.node1 = n1
        edge.node2 = n2

    def delEdge(self, n1, n2, edge):
        ''' docstring: 与上面操作相反 '''
        self.nextedges[n1.id].remove((n2, edge))
        self.nextedges[n2.id].remove((n1, edge))

    def findPath(self, dest):
        ''' docstring: 选择最短路径，以观察节点为起点，返回到目标节点的路径（nid序列） '''
        if self.node_me == None:
            return None
        # print('init')
        for item in self.items():
            if isinstance(item, Node):
                item.setSelected(False)
                item.isvisited = False
                item.prenode = None
        # print('start')
        tmpqueue = Queue()
        tmpqueue.put(self.node_me)
        self.node_me.isvisited = True
        while not tmpqueue.empty():
            topnode = tmpqueue.get()
            for nextnode, nextedge in self.nextedges[topnode.id]:
                if not nextnode.isvisited:
                    tmpqueue.put(nextnode)
                    nextnode.isvisited = True
                    nextnode.prenode = topnode
        # print('get ans')
        if not dest.isvisited:
            return None
        else:
            ret = []
            now = dest
            while now:
                ret.append(now.id)
                now.setSelected(True)
                now = now.prenode
            ret.reverse()
            return ret

    def resetPos(self):
        # 设置图元位置
        num1 = len(self.ASinfo)
        self.R = 32 * num1 + 256
        now = 0
        for nodelist in self.ASinfo.values():
            alpha = pi * 2 / num1 * now
            now += 1
            X, Y = (-sin(alpha)*self.R, -cos(alpha)*self.R)
            # print(i, ':', alpha, '(', X, Y, ')', item.nid)
            asitem = nodelist.pop()
            asitem.setPos(X, Y)
            num2 = len(nodelist)
            r = num2 * 16 + 100
            for i, node in enumerate(nodelist):
                beta = pi * 2 / num2 * i + alpha
                x = X-sin(beta)*r
                y = Y-cos(beta)*r
                node.setPos(x, y)
            nodelist.append(asitem)

    def initTopo(self, path):
        ''' docstring: 初始化拓扑为配置文件信息 '''
        with open(path, 'r') as f:
            self.data = load(f)
            self.topo = self.data.get('topo map', {})
        if len(self.topo) == 0:
            return
        
        # 添加节点
        tmpass = []
        tmpnodes = []
        for i in range(len(self.topo['nodes'])):
            node = self.topo['nodes'][i]
            ntp = node['type']
            nnm = node.get('name', None)
            nsz = node.get('size', 0)
            nid = node.get('nid', None)
            font = node.get('font', None)
            if font:
                nft = QFont()
                nft.fromString(font)
            else:
                nft = None
            ncr = node.get('color', None)
            item = Node(ntp, nnm, nsz, nid, nft, ncr)
            self.addItem(item)
            pos = node['pos']
            item.setPos(pos[0], pos[1])
            if ntp == 0:
                tmpass.append((i, item))
            elif ntp == 5:
                self.node_me = item
            tmpnodes.append(item)
        # 添加AS信息
        self.ASinfo = {}
        self.belongAS = {}
        for (i, asitem) in tmpass:
            nodelist = [tmpnodes[x] for x in self.topo['ASinfo'][str(i)]]
            nodelist.append(asitem)
            self.ASinfo[asitem.id] = nodelist
            self.belongAS[asitem.id] = asitem
            for x in self.topo['ASinfo'][str(i)]:
                self.belongAS[tmpnodes[x].id] = asitem
        # 添加边
        for item in self.topo['edges']:
            x = item[0]
            y = item[1]
            if len(item) > 2:
                font = None
                if len(item) > 3:
                    font = QFont()
                    font.fromString(item[3])
                color = None
                if len(item) > 4:
                    color = item[4]
                edgeitem = Edge(tmpnodes[x], tmpnodes[y], 0, item[2], font, color)
            else:
                edgeitem = Edge(tmpnodes[x], tmpnodes[y], linetype = 1)
            self.addItem(edgeitem)
            self.addEdge(tmpnodes[x], tmpnodes[y], edgeitem)
        
        # 根据标志位显示标签
        if self.parent().labelenable:
            for item in self.items():
                if isinstance(item, Node) or isinstance(item, Edge):
                    item.label.show()
        if self.parent().throughputenable:
            for item in self.items():
                if isinstance(item, Node) and not item.myType:
                    if item.id == self.belongAS[self.node_me.id].id:
                        continue
                    item.throughputlabel.show()

    def saveTopo(self, path):
        ''' docstring: 存储拓扑图 '''
        with open(path, 'r') as f:
            self.data = load(f)
        self.topo = {}

        # 删除所有还在waitlist中的点，视为添加失败
        for item in self.waitlist:
            self.removeItem(item)
        # 删除所有背景线
        for item in self.backgroundLines:
            self.removeItem(item)
        # 添加点
        tmpnodes = []
        tmpnodemap = {}
        num = 0
        for item in self.items():
            if isinstance(item, Node):
                node = {}
                node['type'] = item.myType
                if item.myType == 0:
                    node['size'] = item.size
                elif item.myType == 1 or item.myType == 2 or item.myType==5:
                    node['nid'] = item.nid
                node['pos'] = [item.scenePos().x(), item.scenePos().y()]
                node['name'] = item.name
                node['font'] = item.label.currentfont.toString()
                node['color'] = item.label.currentcolor.name()
                tmpnodes.append(node)
                tmpnodemap[item.id] = num
                num += 1
        self.topo['nodes'] = tmpnodes
        # 添加边
        tmpedges = []
        for item in self.items():
            if isinstance(item, Edge):
                x = tmpnodemap[item.node1.id]
                y = tmpnodemap[item.node2.id]
                if item.PX:
                    font = item.label.currentfont.toString()
                    color = item.label.currentcolor.name()
                    tmpedges.append([x, y, item.PX, font, color])
                else:
                    tmpedges.append([x, y])
        self.topo['edges'] = tmpedges
        # 添加AS信息
        tmpasinfo = {}
        for asid, nodes in self.ASinfo.items():
            x = tmpnodemap[asid]
            y = []
            for node in nodes:
                z = tmpnodemap[node.id]
                if x != z:
                    y.append(z)
            tmpasinfo[str(x)] = y
        self.topo['ASinfo'] = tmpasinfo

        with open(path, 'w') as f:
            self.data['topo map'] = self.topo
            dump(self.data, f)
