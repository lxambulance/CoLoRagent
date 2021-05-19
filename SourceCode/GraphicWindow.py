# coding=utf-8
''' docstring: scene/view模型框架 '''

from NodeEdge import Node, Edge
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtGui import QColor, QStandardItemModel
from PyQt5.QtCore import qsrand, qrand, QTime, pyqtSignal, QObject, Qt, QModelIndex

from topoGraphView import topoGraphView
from topoGraphScene import topoGraphScene


class GraphicMessage(QObject):
    ''' docstring: 拓扑图专用信号返回 '''
    choosenid = pyqtSignal(str)
    chooseitem = pyqtSignal(str, str, str)


class GraphicWindow(QWidget):
    ''' docstring: 拓扑图窗口类 '''

    def __init__(self, parent=None):
        super().__init__(parent)
        qsrand(QTime(0, 0, 0).secsTo(QTime.currentTime()))
        self.signal_ret = GraphicMessage()
        self.scene = topoGraphScene(self)
        self.view = topoGraphView(self.scene, self)
        self.addedgetype = 0
        self.addedgeenable = False
        self.accessrouterenable = False
        self.findpathenable = False
        self.labelenable = True
        self.chooseASenable = False
        self.chooseItem = None

        # 设置最小大小
        # self.setMinimumSize(400, 400)
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

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'):
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'):
            event.accept()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        pass

    def dropEvent(self, event):
        if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'):
            data = event.mimeData()
            source_item = QStandardItemModel()
            source_item.dropMimeData(data, Qt.CopyAction, 0, 0, QModelIndex())
            nodename = source_item.item(0, 0).text()
            # print(nodename)
            if nodename == 'cloud':
                num = 0
                for item in self.scene.items():
                    if isinstance(item, Node) and not item.type:
                        num += 1
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
                node = Node(nodetype=5)
            if node.type:
                self.scene.waitlist.append(node)
            self.scene.addItem(node)
            pos = self.view.mapToScene(event.pos())
            node.setPos(pos)
            if self.labelenable:
                node.label.show()
            else:
                node.label.hide()

    def loadTopo(self, path):
        self.scene.initTopo_config(path)
        self.view.scaleView(0.5)
        # if self.scene.node_me:
        #     print(self.scene.node_me.nid)

    def saveTopo(self, path):
        self.scene.saveTopo(path)

    def setBackground(self, colorstr):
        ''' docstring: 修改拓扑背景颜色以适配风格修改 '''
        self.view._color_background = QColor(colorstr)
        self.view.setBackgroundBrush(self.view._color_background)

    def setNid(self, nid):
        self.scene.nid_me = nid

    def modifyItem(self, itemname=None, itemnid=None, itemas=None):
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
        try:
            tmpASlist = list(map(int,tmplist.split(',')))
        except ValueError:
            pass
        self.chooseASenable = True
        for item in self.scene.items():
            if isinstance(item, Node) and item.type:
                item.hide()
            if isinstance(item, Node) and not item.type:
                num = item.name
                pos = len(num)-1
                while pos>=0 and num[pos].isdigit():
                    pos -= 1
                num = num[pos+1:]
                if num in tmplist:
                    item.addClickTimes()
        if self.scene.node_me:
            self.scene.node_me.show()

    def endChooseAS(self):
        self.chooseASenable = False
        tmpASlist = None
        for item in self.scene.items():
            if isinstance(item, Node) and item.type:
                item.show()
            if isinstance(item, Node) and not item.type and (item.clicktime & 1):
                num = item.name
                pos = len(num)-1
                while pos>=0 and num[pos].isdigit():
                    pos -= 1
                num = num[pos+1:]
                if not tmpASlist:
                    tmpASlist = num
                else:
                    tmpASlist = num + ',' + tmpASlist
            if isinstance(item, Node) and not item.type:
                item.clicktime = 0
                item.setSelected(False)
        return tmpASlist

    def setMatchedPIDs(self, PIDs):
        tmpnode = []
        for item in self.scene.items():
            item.setSelected(False)
            if isinstance(item, Edge) and item.type and ('<' + item.PX ) in PIDs:
                item.setSelected(True)
                tmpnode.append(item.node1)
                tmpnode.append(item.node2)
        for node in tmpnode:
            self.scene.belongAS[node.id].setSelected(True)
        # TODO：匹配错误返回False
        return True

    def getASid(self, PIDs):
        posl = PIDs.rfind('<')
        posr = PIDs.rfind('>')
        lastPID = PIDs[posl:posr]
        target = None
        tmpAS = {}
        for item in self.scene.items():
            if isinstance(item, Edge) and item.type and ('<' + item.PX ) in lastPID:
                target = item
            if isinstance(item, Edge) and item.type and ('<' + item.PX ) in PIDs:
                if not tmpAS.get(self.scene.belongAS[item.node1.id].name, None):
                    tmpAS[self.scene.belongAS[item.node1.id].name] = 0
                tmpAS[self.scene.belongAS[item.node1.id].name] += 1
                if not tmpAS.get(self.scene.belongAS[item.node2.id].name, None):
                    tmpAS[self.scene.belongAS[item.node2.id].name] = 0
                tmpAS[self.scene.belongAS[item.node2.id].name] += 1
        if not target:
            return None
        else:
            n1 = self.scene.belongAS[target.node1.id].name
            n2 = self.scene.belongAS[target.node2.id].name
            if tmpAS[n1] < tmpAS[n2]:
                return n1
            elif tmpAS[n1] > tmpAS[n2]:
                return n2
            else:
                if not self.scene.node_me:
                    return None
                n0 = self.scene.belongAS[self.scene.node_me.id].name
                if n0 == n1:
                    return n2
                else:
                    return n1


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    window = GraphicWindow()
    window.scene.initTopo_config("D:/CodeHub/CoLoRagent/data.db")
    window.show()
    sys.exit(app.exec_())
