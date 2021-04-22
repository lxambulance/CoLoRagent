# coding=utf-8
''' docstring: scene/view模型框架 '''

from random import shuffle
from math import pi
from json import load, dump
from math import pi, sin, cos
from queue import Queue
from PyQt5.QtWidgets import QGraphicsScene
from PyQt5.QtCore import qsrand, qrand, QTime, pyqtSignal

from NodeEdge import Node, Edge


class topoGraphScene(QGraphicsScene):
    ''' docstring: 场景模型类 '''
    chooseRouter = pyqtSignal(str)
    choosePath = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tmpnode = None
        self.tmpedge = None

        self.node_me = None
        self.nid_me = None

        self.ASinfo = {} # ASnid:[node,...]
        self.belongAS = {} # nid:ASitem
        self.nextedges = {} # nid:[(nextnode, edge),...]
        self.R = 0 # 布局中大圆半径

        self.topo = {}
        self.data = {}

    def addEdge(self, n1, n2, edge):
        ''' docstring: 向nextedges字典中添加点-边映射（无向边） '''
        tmplist = self.nextedges.get(n1.nid, [])
        tmplist.append((n2, edge))
        self.nextedges[n1.nid] = tmplist
        tmplist = self.nextedges.get(n2.nid, [])
        tmplist.append((n1, edge))
        self.nextedges[n2.nid] = tmplist
        # 绑定对应点，便于删除
        edge.node1 = n1
        edge.node2 = n2

    def delEdge(self, n1, n2, edge):
        ''' docstring: 与上面操作相反 '''
        self.nextedges[n1.nid].remove((n2, edge))
        self.nextedges[n2.nid].remove((n1, edge))

    def findPath(self, dest):
        ''' docstring: 根据目标地址选择路径，返回经过节点nid路径 '''
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
            for nextnode, nextedge in self.nextedges[topnode.nid]:
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
                ret.append(now.nid)
                now.setSelected(True)
                now = now.prenode
            ret.reverse()
            return ret

    def initTopo_config(self, path):
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
            if ntp == 0:
                item = Node(nodetype = ntp, nodename = nnm, nodesize = node['size'])
                tmpass.append((i, item))
            elif ntp == 1:
                item = Node(nodetype = ntp, nodename = nnm, nodenid = node['nid'])
            elif ntp == 2 or ntp == 3:
                item = Node(nodetype = ntp, nodename = nnm, nodenid = node['nid'])
            elif ntp == 4:
                item = Node(nodetype = ntp, nodename = nnm)
            self.addItem(item)
            tmpnodes.append(item)
        # 添加AS信息
        self.R = 0
        self.ASinfo = {}
        self.belongAS = {}
        for (i, asitem) in tmpass:
            nodelist = [tmpnodes[x] for x in self.topo['ASinfo'][str(i)]]
            # 随机打乱
            shuffle(nodelist)
            self.R = max(self.R, len(nodelist))
            # 为了后续显示方便，将RM放首位置
            for (j, node) in enumerate(nodelist):
                if node.type == 1:
                    nodelist[0], nodelist[j] = nodelist[j], nodelist[0]
                    break
            nodelist.append(asitem)
            self.ASinfo[asitem.nid] = nodelist
            self.belongAS[asitem.nid] = asitem
            for x in self.topo['ASinfo'][str(i)]:
                self.belongAS[tmpnodes[x].nid] = asitem
        # 设置图元位置
        self.R *= 64
        num1 = len(self.ASinfo)
        now = 0
        for nodelist in self.ASinfo.values():
            alpha = pi * 2 / num1 * now
            now += 1
            X, Y = (-sin(alpha)*self.R, -cos(alpha)*self.R)
            # print(i, ':', alpha, '(', X, Y, ')', item.nid)
            asitem = nodelist.pop()
            asitem.setPos(X, Y)
            num2 = len(nodelist)
            r = num2*64*sin(pi/num1)
            for i, node in enumerate(nodelist):
                beta = pi * 2 / num2 * i + alpha
                x = X-sin(beta)*r
                y = Y-cos(beta)*r
                node.setPos(x, y)
        # 添加边
        for (x, y, PX) in self.topo['edges']:
            lt = 0
            if self.belongAS[tmpnodes[x].nid] is not self.belongAS[tmpnodes[y].nid]:
                lt = 1
            if not len(PX):
                edgeitem = Edge(tmpnodes[x].scenePos(), tmpnodes[y].scenePos(), linetype = lt)
            else:
                edgeitem = Edge(tmpnodes[x].scenePos(), tmpnodes[y].scenePos(), linetype = lt, linePX = PX)
            self.addItem(edgeitem)
            self.addEdge(tmpnodes[x], tmpnodes[y], edgeitem)

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
            tmpedge = Edge(nodes[i*2+1].scenePos(), nodes[j*2+1].scenePos(), linetype=qrand()%2)
            self.addItem(tmpedge)
            self.addEdge(nodes[i*2+1], nodes[j*2+1], tmpedge)

    def saveTopo(self, path):
        ''' docstring: 存储拓扑图（未完成） '''
        # TODO: 存储时如何不影响已经写了的部分
        with open(path, 'r') as f:
            self.data = load(f)
        with open(path, 'w') as f:
            # TODO: 需要用现有信息改写topo内容
            dump(self.data, f)
