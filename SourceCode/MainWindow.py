# coding=utf-8
''' docstring: CoLoR Pan主页 '''

# 添加文件路径../
import os, sys, math
__BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
sys.path.append(__BASE_DIR)
HOME_DIR = __BASE_DIR + '/.tmp'

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from mainPage import Ui_MainWindow

from CmdlineWindow import CmdlineWindow
from VideoWindow import VideoWindow
from AddItemWindow import AddItemWindow
from serviceTable import serviceTableModel, progressBarDelegate
from serviceList import serviceListModel

from PointLine import Node, Line
import FileData
from worker import worker

from ProxyLib import Sha1Hash, AddCacheSidUnit, DeleteCacheSidUnit, SidAnn, Get, CacheSidUnits

class MainWindow(QMainWindow, Ui_MainWindow):
    ''' docstring: class MainWindow '''

    def __init__(self):
        super().__init__()
        self.setupUi(self)

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
        self.selectItem = None

        # 使用自定义模型
        self.fd = FileData.FileData()
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
        self.tableView.setColumnWidth(0, 150)
        self.tableView.setColumnWidth(1, 300)
        self.tableView.setColumnWidth(2, 300)
        self.tableView.setColumnWidth(3, 120)
        self.tableView.setColumnWidth(4, 120)

        # 设置listview(0)与tableview(1)的视图转换
        self.switchlistortable = 1
        self.listView.hide()
        self.splitter.setSizes([300,300,400])

        # 设置线程池
        self.threadpool = QThreadPool()

        # 尝试新建文件仓库
        if not os.path.exists(HOME_DIR):
            os.mkdir(HOME_DIR)

        # 人工设置拓扑图
        self.node = [0] * 5
        for i in range(5):
            self.node[i] = Node()
            self.graphics.scene().addItem(self.node[i])
            a = math.pi * 2 / 5
            R = 250
            x, y = round(math.cos(a*3/4+a*i) * R), round(math.sin(a*3/4+a*i) * R)
            self.node[i].setPos(x, y)
        self.line = [0] * 5
        for i in range(5):
            j = (i + 2) % 5
            self.line[i] = Line(self.node[i],self.node[j],self.graphics)
            self.graphics.scene().addItem(self.line[i])
        # 设置缩放比例
        self.graphics.scaleView(0.7)

        # 设置信号与槽的连接
        self.tableView.signal.connect(self.setSelectItem)
        self.listView.signal.connect(self.setSelectItem)
        self.listView.doubleClicked.connect(self.doubleClickItem)
        self.tableView.doubleClicked.connect(self.doubleClickItem)

        self.action_add.triggered.connect(self.addItem)
        self.action_del.triggered.connect(self.delItem)
        self.action_dow.triggered.connect(self.dowItem)
        self.action_reg.triggered.connect(self.regItem)
        self.action_undoReg.triggered.connect(self.undoRegItem)
        self.action_openDir.triggered.connect(self.openFolder)
        self.action_cmd.triggered.connect(self.openCmdLinePage)
        self.action_video.triggered.connect(self.openVideoPage)
        self.action_hub.triggered.connect(self.openHub)
        self.action_import.triggered.connect(self.importData)
        self.action_swi.triggered.connect(self.switchView)
        self.action_reset.triggered.connect(self.resetView)

        self.button_swi.triggered.connect(self.switchView)
        self.button_openfolder.triggered.connect(self.openFolder)
        self.button_addfile.triggered.connect(self.addItem)

    def setSelectItem(self, row):
        if (row == -1):
            self.selectItem = None
            self.showStatus('')
        else:
            self.selectItem = self.tablemodel.createIndex(row, 0)
            self.showStatus('选中条目' + str(row + 1))

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
                self.selectItem = self.tablemodel.createIndex(row, 0)
                self.regItem()

    def calcHashRet(self, row):
        ''' docstring: 这是一个返回函数的函数 '''
        def result(s):
            s = str(s)
            # print(s)
            self.fd.setData(row, 2, s)
            a = self.tablemodel.createIndex(row, 2)
            self.tablemodel.dataChanged.emit(a,a)
        return result

    def delItem(self):
        ''' docstring: 删除选中条目 '''
        nowSelectItem = QModelIndex(self.selectItem)
        if nowSelectItem != None:
            self.fd.removeItem(nowSelectItem.row())
            self.modelViewUpdate()
            self.showStatus('条目' + str(nowSelectItem.row()+1) + '已删除')
            nowSelectItem = None
        else:
            self.showStatus('未选中任何条目')

    def dowItem(self):
        ''' docstring: 从远端下载数据 '''
        nowSelectItem = QModelIndex(self.selectItem)
        if nowSelectItem == None:
            self.showStatus('未选中任何条目')
            return
        isDow = self.fd.getData(nowSelectItem.row(), 4)
        if isDow:
            self.showStatus('条目已下载')
            return
        SID = self.fd.getData(nowSelectItem.row(), 2)
        filepath = self.fd.getData(nowSelectItem.row(), 1)
        downloadworker = worker(0, Get, SID, filepath)
        downloadworker.signals.finished.connect(lambda:self.fd.setData(nowSelectItem.row(), 4, 100))
        self.showStatus('文件'+str(nowSelectItem.row()+1)+'开始下载')
        self.threadpool.start(downloadworker)

    def regItem(self):
        ''' docstring: 通告 '''
        nowSelectItem = QModelIndex(self.selectItem)
        if nowSelectItem == None:
            self.showStatus('未选中条目')
            return
        isReg = self.fd.getData(nowSelectItem.row(), 3)
        if isReg:
            self.showStatus('条目'+str(nowSelectItem.row() + 1)+'已通告')
            return
        filepath = self.fd.getData(nowSelectItem.row(), 1)
        message = '条目'+str(nowSelectItem.row() + 1)+'已通告'
        
        registerworker = worker(1, self.regItem_main, filepath)
        registerworker.signals.progress.connect(self.regProgress(nowSelectItem.row()))
        registerworker.signals.finished.connect(
            lambda:self.regFinished(nowSelectItem.row(), 100, message))
        self.threadpool.start(registerworker)

    def regItem_main(self, filepath, progress_callback):
        AddCacheSidUnit(filepath, 1, 0, 0, 0)
        progress_callback.emit(20)
        SidAnn()
        progress_callback.emit(100)

    def undoRegItem(self):
        ''' docstring: 取消通告 '''
        nowSelectItem = QModelIndex(self.selectItem)
        if nowSelectItem == None:
            self.showStatus('未选中条目')
            return
        isReg = self.fd.getData(nowSelectItem.row(), 3)
        if not isReg:
            self.showStatus('条目'+str(nowSelectItem.row() + 1)+'已取消通告')
            return
        filepath = self.fd.getData(nowSelectItem.row(), 1)
        message = '条目'+str(nowSelectItem.row() + 1)+'已取消通告'

        cancelregworker = worker(1, self.undoRegItem_main, filepath)
        cancelregworker.signals.progress.connect(self.regProgress(nowSelectItem.row()))
        cancelregworker.signals.finished.connect(
            lambda:self.regFinished(nowSelectItem.row(), 0, message))
        self.threadpool.start(cancelregworker)
    
    def undoRegItem_main(self, filepath, progress_callback):
        AddCacheSidUnit(filepath, 3, 0, 0, 0)
        progress_callback.emit(80)
        SidAnn()
        progress_callback.emit(0)

    def regProgress(self, row):
        def updateProgress(value):
            self.fd.setData(row, 3, value)
            a = self.tablemodel.createIndex(row, 3)
            self.tablemodel.dataChanged.emit(a,a)
        return updateProgress

    def regFinished(self, row, value, message):
        self.fd.setData(row, 3, value)
        a = self.tablemodel.createIndex(row, 3)
        self.tablemodel.dataChanged.emit(a,a)
        self.showStatus(message)

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
        self.splitter.setSizes([300,300,400])

    def openHub(self):
        ''' docstring: 打开本地仓库 '''
        openhubworker = worker(0, os.startfile, HOME_DIR)
        self.threadpool.start(openhubworker)

    def openFolder(self):
        ''' docstring: 打开所选文件所在文件夹 '''
        nowSelectItem = self.selectItem
        if nowSelectItem == None:
            self.showStatus('未选中文件')
            return
        tmp = self.fd.getData(nowSelectItem.row(), 1)
        filepath = tmp[:tmp.rfind('/')]
        openfolderworker = worker(0, os.startfile, filepath)
        self.threadpool.start(openfolderworker)

    def openCmdLinePage(self):
        ''' docstring: 打开命令行 '''
        self.cmdlinewindow = CmdlineWindow()
        self.cmdlinewindow.show()

    def openVideoPage(self):
        ''' docstring: 打开视频页面 '''
        self.videowindow = VideoWindow()
        self.videowindow.show()

    def importData(self):
        ''' docstring: 导入其他数据文件 '''
        fpath = QFileDialog.getOpenFileName(self, '打开文件', HOME_DIR)
        if fpath[0]:
            self.fd.load(fpath[0], 1)
            self.modelViewUpdate()

    def doubleClickItem(self, index):
        ''' docstring: 双击条目 '''
        if index != None:
            self.registerwindow = registerWindow(self.fd, index.row())
            self.registerwindow.exec_()
            if self.registerwindow.returnValue != None:
                # TODO: 根据返回值执行操作
                pass
        else:
            self.showStatus('未选中条目')

    def closeEvent(self, event):
        ''' docstring: 关闭窗口时弹出警告 '''
        status = QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        reply = QMessageBox.question(self, '警告：是否保存数据', '保存并退出?', status)
        if reply == QMessageBox.Yes:
            # 做出保存操作
            self.fd.save()
            event.accept()
        elif reply == QMessageBox.No:
            event.accept()
        else:
            event.ignore()

if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
