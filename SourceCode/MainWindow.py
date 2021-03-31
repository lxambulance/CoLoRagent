# coding=utf-8
''' docstring: CoLoR Pan主页 '''

# 添加文件路径../
import os, sys, math
__BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
sys.path.append(__BASE_DIR)
HOME_DIR = __BASE_DIR + '/.tmp'
DATA_DIR = __BASE_DIR + '/data.db'

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from mainPage import Ui_MainWindow

from AddItemWindow import AddItemWindow
from serviceList import serviceListModel
from serviceTable import serviceTableModel, progressBarDelegate

import FileData
from worker import worker

from ProxyLib import (
    Sha1Hash, AddCacheSidUnit, DeleteCacheSidUnit,
    SidAnn, Get, CacheSidUnits
)
# TODO: 在Get中写入Nid
import ProxyLib as PL

class MainWindow(QMainWindow, Ui_MainWindow):
    ''' docstring: class MainWindow '''

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.nid = f"{PL.Nid:032x}"

        # 添加右键菜单
        self.listView.addAction(self.action_reg)
        self.tableView.addAction(self.action_reg)
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
        self.button_openfolder = QAction(QIcon(":/icon/openFolder"), "打开", self)
        self.button_openfolder.setStatusTip("打开文件夹")
        self.toolBar.addAction(self.button_openfolder)
        self.button_addfile = QAction(QIcon(":/icon/addFile"), "添加", self)
        self.button_addfile.setStatusTip("添加文件")
        self.toolBar.addAction(self.button_addfile)

        # 设置选中条目
        self.selectItems = []

        # 使用自定义模型
        self.fd = FileData.FileData(nid = self.nid)
        try:
            self.fd.load()
        except:
            pass
        self.listmodel = serviceListModel(self.fd)
        self.tablemodel = serviceTableModel(self.fd)
        self.progressbardelegate = progressBarDelegate(self)
        self.progressbarpool = {}

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
        # self.graphics.loadTopo(DATA_DIR) # 载入拓扑图
        self.graphics.initTopo_old() # 人工设置拓扑图

        # 设置listview(0)与tableview(1)的视图转换
        self.switchlistortable = 1
        self.listView.hide()
        self.splitter_horizon.setSizes([400,400,400])
        self.splitter_vertical.setSizes([400,800])

        # 设置线程池
        self.threadpool = QThreadPool()

        # 尝试新建文件仓库
        if not os.path.exists(HOME_DIR):
            os.mkdir(HOME_DIR)

        # 设置tab选项卡只读显示
        self.textEdit.setReadOnly(True)

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
        self.action_undoReg.triggered.connect(self.undoRegItem)
        self.action_openDir.triggered.connect(self.openFolder)
        self.action_hub.triggered.connect(self.openHub)
        self.action_import.triggered.connect(self.importData)
        self.action_swi.triggered.connect(self.switchView)
        self.action_reset.triggered.connect(self.resetView)

        self.button_swi.triggered.connect(self.switchView)
        self.button_openfolder.triggered.connect(self.openFolder)
        self.button_addfile.triggered.connect(self.addItem)

    def setSelectItem(self, items):
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
            # 计算hash值
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
            additemworker = worker(0, self.addItem_multi, nowitems)
            additemworker.signals.finished.connect(lambda:self.modelViewUpdate())
            self.threadpool.start(additemworker)
    
    def addItem_multi(self, items):
        for item_str in items:
            if os.path.isfile(item_str):
                item = item_str.replace('\\', '/')
                pos = item.rfind('/')
                item_hash = self.nid + Sha1Hash(item_str)
                self.fd.setItem(filename = item[pos+1:], filepath = item, filehash = item_hash)
            elif os.path.isdir(item_str):
                # TODO: 支持文件夹
                pass

    def calcHashRet(self, row):
        ''' docstring: 这是一个返回函数的函数 '''
        def result(s):
            s = self.nid + s
            # print(s)
            self.fd.setData(row, 2, s)
            a = self.tablemodel.createIndex(row, 2)
            self.tablemodel.dataChanged.emit(a,a)
        return result

    def delItem(self):
        ''' docstring: 删除选中条目 '''
        if len(self.selectItems) == 0:
            self.showStatus('未选中任何条目')
        else:
            nowSelectItems = self.selectItems.copy()
            delitemworker = worker(0, self.delItem_multi, nowSelectItems)
            delitemworker.signals.finished.connect(lambda:self.modelViewUpdate())
            delitemworker.signals.finished.connect(lambda:self.showStatus('条目已删除'))
            self.threadpool.start(delitemworker)
    
    def delItem_multi(self, items):
        items.sort(reverse = True)
        # print(items)
        for item in items:
            self.fd.removeItem(item)

    def dowItem(self):
        ''' docstring: 从远端下载数据 '''
        if len(self.selectItems) == 0:
            self.showStatus('未选中任何条目')
        else:
            nowSelectItems = self.selectItems.copy()
            dowitemworker = worker(1, self.dowItem_multi, nowSelectItems)
            for item in nowSelectItems:
                dowitemworker.signals.progress.connect(self.updateProgress(item, 4))
            dowitemworker.signals.finished.connect(lambda:self.showStatus('条目已下载'))
            self.threadpool.start(dowitemworker)
    
    def dowItem_multi(self, items, progress_callback):
        total = len(items)
        now = 0
        for item in items:
            now += 1
            isDow = self.fd.getData(item, 4)
            if isDow:
                continue
            SID = self.fd.getData(item, 2)
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
                regitemworker.signals.progress.connect(self.updateProgress(item, 3))
            regitemworker.signals.finished.connect(lambda:self.showStatus('条目已通告'))
            self.threadpool.start(regitemworker)

    def regItem_multi(self, items, progress_callback):
        total = len(items)
        now = 0
        for item in items:
            now += 1
            isReg = self.fd.getData(item, 3)
            if isReg:
                continue
            filepath = self.fd.getData(item, 1)
            AddCacheSidUnit(filepath, 1, 0, 0, 0)
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
                undoregworker.signals.progress.connect(self.updateProgress(item, 3))
            undoregworker.signals.finished.connect(lambda:self.showStatus('条目已取消通告'))
            self.threadpool.start(undoregworker)
    
    def undoRegItem_multi(self, items, progress_callback):
        total = len(items)
        now = total
        for item in items:
            now -= 1
            isReg = self.fd.getData(item, 3)
            if not isReg:
                continue
            filepath = self.fd.getData(item, 1)
            AddCacheSidUnit(filepath, 3, 0, 0, 0)
            progress_callback.emit(round(now*20/total + 80))
        SidAnn()
        progress_callback.emit(0)

    def updateProgress(self, row, column):
        def main(value):
            self.fd.setData(row, column, value)
            a = self.tablemodel.createIndex(row, column)
            self.tablemodel.dataChanged.emit(a,a)
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
        self.splitter_horizon.setSizes([400,400,400])
        self.splitter_vertical.setSizes([400,800])

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
        filepath = tmp[:tmp.rfind('/')]
        openfolderworker = worker(0, os.startfile, filepath)
        openfolderworker.signals.finished.connect(lambda:self.showStatus('文件已打开'))
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
            self.graphics.saveTopo(DATA_DIR)
            event.accept()
        elif reply == QMessageBox.No:
            event.accept()
        else:
            event.ignore()

    def viewInfo(self, index):
        ''' docstring: 双击条目显示文件内容 '''
        filepath = self.fd.getData(index.row(), 1)
        if not os.path.exists(filepath):
            self.showStatus('文件不存在')
            return
        with open(filepath, 'r', encoding='utf-8') as f:
            tmp = f.read(500)
        filename = self.fd.getData(index.row(), 0)
        self.textEdit.append('click file:' + filename + ' content:\n' + tmp + '\n--------------------')

if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
