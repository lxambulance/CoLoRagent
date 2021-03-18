# coding=utf-8
''' docstring: CoLoR Pan主页 '''

# 添加文件路径../
import os
import sys
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
from registerWindow import registerWindow
from serviceTableModel import serviceTableModel
from serviceListModel import serviceListModel

import FileData
from worker import worker

from ProxyLib import Sha1Hash, AddCacheSidUnit, DeleteCacheSidUnit, SidAnn, Get, CacheSidUnits

class MainWindow(QMainWindow, Ui_MainWindow):
    ''' docstring: class MainWindow '''

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # 添加右键菜单
        for i in range(5):
            eval('self.listView.addAction(self.action_'+str(i+2)+')')
            eval('self.tableView.addAction(self.action_'+str(i+2)+')')
        
        # 设置选中条目
        self.selectItem = None

        # 使用自定义模型
        self.fd = FileData.FileData()
        try:
            self.fd.load()
        except:
            pass
        self.model1 = serviceListModel(self.fd)
        self.model2 = serviceTableModel(self.fd)

        # 设置模型对应的view
        self.treeView.hide()
        self.listView.setModel(self.model1)
        self.listView.setViewMode(self.listView.IconMode)
        self.listView.setResizeMode(self.listView.Adjust)
        self.listView.setIconSize(QSize(80, 80))
        self.listView.setGridSize(QSize(100, 100))
        self.tableView.setModel(self.model2)

        # 设置listview(0)与tableview(1)的视图转换
        self.switchlistortable = 1
        self.tableView.hide()

        # 设置线程池
        self.threadpool = QThreadPool()

        # 尝试新建文件仓库
        if not os.path.exists(HOME_DIR):
            os.mkdir(HOME_DIR)

        # 设置信号与槽的连接
        self.tableView.signal.connect(self.setSelectItem)
        self.listView.signal.connect(self.setSelectItem)

        self.pushButton_add.clicked.connect(self.addItem)
        self.action_1.triggered.connect(self.addItem)
        self.action_6.triggered.connect(self.delItem)
        self.pushButton_dow.clicked.connect(self.dowItem)
        self.action_4.triggered.connect(self.dowItem)

        self.pushButton_reg.clicked.connect(self.regItem)
        self.action_2.triggered.connect(self.regItem)
        self.action_3.triggered.connect(self.cancelRegItem)

        self.action_5.triggered.connect(self.openFolder)
        self.action_cmd.triggered.connect(self.openCmdLinePage)
        self.action_video.triggered.connect(self.openVideoPage)
        self.action_hub.triggered.connect(self.openHub)
        self.pushButton_swi.clicked.connect(self.switchView)
        self.action_import.triggered.connect(self.importData)

        self.listView.doubleClicked.connect(self.doubleClickItem)
        self.tableView.doubleClicked.connect(self.doubleClickItem)

    def setSelectItem(self, row):
        # print(row)
        if (row == -1):
            self.selectItem = None
            self.showStatus('')
        else:
            self.selectItem = self.model2.createIndex(row, 0)
            self.showStatus('选中条目' + str(row + 1))

    def modelViewUpdate(self):
        ''' docstring: 刷新视图 '''
        self.model1.layoutChanged.emit()
        self.model2.layoutChanged.emit()

    def showStatus(self, s):
        self.statusBar().showMessage(s)

    def addItem(self):
        ''' docstring: 按下添加按钮 '''
        self.additemwindow = AddItemWindow(self.fd)
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
                self.selectItem = self.medel2.createIndex(row, 0)
                self.regItem()

    def calcHashRet(self, row):
        ''' docstring: 这是一个返回函数的函数 '''
        def result(s):
            s = str(s)
            # print(s)
            self.fd.setData(row, 2, s)
            a = self.model2.createIndex(row, 2)
            self.model2.dataChanged.emit(a,a)
        return result

    def delItem(self):
        ''' docstring: 删除选中条目 '''
        if self.selectItem != None:
            self.fd.removeItem(self.selectItem.row())
            self.modelViewUpdate()
            self.showStatus('条目' + str(self.selectItem.row()+1) + '已删除')
            self.selectItem = None
        else:
            self.showStatus('未选中任何条目')

    def dowItem(self):
        ''' docstring: 从远端下载数据 '''
        if self.selectItem == None:
            self.showStatus('未选中任何条目')
            return
        isDow = self.fd.getData(self.selectItem.row(), 4)
        if isDow:
            self.showStatus('条目已下载')
            return
        SID = self.fd.getData(self.selectItem.row(), 2)
        filepath = self.fd.getData(self.selectItem.row(), 1)
        downloadworker = worker(0, Get, SID, filepath)
        downloadworker.signals.finished.connect(lambda:self.fd.setData(self.selectItem.row(), 4, 1))
        self.showStatus('文件'+str(self.selectItem.row()+1)+'开始下载')
        self.threadpool.start(downloadworker)

    def regItem(self):
        ''' docstring: 通告 '''
        if self.selectItem == None:
            self.showStatus('未选中条目')
            return
        isReg = self.fd.getData(self.selectItem.row(), 3)
        if isReg:
            self.showStatus('条目'+str(self.selectItem.row() + 1)+'已通告')
            return
        filepath = self.fd.getData(self.selectItem.row(), 1)
        message = '条目'+str(self.selectItem.row() + 1)+'已通告'
        
        registerworker = worker(0, self.regItem_main, filepath)
        registerworker.signals.finished.connect(
            lambda:self.regFinished(self.selectItem.row(), 1, message))
        self.threadpool.start(registerworker)

    def regItem_main(self, filepath):
        AddCacheSidUnit(filepath, 1, 0, 0, 0)
        SidAnn()

    def cancelRegItem(self):
        ''' docstring: 取消通告 '''
        if self.selectItem == None:
            self.showStatus('未选中条目')
            return
        isReg = self.fd.getData(self.selectItem.row(), 3)
        if not isReg:
            self.showStatus('条目'+str(self.selectItem.row() + 1)+'已取消通告')
            return
        filepath = self.fd.getData(self.selectItem.row(), 1)
        message = '条目'+str(self.selectItem.row() + 1)+'已取消通告'

        cancelregworker = worker(0, self.cancelRegItem_main, filepath)
        cancelregworker.signals.finished.connect(
            lambda:self.regFinished(self.selectItem.row(), 0, message))
        self.threadpool.start(cancelregworker)
    
    def cancelRegItem_main(self, filepath):
        AddCacheSidUnit(filepath, 3, 0, 0, 0)
        SidAnn()

    def regFinished(self, row, value, message):
        self.fd.setData(row, 3, value)
        a = self.model2.createIndex(row, 3)
        self.model2.dataChanged.emit(a,a)
        self.showStatus(message)

    def switchView(self):
        ''' docstring: 切换视图按钮 '''
        if self.switchlistortable:
            self.listView.hide()
            self.tableView.show()
            self.showStatus('切换到列表视图')
        else:
            self.listView.show()
            self.tableView.hide()
            self.showStatus('切换到图标视图')
        self.switchlistortable ^= 1

    def openHub(self):
        ''' docstring: 打开本地仓库 '''
        openhubworker = worker(0, os.startfile, HOME_DIR)
        self.threadpool.start(openhubworker)

    def openFolder(self):
        ''' docstring: 打开所选文件所在文件夹 '''
        if self.selectItem == None:
            self.showStatus('未选中文件')
            return
        tmp = self.fd.getData(self.selectItem.row(), 1)
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
            self.fd.load(fpath[0])
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
