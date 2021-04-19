# coding=utf-8
''' docstring: scene/view模型框架 '''

from math import pi
from json import load, dump
from math import pi, sin, cos
from PyQt5.QtWidgets import QGraphicsScene
from PyQt5.QtCore import qsrand, qrand, QTime

from NodeEdge import Node, Edge


class topoGraphScene(QGraphicsScene):
    ''' docstring: 场景模型类 '''

    def __init__(self, parent=None):
        super().__init__(parent)
        qsrand(QTime(0,0,0).secsTo(QTime.currentTime()))
        self.nodes = []
        self.edges = []
        self.ASinfo = []
        self.belongAS = {}
        self.R = 0

        self.topo = {}
        self.data = {}

    def initTopo(self):
        pass

    def initTopo_startest(self):
        ''' docstring: 测试topo显示功能，画一个五角星 '''
        for i in range(5):
            if (i == 4):
                tmpitem = Node(nodetype=1)
            elif (i & 1):
                tmpitem = Node(nodetype=2)
            else:
                tmpitem = Node(nodetype=3)
            self.addItem(tmpitem)
            a = pi * 2 / 5
            R = 200
            x, y = round(cos(a*3/4+a*i) * R), round(sin(a*3/4+a*i) * R)
            tmpitem.setPos(x, y)
        self.addItem(Node(nodetype=0))

        nodes = self.items()
        for i in range(5):
            j = (i + 2) % 5
            self.addItem(Edge(nodes[i], nodes[j], linetype=1))

    def calcItemsPos(self):
        ''' docstring: 计算每个物体的位置，实现自动布局 '''
        # 方案0：随机布局
        # for item in self.items():
        #     if isinstance(item, Node):
        #         item.setPos(-1000 + qrand() % 2000, -1000 + qrand() % 2000)

        # 方案1：递归画圆布局
        self.R *= 64
        num1 = len(self.ASinfo)
        for i, (item, nodelist) in enumerate(self.ASinfo):
            alpha = pi * 2 / num1 * i
            X, Y = (-sin(alpha)*self.R, -cos(alpha)*self.R)
            print(i, ':', alpha, '(', X, Y, ')', item.nid)
            item.setPos(X, Y)
            num2 = len(nodelist)
            r = num2*64*sin(pi/num1)
            for j, node in enumerate(nodelist):
                beta = pi*2 / num2 * j
                x = X-sin(beta)*r
                y = Y-cos(beta)*r
                node.setPos(x, y)

    def _loadTopo(self, path):
        ''' docstring: 载入拓扑图 '''
        with open(path, 'r') as f:
            self.data = load(f)
            self.topo = self.data.get('topo map', {})
        if len(self.topo) == 0:
            return
        self.nodes = []
        tmpas = []
        for i in range(len(self.topo['nodes'])):
            node = self.topo['nodes'][i]
            ntp = node['type']
            if ntp == 0:
                item = Node(nodetype = ntp, nodename = node.get('name', None), 
                    nodesize = node['size'], nodenid = len(tmpas))
                tmpas.append((i, item))
            elif ntp == 1:
                item = Node(nodetype = ntp, nodename = node.get('name', None), nodenid = node['nid'])
            elif ntp == 2 or ntp == 3:
                item = Node(nodetype = ntp, nodenid = node['nid'])
            elif ntp == 4:
                item = Node(nodetype = ntp)
            self.addItem(item)
            self.nodes.append(item)
        self.edges = []
        for (x, y) in self.topo['edges']:
            item = Edge(self.nodes[x], self.nodes[y], linetype = 0)
            self.addItem(item)
            self.edges.append(item)
        self.ASinfo = []
        self.R = 0
        self.belongAS = {}
        for (i, item) in tmpas:
            nodelist = [self.nodes[x] for x in self.topo['ASinfo'][str(i)]]
            self.ASinfo.append((item, nodelist))
            self.R = max(self.R, len(nodelist))
            for x in self.topo['ASinfo'][str(i)]:
                self.belongAS[x]=len(self.ASinfo)
        for i, (x, y) in enumerate(self.topo['edges']):
            if self.belongAS[x] != self.belongAS[y]:
                self.edges[i].changeType(1)
        self.calcItemsPos()

    def _saveTopo(self, path):
        ''' docstring: 存储拓扑图（未完成） '''
        # TODO: 存储时如何不影响已经写了的部分
        with open(path, 'r') as f:
            self.data = load(f)
        with open(path, 'w') as f:
            # TODO: 需要用现有信息改写topo内容
            dump(self.data, f)
