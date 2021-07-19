# coding=utf-8
''' docstring: scene/view模型框架 '''

from random import shuffle
from math import pi, fabs, sin, cos
from json import load, dump
from queue import Queue
from PyQt5.QtGui import QColor, QPen, QPixmap
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsPixmapItem, QGraphicsScene
from PyQt5.QtCore import qsrand, qrand, QTime, pyqtSignal, Qt
from scapy.fields import X3BytesField

from GraphicsItem import Node, Edge
import resource_rc


class topoGraphScene(QGraphicsScene):
    ''' docstring: 场景模型类 '''

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tmpnode = None
        self.tmpnode_transparent = None
        self.tmpedge = None

        # 添加特殊节点用于收包动画显示
        self.node_file = QGraphicsEllipseItem(-12,-12,24,24)
        self.node_file_img = QGraphicsPixmapItem(QPixmap(':/file/document').scaled(50, 50), self.node_file)
        self.node_file_img.setOffset(-25, -62)
        self.node_file.setPen(QPen(QColor('#ffff80'),2))
        self.node_file.setBrush(Qt.red)
        self.node_file.setZValue(20)
        self.addItem(self.node_file)
        self.node_file.hide()

        # 观察节点特殊记录
        self.node_me = None
        self.nid_me = None
        self.waitlist = [] # 用于暂存添加到topo图中的新节点修改属性

        # 绘制背景线
        self.backgroundLines = []
        for i in range(-250, 250):
            n1 = Node(nodetype=1)
            n2 = Node(nodetype=1)
            n1.setPos(i*20, -5000)
            n2.setPos(i*20, 5000)
            e = Edge(n1, n2, 2)
            e.setFlag(e.ItemIsSelectable, False)
            self.addItem(e)
            self.backgroundLines.append(e)
            n3 = Node(nodetype=1)
            n4 = Node(nodetype=1)
            n3.setPos(-5000, i*20)
            n4.setPos(5000, i*20)
            e = Edge(n3, n4, 2)
            e.setFlag(e.ItemIsSelectable, False)
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
            pos = node['pos']
            if ntp == 0:
                item = Node(nodetype = ntp, nodename = nnm, nodesize = node['size'])
                tmpass.append((i, item))
            elif ntp == 1:
                item = Node(nodetype = ntp, nodename = nnm, nodenid = node['nid'])
            elif ntp == 2 or ntp == 3:
                item = Node(nodetype = ntp, nodename = nnm, nodenid = node['nid'])
            elif ntp == 4:
                item = Node(nodetype = ntp, nodename = nnm)
            else:
                item = Node(nodetype = ntp, nodename = 'Me', nodenid = node['nid'])
                self.node_me = item
            self.addItem(item)
            item.setPos(pos[0], pos[1])
            tmpnodes.append(item)
        # 添加AS信息
        self.ASinfo = {}
        self.belongAS = {}
        for (i, asitem) in tmpass:
            nodelist = [tmpnodes[x] for x in self.topo['ASinfo'][str(i)]]
            # 随机打乱
            shuffle(nodelist)
            # 为了后续显示方便，将RM放首位置
            for (j, node) in enumerate(nodelist):
                if node.type == 1:
                    nodelist[0], nodelist[j] = nodelist[j], nodelist[0]
                    break
            nodelist.append(asitem)
            self.ASinfo[asitem.id] = nodelist
            # print([nodelist[x].name for x in range(len(nodelist))])
            self.belongAS[asitem.id] = asitem
            for x in self.topo['ASinfo'][str(i)]:
                self.belongAS[tmpnodes[x].id] = asitem
                # 直接载入云大小，不需要统计
                # asitem.modifyCount(1)
        # 设置图元位置
        # num1 = len(self.ASinfo)
        # self.R = 32 * num1 + 256
        # now = 0
        # for nodelist in self.ASinfo.values():
        #     alpha = pi * 2 / num1 * now
        #     now += 1
        #     X, Y = (-sin(alpha)*self.R, -cos(alpha)*self.R)
        #     # print(i, ':', alpha, '(', X, Y, ')', item.nid)
        #     asitem = nodelist.pop()
        #     asitem.setPos(X, Y)
        #     num2 = len(nodelist)
        #     r = num2 * 16 + 100
        #     for i, node in enumerate(nodelist):
        #         beta = pi * 2 / num2 * i + alpha
        #         x = X-sin(beta)*r
        #         y = Y-cos(beta)*r
        #         node.setPos(x, y)
        #     nodelist.append(asitem)
        # 添加边
        for (x, y, PX) in self.topo['edges']:
            lt = 1
            if self.belongAS[tmpnodes[x].id] is not self.belongAS[tmpnodes[y].id]:
                lt = 0
            if tmpnodes[x] == self.node_me:
                self.parent().signal_ret.choosenid.emit(f"{tmpnodes[y].name}<{tmpnodes[y].nid}>")
            elif tmpnodes[y] == self.node_me:
                self.parent().signal_ret.choosenid.emit(f"{tmpnodes[x].name}<{tmpnodes[x].nid}>")
            edgeitem = Edge(tmpnodes[x], tmpnodes[y], linetype = lt, linePX = PX)
            self.addItem(edgeitem)
            self.addEdge(tmpnodes[x], tmpnodes[y], edgeitem)
        # 检查边是否有相交
        # for item in self.items():
        #     if isinstance(item, Node) and not item.type:
        #         tmplist = self.ASinfo[item.id]
        #         list_len = len(tmplist)
        #         for i in range(list_len):
        #             for j in range(i+1,list_len):
        #                 x = tmplist[i]
        #                 y = tmplist[j]
        #                 if x.type and y.type and self.nextedges.get(x.id, None) and \
        #                     self.nextedges.get(y.id, None):
        #                     for (nodex, edgex) in self.nextedges[x.id]:
        #                         for (nodey, edgey) in self.nextedges[y.id]:
        #                             if self.line_intersect(x.scenePos(),nodex.scenePos(),
        #                                 y.scenePos(),nodey.scenePos()):
        #                                 # print('swap', x.nid, y.nid)
        #                                 posx = x.scenePos()
        #                                 posy = y.scenePos()
        #                                 x.setPos(posy)
        #                                 y.setPos(posx)
        #         for node in tmplist:
        #             if node.type and self.nextedges.get(node.id, None):
        #                 for (nextnode, edge) in self.nextedges[node.id]:
        #                     edge.updateEdge()
        # 显示标签
        if self.parent().labelenable:
            for item in self.items():
                if isinstance(item, Node) or isinstance(item, Edge):
                    item.label.show()

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
            tmpedge = Edge(nodes[i*2+1], nodes[j*2+1], linetype=qrand()%2)
            self.addItem(tmpedge)
            self.addEdge(nodes[i*2+1], nodes[j*2+1], tmpedge)

    def saveTopo(self, path):
        ''' docstring: 存储拓扑图 '''
        with open(path, 'r') as f:
            self.data = load(f)
        # 删除所有还在waitlist中的点，视为添加失败
        for item in self.waitlist:
            self.removeItem(item)
        self.topo = {}
        # 添加点
        tmpnodes = []
        tmpnodemap = {}
        num = 0
        for item in self.items():
            if isinstance(item, Node):
                node = {}
                node['type'] = item.type
                if item.type == 0:
                    node['name'] = item.name
                    node['size'] = item.size
                elif item.type == 1:
                    node['name'] = item.name
                    node['nid'] = item.nid
                elif item.type in range(2,4):
                    node['nid'] = item.nid
                elif item.type == 4:
                    pass
                else:
                    node['name'] = item.name
                    node['nid'] = item.nid
                pos = item.scenePos()
                node['pos'] = [pos.x(), pos.y()]
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
                px = ""
                if item.PX:
                    px = item.PX
                tmpedges.append([x, y, px])
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
