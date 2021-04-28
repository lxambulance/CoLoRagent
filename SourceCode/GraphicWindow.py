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
        self.labelenable = False
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
                node = Node(nodetype=0)
                self.scene.belongAS[node.nid] = node
                self.scene.ASinfo[node.nid] = [node]
            elif nodename == 'RM':
                node = Node(nodetype=1)
                self.scene.waitlist.append(node)
            elif nodename == 'BR':
                node = Node(nodetype=2)
                self.scene.waitlist.append(node)
            elif nodename == 'router':
                node = Node(nodetype=3)
                self.scene.waitlist.append(node)
            elif nodename == 'switch':
                node = Node(nodetype=4)
            elif nodename == 'PC':
                node = Node(nodetype=5)
                self.scene.waitlist.append(node)
            self.scene.addItem(node)
            if self.labelenable:
                node.label.show()
            else:
                node.label.hide()

    def loadTopo(self, path):
        self.scene.initTopo_config(path)
        self.view.scaleView(0.35)

    def saveTopo(self, path):
        self.scene.saveTopo(path)

    def setBackground(self, colorstr):
        ''' docstring: 修改拓扑背景颜色以适配风格修改 '''
        self.view._color_background = QColor(colorstr)
        self.view.setBackgroundBrush(self.view._color_background)

    def setNid(self, nid):
        self.scene.nid_me = nid

    def modifyItem(self, *, itemname=None, itemnid=None, itemas=None):
        if not self.chooseItem:
            return
        if isinstance(self.chooseItem, Node):
            if itemname:
                self.chooseItem.name = itemname
                self.chooseItem.updateLabel(name=itemname)
            if itemnid and self.chooseItem in self.scene.waitlist:
                self.chooseItem.updateLabel(nid=itemnid)
                self.scene.waitlist.remove(self.chooseItem)
            if itemas and not self.chooseItem in self.scene.waitlist \
                    and not self.scene.belongAS.get(self.chooseItem.nid, None):
                l = itemas.find('<')
                r = itemas.find('>')
                if l<0 or r<0 or l+1>=r or r-l-1 != 32:
                    return
                itemas = itemas[l+1:r]
                chooseAS = self.scene.belongAS[itemas]
                self.scene.belongAS[self.chooseItem.nid]=chooseAS
                self.scene.ASinfo[itemas].append(self.chooseItem)
        elif isinstance(self.chooseItem, Edge):
            if itemnid and self.chooseItem in self.scene.waitlist:
                pos = itemnid.rfind(':')
                itemnid = itemnid[pos+1:]
                self.chooseItem.updateLabel(linePX=itemnid)
                self.scene.waitlist.remove(self.chooseItem)


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    window = GraphicWindow()
    window.scene.initTopo_config("D:/CodeHub/CoLoRagent/data.db")
    window.show()
    sys.exit(app.exec_())
