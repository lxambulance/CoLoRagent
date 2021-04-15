# coding=utf-8
''' docstring: scene/view模型框架 '''

from json import load, dump
from math import pi, sin, cos
from PyQt5.QtWidgets import QGraphicsScene

from NodeEdge import Node, Edge

class topoGraphScene(QGraphicsScene):
    ''' docstring: 场景模型类 '''
    def __init__(self, parent = None):
        super().__init__(parent)
        self.node = []
        self.edge = []
        self.AS = {}
        self.topo = {}
        self.data = {}
    
    def initTopo(self):
        pass

    def initTopo_old(self):
        ''' docstring: 测试topu显示功能，画一个五角星 '''
        for i in range(5):
            self.node.append(Node)
            if (i == 4):
                self.node[i] = Node(myType = 2, nid = i)
            elif (i & 1):
                self.node[i] = Node(myType = 0, nid = i)
            else:
                self.node[i] = Node(myType = 1, nid = i)
            self.addItem(self.node[i])
            a = pi * 2 / 5
            R = 200
            x, y = round(cos(a*3/4+a*i) * R), round(sin(a*3/4+a*i) * R)
            self.node[i].setPos(x, y)
        self.node.append(Node(myType = 3, nid = 5))
        self.addItem(self.node[5])

        for i in range(5):
            self.node[5].addAS(self.node[i])
            j = (i + 2) % 5
            self.edge.append(Edge(self.node[i], self.node[j], myType = 1))
            self.addItem(self.edge[i])
    
    def loadTopo(self, path):
        ''' docstring: 载入拓扑图 '''
        with open(path, 'r') as f:
            self.data = load(f)
            self.topo = self.data.get('topo map', {})
        if len(self.topo) == 0:
            return
        nodetype = self.topo['node type']
        nodename = self.topo['node name']
        for i in range(len(nodetype)):
            if len(nodename[i]):
                self.node.append(Node(myType = nodetype[i], name = nodename[i], nid = i))
            else:
                self.node.append(Node(myType = nodetype[i], nid = i))
            self.addItem(self.node[i])
        edges = self.topo['edge']
        for edge in edges:
            x = edge[0]
            y = edge[1]
            self.edge.append(Edge(self.node[x], self.node[y], myType = 1))
            self.addItem(self.edge[-1])
        self.AS = self.topo['AS']
        for (k,v) in self.AS.items():
            for nid in v:
                self.node[int(k)].addAS(self.node[nid])
        for item in self.items():
                if isinstance(item, Node):
                    item.setPos(-200 + qrand() % 400, -200 + qrand() % 400)

    def saveTopo(self, path):
        ''' docstring: 存储拓扑图 '''
        with open(path, 'r') as f:
            self.data = load(f)
            self.topo = self.data.get('topo map', {})
        nodetype = []
        nodename = []
        AS = {}
        for i in range(len(self.node)):
            nodename.append(self.node[i].name)
            nodetype.append(self.node[i].type)
            if self.node[i].type == 3:
                list_nid = []
                for node in self.node[i].AS:
                    list_nid.append(node.nid)
                AS[i] = list_nid
        edge = []
        for i in range(len(self.edge)):
            x = self.edge[i].n1.nid
            y = self.edge[i].n2.nid
            edge.append([x, y])

        with open(path, 'w') as f:
            self.topo['node type'] = nodetype
            self.topo['node name'] = nodename
            self.topo['edge'] = edge
            self.topo['AS'] = AS
            self.data['topo map'] = self.topo
            dump(self.data, f)
