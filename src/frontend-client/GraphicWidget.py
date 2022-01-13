# coding=utf-8
''' docstring: scene/view模型框架 '''

from math import floor
from GraphicsItem import Node, Edge, Text
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtGui import QColor, QStandardItemModel
from PyQt5.QtCore import (QEasingCurve, QPointF, QPropertyAnimation, QSequentialAnimationGroup, qsrand,
    qrand, QTime, pyqtSignal, QObject, Qt, QModelIndex, pyqtProperty)

from topoGraphView import topoGraphView
from topoGraphScene import topoGraphScene


class GraphicWidget(QWidget):
    ''' docstring: 拓扑图窗口类 '''

    def __init__(self, parent=None):
        super().__init__(parent)
        qsrand(QTime(0, 0, 0).secsTo(QTime.currentTime()))
        self.scene = topoGraphScene(self)
        self.view = topoGraphView(self.scene, self)
        self.signal_to_mainwindow = None
        self.addedgetype = 0
        self.addedgeenable = False
        self.findpathenable = False
        self.labelenable = True
        self.throughputenable = False
        self.chooseASenable = False
        self.chooseItem = None # 记录当前鼠标点击物体
        self.poslist = None

        # 设置属性，允许拖放
        self.setAcceptDrops(True)
        self.view.setAcceptDrops(True)
        # 接管view视图中所有拖放事件
        self.view.dragEnterEvent = self.dragEnterEvent
        self.view.dragMoveEvent = self.dragMoveEvent
        self.view.dragLeaveEvent = self.dragLeaveEvent
        self.view.dropEvent = self.dropEvent
        # 设置垂直布局方式
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)
        # 设置动画
        self._handle_factor = 0 # 动画移动参数
        self.loop_num = 0 # 循环次数
        self.animation = QPropertyAnimation(self, b"handle_factor", self)
        self.animation.setEndValue(0)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.finished.connect(self.setnowpos)

    def setnowpos(self):
        ''' docstring: 循环次数减一，为0时结束 '''
        self.loop_num -= 1
        if not self.loop_num:
            self.poslist = None
            self.scene.node_file.hide()
        else:
            self.animation.start()

    @pyqtProperty(float)
    def handle_factor(self):
        ''' docstring: 参数获取函数 '''
        return self._handle_factor
    
    @handle_factor.setter
    def handle_factor(self, nowfactor):
        ''' docstring: 参数修改函数 '''
        self._handle_factor = nowfactor
        # 修改参数时，重新计算点坐标位置
        if self.poslist:
            num = len(self.poslist)
            i = num-1-floor(nowfactor)
            p1 = self.poslist[i-1]
            p2 = self.poslist[i]
            f = nowfactor - floor(nowfactor)
            p0 = QPointF(p1.x()*f+p2.x()*(1-f),p1.y()*f+p2.y()*(1-f))
            self.scene.node_file.setPos(p0)

    def dragEnterEvent(self, event):
        ''' docstring: 拖动进入事件 '''
        if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'):
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        ''' docstring: 拖动移动事件 '''
        if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'):
            event.accept()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        ''' docstring: 拖动离开事件 '''
        pass

    def dropEvent(self, event):
        ''' docstring: 拖动放事件 '''
        if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'):
            data = event.mimeData()
            source_item = QStandardItemModel()
            source_item.dropMimeData(data, Qt.CopyAction, 0, 0, QModelIndex())
            nodename = source_item.item(0, 0).text()
            # 根据名字生成所需节点
            if nodename == 'AS':
                num = len(self.scene.ASinfo)
                node = Node(nodetype=0, nodename='AS'+str(num + 1))
                self.scene.belongAS[node.id] = node
                self.scene.ASinfo[node.id] = [node]
            elif nodename == 'RM':
                node = Node(nodetype=1)
            elif nodename == 'BR':
                node = Node(nodetype=2)
            elif nodename == 'router':
                node = Node(nodetype=3)
            elif nodename == 'switch':
                node = Node(nodetype=4)
            elif nodename == 'PC':
                if self.scene.node_me:
                    return
                node = Node(nodetype=5, nodename='Me')
                self.node_me = node
            pos = self.view.mapToScene(event.pos())
            item = self.view.getItemAtClick(event)
            if isinstance(item, Text):
                if item.parent:
                    item = item.parent
            if item and not item.myType:
                # print(item.myType, item.name)
                self.scene.belongAS[node.id] = item
                self.scene.ASinfo[item.id].append(node)
                item.modifyCount(1)
            elif node.myType:
                self.scene.waitlist.append(node)
            self.scene.addItem(node)
            node.setPos(pos)
            if self.labelenable:
                node.label.show()
            else:
                node.label.hide()

    def setBackground(self, colorstr):
        ''' docstring: 修改拓扑背景颜色以适配风格修改 '''
        self.view._color_background = QColor(colorstr)
        self.view.setBackgroundBrush(self.view._color_background)

    def setNid(self, nid):
        ''' docstring: 设置观察节点nid，由主程序登录后调用 '''
        self.scene.nid_me = nid

    def modifyItem(self, itemname=None, itemnid=None, itemas=None):
        ''' docstring: 修改item一般属性 '''
        if not self.chooseItem:
            return
        if isinstance(self.chooseItem, Node):
            if itemname:
                self.chooseItem.updateLabel(name=itemname)
            if itemnid:
                self.chooseItem.updateLabel(nid=itemnid)
            if itemas and self.chooseItem in self.scene.waitlist:
                l = itemas.find('(')
                r = itemas.find(')')
                if l<0 or r<0 or l+1>=r:
                    return
                itemas = int(itemas[l+1:r])
                # print(itemas)
                if not self.scene.belongAS.get(itemas, None):
                    return
                chooseAS = self.scene.belongAS[itemas]
                chooseAS.modifyCount(1)
                self.scene.belongAS[self.chooseItem.id]=chooseAS
                self.scene.ASinfo[itemas].append(self.chooseItem)
                self.scene.waitlist.remove(self.chooseItem)
        elif isinstance(self.chooseItem, Edge):
            if itemnid and self.chooseItem in self.scene.waitlist:
                pos = itemnid.rfind(':')
                itemnid = itemnid[pos+1:]
                self.chooseItem.updateLabel(linePX=itemnid)
                self.scene.waitlist.remove(self.chooseItem)
                if self.labelenable:
                    self.chooseItem.label.show()
                else:
                    self.chooseItem.label.hide()

    def startChooseAS(self, tmplist):
        ''' docstring: 开启选择AS模式 '''
        # 先尝试载入已有选择
        try:
            tmpASlist = list(map(int,tmplist.split(',')))
            # print(tmpASlist)
        except ValueError:
            pass
        self.chooseASenable = True
        for item in self.scene.items():
            if isinstance(item, Node) and item.myType: # 将无关节点隐藏
                item.hide()
            if isinstance(item, Node) and not item.myType:
                num = item.name
                pos = len(num)-1
                while pos>=0 and num[pos].isdigit():
                    pos -= 1
                num = num[pos+1:] # 从名字里截取AS号
                if num in tmplist:
                    item.addClickTimes()
                item.setFlag(item.ItemIsMovable, False)
        if self.scene.node_me:
            self.scene.node_me.show()
            self.scene.node_me.setFlag(self.scene.node_me.ItemIsMovable, False)

    def endChooseAS(self):
        ''' docstring: 结束AS选择模式 '''
        self.chooseASenable = False
        if self.scene.node_me:
            self.scene.node_me.setFlag(self.scene.node_me.ItemIsMovable, True)
        tmpASlist = []
        for item in self.scene.items():
            if isinstance(item, Node) and item.myType:
                item.show()
            if isinstance(item, Node) and not item.myType:
                item.setFlag(item.ItemIsMovable, True)
            if isinstance(item, Node) and not item.myType and (item.clicktime & 1):
                num = item.name
                pos = len(num)-1
                while pos>=0 and num[pos].isdigit():
                    pos -= 1
                num = num[pos+1:]
                tmpASlist.append(int(num))
            if isinstance(item, Node) and not item.myType:
                item.clicktime = 0
                item.setSelected(False)
        tmpASlist.sort()
        return ",".join(list(map(str, tmpASlist))) # 最后返回所选结果字符串

    def setMatchedPIDs(self, PIDs, flag=True, pkttype=0, size=0):
        ''' docstring: 显示一次PID匹配 '''
        if self.poslist or not self.scene.node_me:
            # 匹配过快或node_me没有设置
            return False
        num = PIDs.count('<')
        if not num:
            return False
        # print(PIDs, num)
        tmpnode = [None]*num*2
        # poslist生成基于PID从后往前有序，否则可能出错
        for item in self.scene.items():
            item.setSelected(False)
            if isinstance(item, Edge) and item.PX and ('<' + item.PX ) in PIDs: # 记录匹配边的两端节点
                item.setSelected(flag)
                fr = PIDs.find('<'+item.PX)
                id = PIDs[:fr+1].count('<')
                # print(id)
                tmpnode[id*2-2] = item.node1
                tmpnode[id*2-1] = item.node2
        for node in tmpnode:
            if not node: # 端节点不存在，匹配失败
                return False
            self.scene.belongAS[node.id].setSelected(flag)
        lastnode = self.scene.belongAS[self.scene.node_me.id].id # 最后一个节点
        # print(lastnode)
        for i in range(num):
            j = (num-1-i)*2
            # print(self.scene.belongAS[tmpnode[j].id].id,
            #     self.scene.belongAS[tmpnode[j+1].id].id)
            if self.scene.belongAS[tmpnode[j+1].id].id != lastnode:
                # 通过与当前列表中最后一个点比较，判断这条边上点的顺序
                tmpnode[j], tmpnode[j+1] = tmpnode[j+1], tmpnode[j]
            if self.scene.belongAS[tmpnode[j+1].id].id != lastnode:
                # 路径顺序与拓扑图不符
                return False
            lastnode = self.scene.belongAS[tmpnode[j].id].id
        poslist = [] # 获取节点位置序列
        for i, node in enumerate(tmpnode):
            if not i or node.id != tmpnode[i-1].id:
                poslist.append(node.scenePos())
        poslist.append(self.scene.node_me.scenePos())
        self.showAnimation(poslist)
        ASnode = self.scene.belongAS[tmpnode[0].id]
        if pkttype:
            ASnode.updateLabel(datasize=size)
        else:
            ASnode.updateLabel(getsize=size)
        return True

    def showAnimation(self, poslist):
        ''' docstring: 显示收包动画 '''
        if self.poslist:
            return
        self.poslist = poslist.copy()
        self.scene.node_file.setPos(poslist[0])
        self.scene.node_file.show()
        num = len(poslist)
        self.animation.setStartValue(num-1)
        self.animation.setDuration(min(num*1000, 4000))
        self.loop_num = 2
        self.animation.start()

    def getASid(self, PIDs, Type, size):
        ''' docstring: 获取所对应PIDs序列末端节点所属AS号，顺便存储各AS收发包参数 '''
        # TODO: 可以和上面匹配过程合并起来并保存，这样每条路径只需要匹配一遍
        posl = PIDs.find('<')
        posr = PIDs.find('>')
        lastPID = PIDs[posl:posr]
        target = None
        tmpAS = {}
        # 做法比较蠢，统计了一遍匹配边端点出现次数，出现一次的非观察节点就是答案
        for item in self.scene.items():
            if isinstance(item, Edge) and ('<' + item.PX ) in lastPID:
                target = item
            if isinstance(item, Edge) and ('<' + item.PX ) in PIDs:
                if not tmpAS.get(self.scene.belongAS[item.node1.id].name, None):
                    tmpAS[self.scene.belongAS[item.node1.id].name] = 0
                tmpAS[self.scene.belongAS[item.node1.id].name] += 1
                if not tmpAS.get(self.scene.belongAS[item.node2.id].name, None):
                    tmpAS[self.scene.belongAS[item.node2.id].name] = 0
                tmpAS[self.scene.belongAS[item.node2.id].name] += 1
        if not target:
            return None
        else:
            ans = None
            n1 = self.scene.belongAS[target.node1.id].name
            n2 = self.scene.belongAS[target.node2.id].name
            if tmpAS[n1] < tmpAS[n2]:
                ans = self.scene.belongAS[target.node1.id]
            elif tmpAS[n1] > tmpAS[n2]:
                ans = self.scene.belongAS[target.node2.id]
            else:
                if not self.scene.node_me:
                    ans = None
                n0 = self.scene.belongAS[self.scene.node_me.id].name
                if n0 == n1:
                    ans = self.scene.belongAS[target.node2.id]
                else:
                    ans = self.scene.belongAS[target.node1.id]
            if ans:
                if Type:
                    ans.updateLabel(datasize=size)
                else:
                    ans.updateLabel(getsize=size)
                return ans.name
            else:
                return None

    def setMessageSignal(self, signal):
        ''' docstring: 设置信号向主窗体直接连接 '''
        self.signal_to_mainwindow = signal
        self.view.signal_to_mainwindow = signal
        self.scene.signal_to_mainwindow = signal

    def resizeEvent(self, a0):
        self.signal_to_mainwindow.emit(2, "信息显示框")
        return super().resizeEvent(a0)

    def showThroughput(self, flag):
        self.throughputenable = self.throughputenable ^ 1
        for item in self.scene.items():
            if isinstance(item, Node) and not item.myType and \
                item.id != self.scene.belongAS[self.scene.node_me.id].id:
                if self.throughputenable:
                    item.throughputlabel.show()
                else:
                    item.throughputlabel.hide()
