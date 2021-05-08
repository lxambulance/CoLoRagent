# coding=utf-8
''' docstring: CoLoR Pan主页 '''

# 添加文件路径../
import time
import json
import ProxyLib as PL
from ProxyLib import (
    Sha1Hash, AddCacheSidUnit, DeleteCacheSidUnit,
    SidAnn, Get, CacheSidUnits
)
from worker import worker
import FileData
from serviceTable import serviceTableModel, progressBarDelegate
from serviceList import serviceListModel
from AddItemWindow import AddItemWindow
from mainPage import Ui_MainWindow
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, QThreadPool, qrand, QTimer
from PyQt5.QtWidgets import (QApplication, QMainWindow, QAction, 
    QMessageBox, QStyleFactory, QTreeWidgetItem)
import os
import sys
import math
import time

__BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))).replace('\\', '/')
sys.path.append(__BASE_DIR)
HOME_DIR = __BASE_DIR + '/.tmp'
DATA_DIR = __BASE_DIR + '/data.db'
starttime = time.strftime("%y-%m-%d_%H_%M_%S", time.localtime())
LOG_DIR = __BASE_DIR + f'/{starttime}.log'


class MainWindow(QMainWindow, Ui_MainWindow):
    ''' docstring: class MainWindow '''

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # 用于统计频率
        self.time = QTimer()
        self.time.setInterval(5000)
        self.asmetrics = {} # id:[(get num, get total size),(data num, data total size)]

        # 用于收包显示的变量
        self.mapfromSIDtoItem = {}
        self.datapackets = []

        # TODO: 在Get中写入Nid？
        self.nid = f"{PL.Nid:032x}"
        self.graphics_global.setNid(self.nid)

        # 添加右键菜单
        self.listView.addAction(self.action_reg)
        self.tableView.addAction(self.action_reg)
        self.listView.addAction(self.action_advancedreg)
        self.tableView.addAction(self.action_advancedreg)
        self.listView.addAction(self.action_undoReg)
        self.tableView.addAction(self.action_undoReg)
        self.listView.addAction(self.action_dow)
        self.tableView.addAction(self.action_dow)
        self.listView.addAction(self.action_del)
        self.tableView.addAction(self.action_del)
        self.listView.addAction(self.action_openDir)
        self.tableView.addAction(self.action_openDir)

        # 添加toolbar按钮
        self.button_swi = QAction(QIcon(":/icon/switchView"), "切换", self)
        self.button_swi.setStatusTip("视图切换")
        self.toolBar.addAction(self.button_swi)
        self.button_openfolder = QAction(
            QIcon(":/icon/openFolder"), "打开", self)
        self.button_openfolder.setStatusTip("打开文件夹")
        self.toolBar.addAction(self.button_openfolder)
        self.button_addfile = QAction(QIcon(":/icon/addFile"), "添加", self)
        self.button_addfile.setStatusTip("添加文件")
        self.toolBar.addAction(self.button_addfile)

        # 设置选中条目
        self.selectItems = []

        # 使用自定义模型
        self.fd = FileData.FileData(nid=self.nid)
        try:
            self.fd.load()
        except:
            pass
        self.listmodel = serviceListModel(self.fd)
        self.tablemodel = serviceTableModel(self.fd)
        self.progressbardelegate = progressBarDelegate(self)
        self.progressbarpool = {}

        # 设置tab control页
        for i in range(self.fd.rowCount()):
            self.chooseFile.addItem(self.fd.getData(i))
        self.chooseFile.setCurrentIndex(-1)

        # 设置模型对应的view
        self.listView.setModel(self.listmodel)
        self.listView.setViewMode(self.listView.IconMode)
        self.listView.setResizeMode(self.listView.Adjust)
        self.listView.setIconSize(QSize(64, 64))
        self.listView.setGridSize(QSize(80, 80))
        self.tableView.setModel(self.tablemodel)
        self.tableView.setItemDelegate(self.progressbardelegate)
        self.tableView.setSortingEnabled(True)
        self.tableView.setColumnWidth(0, 100)
        self.tableView.setColumnWidth(1, 250)
        self.tableView.setColumnWidth(2, 530)
        self.tableView.setColumnWidth(3, 100)
        self.tableView.setColumnWidth(4, 100)

        # 设置禁止自添加
        self.addNodes.setAcceptDrops(False)
        # TODO: 暂时隐藏搜索功能
        self.search_label.hide()
        self.searchItem.hide()
        self.itemlist_label.hide()
        self.itemlist.hide()

        # 设置listview(0)与tableview(1)的视图转换
        self.switchlistortable = 0
        self.tableView.hide()
        self.splitter_horizon.setSizes([300, 300, 500])
        self.splitter_vertical.setSizes([700, 500])

        # 设置线程池 TODO: 线程池放到窗口外面
        self.threadpool = QThreadPool()

        # 尝试新建文件仓库
        if not os.path.exists(HOME_DIR):
            os.mkdir(HOME_DIR)

        # 设置信号与槽的连接
        self.tableView.signal_select.connect(self.setSelectItem)
        self.listView.signal_select.connect(self.setSelectItem)
        self.listView.signal_add.connect(self.addItems)
        self.tableView.doubleClicked.connect(self.viewInfo)
        self.listView.doubleClicked.connect(self.viewInfo)

        self.action_add.triggered.connect(self.addItem)
        self.action_del.triggered.connect(self.delItem)
        self.action_dow.triggered.connect(self.dowItem)
        self.action_reg.triggered.connect(self.regItem)
        self.action_advancedreg.triggered.connect(self.showAdvancedReg)
        self.chooseFile.currentIndexChanged[int].connect(self.showAdvancedRegArgs)
        self.setlevel.textEdited.connect(lambda x:self.changeAdvancedReg(level=x))
        self.whitelist.textEdited.connect(lambda x:self.changeAdvancedReg(whitelist=x))
        self.whitelist_button.clicked.connect(self.chooseASs)
        self.advancedReg.clicked.connect(self.advancedRegItem)
        self.action_undoReg.triggered.connect(self.undoRegItem)
        self.action_openDir.triggered.connect(self.openFolder)
        self.action_hub.triggered.connect(self.openHub)
        self.action_import.triggered.connect(self.importData)
        self.action_swi.triggered.connect(self.switchView)
        self.action_reset.triggered.connect(self.resetView)

        self.button_swi.triggered.connect(self.switchView)
        self.button_openfolder.triggered.connect(self.openFolder)
        self.button_addfile.triggered.connect(self.addItem)

        self.addLine.clicked.connect(self.setTopoEdgeEnable)

        self.graphics_global.scene.chooseRouter.connect(self.setAccessRouter)
        self.graphics_global.scene.choosePath.connect(self.setPath)
        self.chooseRouter.clicked.connect(self.setTopoRouterEnable)
        self.graphics_global.signal_ret.choosenid.connect(
            lambda s: self.accessRouter.setText(s))
        self.graphics_global.signal_ret.chooseitem.connect(self.showItem)
        self.addLine.clicked.connect(self.topoAddLine)
        self.itemnid.returnPressed.connect(
            lambda: self.graphics_global.modifyItem(itemnid=self.itemnid.text()))
        self.itemas.returnPressed.connect(
            lambda: self.graphics_global.modifyItem(itemas=self.itemas.text()))
        self.itemname.returnPressed.connect(
            lambda: self.graphics_global.modifyItem(itemname=self.itemname.text()))
        self.lineType.currentIndexChanged.connect(self.setTopoLineType)
        self.dataPktReceive.itemClicked.connect(self.showMatchedPIDs)
        self.time.timeout.connect(self.reCalc)

        # 载入拓扑图，需要相关信号绑定完成后再载入
        self.graphics_global.loadTopo(DATA_DIR)

    def chooseASs(self, flag):
        if flag:
            row = self.chooseFile.currentIndex()
            if row == -1:
                self.showStatus('请选择高级通告条目')
                self.whitelist_button.setChecked(False)
                return
            self.whitelist_button.setText('选择完毕')
            self.graphics_global.startChooseAS(self.whitelist.text())
        else:
            self.whitelist_button.setText('图中选择')
            ret = self.graphics_global.endChooseAS()
            self.whitelist.setText(ret)

    def showItem(self, name, nid, AS):
        self.itemname.setText(name)
        self.itemnid.setText(nid)
        self.itemas.setText(AS)

    def setTopoLineType(self, index):
        self.graphics_global.addedgetype = index

    def topoAddLine(self):
        self.graphics_global.addedgeenable = True
        self.graphics_global.addedgetype = self.lineType.currentIndex()

    def setAccessRouter(self, s):
        self.accessRouter.setText(s)

    def setPath(self, paths):
        print(paths)

    def getPathFromPkt(self, type, SID, paths, size, nid):
        ''' docstring: 收包显示 '''
        name = 'Unknown packet'
        for i in range(self.fd.rowCount()):
            if SID == self.fd.getData(i,2):
                name = self.fd.getData(i,0)
                break
        if type == 0x72:
            name = '<Get>' + name
        elif type == 0x73:
            name = '<Data>' + name
        else:
            name = '<Control> packet'
        item = self.mapfromSIDtoItem.get(SID, None)
        if not item:
            # 该SID下第一个包，建立顶层节点topItem
            self.datapackets.append(QTreeWidgetItem(None, [name, "0", SID]))
            self.dataPktReceive.addTopLevelItem(self.datapackets[-1])
            self.mapfromSIDtoItem[SID] = self.datapackets[-1]
            item = self.datapackets[-1]
        path_str = '-'.join(map(lambda x:f"<{x:08x}>",paths))
        if type == 0x72:
            item.addChild(QTreeWidgetItem([f"from nid {nid:032x}", str(size), "PIDs="+path_str]))
        elif type == 0x73:
            num = item.childCount()
            item.addChild(QTreeWidgetItem([f"piece<{num+1}>", str(size), "PIDs="+path_str]))
            totsize = int(item.text(1))
            item.setText(1, str(totsize+size))
        else:
            num = item.childCount()
            item.addChild(QTreeWidgetItem([f"piece<{num+1}>", str(size), ""]))

    def reCalc(self):
        ''' docstring: 重新计算统计量 '''
        self.metrics.clear()

        self.metrics.update()

    def showMatchedPIDs(self, item, column):
        ''' docstring: 选中物体，显示匹配 '''
        #print(item.text(column))
        pitem = item.parent()
        if not pitem or 'Control' in pitem.text(0):
            return
        self.graphics_global.setMatchedPIDs(item.text(2))

    def setTopoRouterEnable(self):
        self.graphics_global.accessrouterenable = True

    def setTopoEdgeEnable(self):
        self.graphics_global.addedgeenable = True

    def setSelectItem(self, items):
        ''' docstring: 通过列表和表格多选信号返回选择条目对象 '''
        if len(items) == 0:
            self.selectItems = []
        else:
            status = '选中条目'
            self.selectItems = []
            for item in items:
                self.selectItems.append(item.row())
                status += ' ' + str(item.row() + 1)
            self.showStatus(status)

    def modelViewUpdate(self):
        ''' docstring: 刷新视图 '''
        self.listmodel.layoutChanged.emit()
        self.tablemodel.layoutChanged.emit()

    def showStatus(self, s):
        self.statusBar().showMessage(s)

    def addItem(self):
        ''' docstring: 按下添加按钮 '''
        self.additemwindow = AddItemWindow(self.fd, self)
        ret = self.additemwindow.exec_()
        row = self.additemwindow.newitemrow
        needReg = self.additemwindow.needReg
        # ret 可用于后续判断返回结果
        if (ret) and (row != None):
            self.modelViewUpdate()
            self.chooseFile.addItem(self.fd.getData(row, 0))
            # 计算hash值
            if not self.fd.getData(row, 2):
                filepath = self.fd.getData(row, 1)
                hashworker = worker(0, Sha1Hash, filepath)
                # print('start calc hash: ', filepath)
                hashworker.signals.result.connect(self.calcHashRet(row))
                self.threadpool.start(hashworker)
            # 检查needReg，进行通告流程
            if needReg:
                self.selectItems = [row]
                self.regItem()

    def addItems(self, items):
        nowitems = items.copy()
        if len(nowitems):
            lastrow = self.fd.rowCount()
            for item_str in nowitems:
                if os.path.isfile(item_str):
                    item = item_str.replace('\\', '/')
                    pos = item.rfind('/')
                    self.fd.addItem(filename=item[pos+1:], filepath=item)
                    self.chooseFile.addItem(item[pos+1:])
                elif os.path.isdir(item_str):
                    # TODO: 支持文件夹
                    pass
            self.modelViewUpdate()
            nowrow = self.fd.rowCount()
            for i in range(lastrow, nowrow):
                filepath = self.fd.getData(i, 1)
                hashworker = worker(0, Sha1Hash, filepath)
                hashworker.signals.result.connect(self.calcHashRet(i))
                self.threadpool.start(hashworker)

    def calcHashRet(self, row):
        ''' docstring: 这是一个返回函数的函数 '''
        def result(s):
            s = self.nid + s
            # print(s)
            self.fd.setData(row, 2, s)
            a = self.tablemodel.createIndex(row, 2)
            self.tablemodel.dataChanged.emit(a, a)
        return result

    def delItem(self):
        ''' docstring: 删除选中条目 '''
        if len(self.selectItems) == 0:
            self.showStatus('未选中任何条目')
        else:
            nowSelectItems = self.selectItems.copy()
            delitemworker = worker(0, self.delItem_multi, nowSelectItems)
            delitemworker.signals.finished.connect(
                lambda: self.modelViewUpdate())
            delitemworker.signals.finished.connect(
                lambda: self.showStatus('条目已删除'))
            self.threadpool.start(delitemworker)

    def delItem_multi(self, items):
        items.sort(reverse=True)
        # print(items)
        if self.chooseFile.currentIndex() in items:
            self.chooseFile.setCurrentIndex(-1)
        for item in items:
            if not self.fd.getData(item, 0):
                continue
            self.fd.removeItem(item)
            self.chooseFile.removeItem(item)

    def dowItem(self):
        ''' docstring: 从远端下载数据 '''
        if len(self.selectItems) == 0:
            self.showStatus('未选中任何条目')
        else:
            nowSelectItems = self.selectItems.copy()
            dowitemworker = worker(1, self.dowItem_multi, nowSelectItems)
            for item in nowSelectItems:
                dowitemworker.signals.progress.connect(
                    self.updateProgress(item, 4))
            dowitemworker.signals.finished.connect(
                lambda: self.showStatus('条目已下载'))
            self.threadpool.start(dowitemworker)

    def dowItem_multi(self, items, progress_callback):
        total = len(items)
        now = 0
        wait_list = []
        for item in items:
            if not self.fd.getData(item, 0):
                continue
            now += 1
            isDow = self.fd.getData(item, 4)
            if isDow:
                continue
            SID = self.fd.getData(item, 2)
            wait_list.append(SID)
            filepath = self.fd.getData(item, 1)
            Get(SID, filepath)
            progress_callback.emit(round(now*100/total))
        # TODO：涉及进度条完成状态需要通过color monitor精确判断

    def regItem(self):
        ''' docstring: 通告 '''
        if len(self.selectItems) == 0:
            self.showStatus('未选中条目')
        else:
            nowSelectItem = self.selectItems.copy()
            regitemworker = worker(1, self.regItem_multi, nowSelectItem)
            for item in nowSelectItem:
                regitemworker.signals.progress.connect(
                    self.updateProgress(item, 3))
            regitemworker.signals.finished.connect(
                lambda: self.showStatus('条目已通告'))
            self.threadpool.start(regitemworker)

    def showAdvancedReg(self):
        ''' docstring: 高级通告 '''
        if len(self.selectItems) == 0:
            self.showStatus('未选中条目')
        elif len(self.selectItems) > 1:
            self.showStatus('选中要素过多')
        else:
            nowSelectItem = self.selectItems[0]
            # print("choose", nowSelectItem)
            self.tabWidget.setCurrentIndex(3)
            self.chooseFile.setCurrentIndex(nowSelectItem)
            self.showAdvancedRegArgs(nowSelectItem)
    
    def showAdvancedRegArgs(self, row):
        ''' docstring: 高级通告切换显示 '''
        level = self.fd.getData(row, 5)
        if level:
            self.setlevel.setText(level)
        else:
            self.setlevel.setText('')
        whitelist = self.fd.getData(row, 6)
        if whitelist:
            self.whitelist.setText(whitelist)
        else:
            self.whitelist.setText('')
        # print(row, level, whitelist)

    def changeAdvancedReg(self, level=None, whitelist=None):
        ''' docstring: 修改高级通告策略 '''
        nowSelectItem = self.chooseFile.currentIndex()
        if nowSelectItem<0 or nowSelectItem>=self.fd.rowCount():
            return
        newItem = self.fd.getItem(nowSelectItem)
        while len(newItem)<7:
            newItem.append(None)
        if level != None:
            newItem[5] = level
            self.fd.setItem(nowSelectItem, newItem)
        if whitelist != None:
            newItem[6] = whitelist
            self.fd.setItem(nowSelectItem, newItem)

    def advancedRegItem(self):
        nowSelectItem = self.chooseFile.currentIndex()
        if nowSelectItem<0 or nowSelectItem>=self.fd.rowCount():
            return
        filepath = self.fd.getData(nowSelectItem, 1)
        level = self.fd.getData(nowSelectItem, 5)
        whitelist = self.fd.getData(nowSelectItem, 6)
        kwargs = {}
        if level != None:
            kwargs['level'] = int(level)
        if whitelist != None:
            kwargs['WhiteList'] = list(map(int,whitelist.split(',')))
        regitemworker = worker(0, AddCacheSidUnit, filepath, 1,1,1,1, **kwargs)
        regitemworker.signals.finished.connect(lambda:self.updateProgress(nowSelectItem, 3)(100))
        regitemworker.signals.finished.connect(lambda:self.showStatus('条目已通告'))
        regitemworker.signals.finished.connect(SidAnn)
        self.threadpool.start(regitemworker)

    def regItem_multi(self, items, progress_callback):
        total = len(items)
        now = 0
        for item in items:
            if not self.fd.getData(item, 0):
                continue
            now += 1
            isReg = self.fd.getData(item, 3)
            if isReg:
                continue
            filepath = self.fd.getData(item, 1)
            AddCacheSidUnit(filepath, 1, 1, 1, 1)
            progress_callback.emit(round(now*20/total))
        SidAnn()
        progress_callback.emit(100)

    def undoRegItem(self):
        ''' docstring: 取消通告 '''
        if len(self.selectItems) == 0:
            self.showStatus('未选中条目')
        else:
            nowSelectItem = self.selectItems.copy()
            undoregworker = worker(1, self.undoRegItem_multi, nowSelectItem)
            for item in nowSelectItem:
                undoregworker.signals.progress.connect(
                    self.updateProgress(item, 3))
            undoregworker.signals.finished.connect(
                lambda: self.showStatus('条目已取消通告'))
            self.threadpool.start(undoregworker)

    def undoRegItem_multi(self, items, progress_callback):
        total = len(items)
        now = total
        for item in items:
            if not self.fd.getData(item, 0):
                continue
            now -= 1
            isReg = self.fd.getData(item, 3)
            if not isReg:
                continue
            filepath = self.fd.getData(item, 1)
            AddCacheSidUnit(filepath, 3, 1, 1, 1)
            progress_callback.emit(round(now*20/total + 80))
        SidAnn()
        progress_callback.emit(0)

    def updateProgress(self, row, column):
        def main(value):
            self.fd.setData(row, column, value)
            a = self.tablemodel.createIndex(row, column)
            self.tablemodel.dataChanged.emit(a, a)
        return main

    def switchView(self):
        ''' docstring: 切换视图按钮 '''
        self.switchlistortable ^= 1
        if self.switchlistortable:
            self.listView.hide()
            self.tableView.show()
            self.showStatus('切换到列表视图')
        else:
            self.listView.show()
            self.tableView.hide()
            self.showStatus('切换到图标视图')

    def resetView(self):
        ''' docstring: 恢复初始视图格式 '''
        if not self.toolBar.toggleViewAction().isChecked():
            self.toolBar.toggleViewAction().trigger()
        self.splitter_horizon.setSizes([300, 300, 500])
        self.splitter_vertical.setSizes([700, 500])
        if self.scaling.isChecked():
            self.scaling.setText('放大')
            self.scaling.setChecked(False)

    def openHub(self):
        ''' docstring: 打开本地仓库 '''
        openhubworker = worker(0, os.startfile, HOME_DIR)
        self.threadpool.start(openhubworker)

    def openFolder(self):
        ''' docstring: 打开所选文件所在文件夹 '''
        nowSelectItem = self.selectItems.copy()
        if len(nowSelectItem) == 0:
            self.showStatus('未选中文件')
            return
        elif len(nowSelectItem) != 1:
            self.showStatus('选中文件过多')
            return
        tmp = self.fd.getData(nowSelectItem[0], 1)
        if not os.path.exists(tmp) or not tmp:
            self.showStatus('文件不存在')
            return
        filepath = tmp[:tmp.rfind('/')]
        openfolderworker = worker(0, os.startfile, filepath)
        openfolderworker.signals.finished.connect(
            lambda: self.showStatus('文件已打开'))
        self.threadpool.start(openfolderworker)

    def importData(self):
        ''' docstring: 导入其他数据文件 '''
        fpath = QFileDialog.getOpenFileName(self, '打开文件', HOME_DIR)
        if fpath[0]:
            self.fd.load(fpath[0])
            self.modelViewUpdate()

    def closeEvent(self, event):
        ''' docstring: 关闭窗口时弹出警告 '''
        status = QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        reply = QMessageBox.question(self, '警告：是否保存数据', '保存并退出?', status)
        if reply == QMessageBox.Yes:
            # 做出保存操作
            self.fd.save()
            self.graphics_global.saveTopo(DATA_DIR)
            self.saveLog()
            event.accept()
        elif reply == QMessageBox.No:
            event.accept()
        else:
            event.ignore()

    def saveLog(self):
        with open(LOG_DIR, 'w', encoding='utf-8') as f:
            s = self.textEdit.toPlainText()
            f.write(s)

    def viewInfo(self, index):
        ''' docstring: 双击条目显示文件内容 '''
        filepath = self.fd.getData(index.row(), 1)
        filename = self.fd.getData(index.row(), 0)
        filepid = self.fd.getData(index.row(), 2)
        viewjsonworker = worker(0, self.viewJson, filename, filepath, filepid)
        viewjsonworker.signals.result.connect(self.textEdit.append)
        self.threadpool.start(viewjsonworker)

    def viewJson(self, filename, filepath, filepid):
        ret = f'double click {filename} <PID:{filepid}> = '
        if not os.path.exists(filepath):
            return ret + '本地文件不存在\n'
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                fcontent = ""
                while True:
                    tmp = f.read(512)
                    if not tmp:
                        break
                    fcontent += tmp
                    if len(fcontent) > 512 * 10:
                        return ret + '\{...(内容过长)...\}\n'
            data = json.loads(fcontent)
        except:
            return ret + '非JSON格式文件\n'
        ret += json.dumps(data, sort_keys=True, indent=4,
                          separators=(', ', ': '))
        return ret

    def handleMessageFromPkt(self, messageType, message):
        if messageType == 0:
            self.textEdit.append(message + '\n')
        elif messageType == 1:
            # 收到warning
            self.textEdit.append('[warning]' + message + '\n')
        else:
            self.showEvent('无效的后端信息')


if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    window.getPathFromPkt(0x72, '123', [0x11222695], 100, 0x12)
    window.getPathFromPkt(0x72, '123', [0x11222695,0x33446217], 1500, 0x23)
    window.getPathFromPkt(0x73, 'abc', [0x11222695,0x33446217,0x55666217], 1000, 0)
    window.getPathFromPkt(0x73, 'abc', [0x33446217,0x55666217], 100, 0)
    window.getPathFromPkt(0x74, '', [], 20, 0)

    sys.exit(app.exec_())
