# coding=utf-8
''' docstring: CoLoR Pan主页 '''

import time
import json
import ProxyLib as PL
from ProxyLib import (
    Sha1Hash, AddCacheSidUnit, DeleteCacheSidUnit,
    SidAnn, Get, CacheSidUnits)
from scapy.utils import randstring
from worker import worker
import FileData as FD
from serviceTable import serviceTableModel, progressBarDelegate
from serviceList import serviceListModel
from AddItemWindow import AddItemWindow
from GraphicWindow import GraphicWindow
from videoWindow import videoWindow
from cmdWindow import cmdWindow
from mainPage import Ui_MainWindow
import pyqtgraph as pg

from PyQt5.QtGui import QIcon, QPalette
from PyQt5.QtCore import QSize, QThreadPool, qrand, QTimer
from PyQt5.QtWidgets import (QApplication, QMainWindow, QAction, 
    QMessageBox, QStyleFactory, QTreeWidgetItem, QFileDialog,
    QHeaderView, QTableWidgetItem, QVBoxLayout, QScrollArea, QWidget)

import os
import sys
import time

__BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))).replace('\\', '/')
sys.path.append(__BASE_DIR)
HOME_DIR = __BASE_DIR + '/.tmp'
DATA_PATH = __BASE_DIR + '/data.json'
starttime = time.strftime("%y-%m-%d_%H_%M_%S", time.localtime())
LOG_PATH = HOME_DIR + f'/{starttime}.log'


class MainWindow(QMainWindow, Ui_MainWindow):
    ''' docstring: class MainWindow '''

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # 隐藏searchLog搜索框
        self.searchLog.hide()

        # 修改数据存储路径
        FD.DATA_PATH = DATA_PATH
        FD.HOME_DIR = HOME_DIR
        
        # 尝试新建文件仓库
        if not os.path.exists(HOME_DIR):
            os.mkdir(HOME_DIR)

        # 设置线程池 TODO: 线程池放到窗口外面
        self.threadpool = QThreadPool()

        # 用于统计频率和AS统计
        self.timer = QTimer()
        self.timer_message = QTimer()
        self.timer.setInterval(3000)
        self.messagebox = None

        # 用于收包显示的变量
        self.mapfromSIDtoItem = {}
        self.datapackets = []

        # TODO: 在Get中写入Nid？
        self.nid = f"{PL.Nid:032x}"

        # 设置表格头伸展方式
        self.dataPktReceive.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.dataPktReceive.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)

        # 设置速度图线格式
        self.speed_x = [x*5 for x in range(20)]
        self.speed_y = [0]*20
        self.totalsize = 0
        speedpen = pg.mkPen(color=(255,0,0))
        color = self.palette().color(QPalette.Background).name()
        color = '#ffffff' if color == '#f0f0f0' else color
        self.speedGraph.setBackground(color)
        self.speed_line = self.speedGraph.plot(self.speed_x, self.speed_y, pen=speedpen)

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
        self.button_swi = QAction(QIcon(":/icon/switchView"), "视图切换", self)
        self.button_swi.setStatusTip("视图切换")
        self.toolBar.addAction(self.button_swi)
        self.button_openfolder = QAction(QIcon(":/icon/openFolder"), "打开文件夹", self)
        self.button_openfolder.setStatusTip("打开文件夹")
        self.toolBar.addAction(self.button_openfolder)
        self.button_addfile = QAction(QIcon(":/icon/addFile"), "添加文件", self)
        self.button_addfile.setStatusTip("添加文件")
        self.toolBar.addAction(self.button_addfile)
        self.button_showtopo = QAction(QIcon(":/icon/openMap"), "显示网络拓扑", self)
        self.button_showtopo.setStatusTip("显示网络拓扑")
        self.toolBar.addAction(self.button_showtopo)
        self.button_showtopo.setCheckable(True)

        # 设置其他窗口为空
        self.videowindow = None
        self.cmdwindow = None
        self.action_cmdline.setVisible(False) # TODO: 命令行待完善

        # 设置选中条目
        self.selectItems = []

        # 使用自定义模型
        self.fd = FD.FileData(nid=self.nid)
        try:
            self.fd.load()
        except:
            pass
        self.listmodel = serviceListModel(self.fd)
        self.tablemodel = serviceTableModel(self.fd)
        self.progressbardelegate = progressBarDelegate(self)
        self.progressbarpool = {}

        # 设置网络拓扑窗口
        self.graphicwindow = GraphicWindow(self.fd)
        self.graphicwindow.loadTopo(DATA_PATH)
        self.graphicwindow.hide()

        # 设置日志记录
        for i in range(self.fd.rowCount()):
            filename = self.fd.getData(i)
            self.graphicwindow.chooseFile.addItem(filename)
            # 添加log记录
            self.logWidget.addLog("<导入> 文件或服务", filename, True)

        # 设置模型对应的view
        self.listView.setModel(self.listmodel)
        self.listView.setViewMode(self.listView.IconMode)
        self.listView.setResizeMode(self.listView.Adjust)
        self.listView.setIconSize(QSize(64, 64))
        self.listView.setGridSize(QSize(80, 80))
        self.tableView.setModel(self.tablemodel)
        self.tableView.setItemDelegate(self.progressbardelegate)

        # 设置listview(0)与tableview(1)的视图转换
        self.switchlistortable = 0
        self.tableView.hide()
        self.splitter_horizontal.setSizes([200, 200, 500])
        self.splitter_vertical.setSizes([350, 450])

        # 设置信号与槽的连接
        # 视图信号
        self.tableView.signal_select.connect(self.setSelectItem)
        self.listView.signal_select.connect(self.setSelectItem)
        self.listView.signal_add.connect(self.addItems)
        self.tableView.doubleClicked.connect(self.viewInfo)
        self.listView.doubleClicked.connect(self.viewInfo)
        # 拓扑图信号连接
        self.graphicwindow.GS.hide_window_signal.connect(self.showTopo)
        self.graphicwindow.GS.advencedRegrow_signal.connect(self.advancedRegItem)
        # 动作信号
        self.action_add.triggered.connect(self.addItem)
        self.action_del.triggered.connect(self.delItem)
        self.action_dow.triggered.connect(self.dowItem)
        self.action_reg.triggered.connect(self.regItem)
        # logTexted不处理setText函数，textChanged处理所有改动
        self.action_undoReg.triggered.connect(self.undoRegItem)
        self.action_openDir.triggered.connect(self.openFolder)
        self.action_hub.triggered.connect(self.openHub)
        self.action_import.triggered.connect(self.importData)
        self.action_swi.triggered.connect(self.switchView)
        self.action_reset.triggered.connect(self.resetView)
        self.action_video.triggered.connect(self.openVideoWindow)
        self.action_cmdline.triggered.connect(self.openCmdWindow)
        self.action_advancedreg.triggered.connect(self.showAdvancedReg)
        # 按钮信号
        self.button_swi.triggered.connect(self.switchView)
        self.button_openfolder.triggered.connect(self.openFolder)
        self.button_addfile.triggered.connect(self.addItem)
        self.button_showtopo.triggered.connect(self.showTopo)
        # 收包信号
        self.dataPktReceive.itemClicked.connect(self.showMatchedPIDs)
        # 计时信号
        self.timer.timeout.connect(self.updateSpeedLine)
        self.timer_message.timeout.connect(self.timerMessageClear)
        
        # 计时器开始
        self.timer.start()

    def openCmdWindow(self):
        ''' docstring: 打开命令行窗口 '''
        if not self.cmdwindow:
            self.cmdwindow = cmdWindow()
        else:
            self.cmdwindow.setGeometry(self.cmdwindow.geometry())
        self.cmdwindow.show()
        self.logWidget.addLog("<动作> 打开视频窗口", f"Geo = {self.cmdwindow.geometry()}", False)

    def openVideoWindow(self):
        ''' docstring: 打开视频窗口 '''
        if not self.videowindow:
            self.videowindow = videoWindow()
        else:
            self.videowindow.setGeometry(self.videowindow.geometry())
        self.videowindow.show()
        self.logWidget.addLog("<动作> 打开视频窗口", f"Geo = {self.videowindow.geometry()}", False)

    def showTopo(self, status):
        ''' docstring: 显示(status==True)/隐藏(False) 拓扑图函数 '''
        if status:
            geo = self.graphicwindow.geometry()
            if geo.left() or geo.top():
                self.graphicwindow.setGeometry(geo)
            self.graphicwindow.show()
            self.logWidget.addLog("<动作> 打开拓扑窗口", f"Geo = {geo}", False)
        else:
            # 确保通过x关闭后，主窗口按钮状态同步
            if self.button_showtopo.isChecked():
                self.button_showtopo.trigger()
            self.graphicwindow.hide()

    def updateSpeedLine(self):
        ''' docstring: 设置折线图显示，3秒刷新一次 '''
        self.speed_x = self.speed_x[1:]
        self.speed_x.append(self.speed_x[-1] + 3)
        self.speed_y = self.speed_y[1:]
        self.speed_y.append(self.totalsize)
        if self.totalsize:
            self.logWidget.addLog("<统计> 收包大小", f"Size = {self.totalsize} 字节", True)
        self.totalsize = 0
        self.speed_line.setData(self.speed_x, self.speed_y)
        # 测试拖动条效果
        # bar = self.logWidget.scrollarea.verticalScrollBar()
        # print(bar.value(), bar.maximum())

    def getPathFromPkt(self, type, SID, paths, size, nid):
        ''' docstring: 收包信息分类显示 '''
        name = 'Unknown packet'
        for i in range(self.fd.rowCount()):
            if SID == self.fd.getData(i,2):
                name = self.fd.getData(i,0)
                break
        if (type&0xff) == 0x72:
            name = '<Get>' + name
        elif (type&0xff) == 0x73:
            if not ((type >> 8) & 1):
                name = '<Data>' + name
                paths = paths[1:]
            else:
                name = '<Data Ack>' + name
            paths.reverse()
        else:
            name = '<Control> packet'
        item = self.mapfromSIDtoItem.get(name+SID, None)
        if not item:
            # 该SID下第一个包，建立顶层节点topItem
            self.datapackets.append(QTreeWidgetItem(None, [name, "0", SID]))
            self.dataPktReceive.addTopLevelItem(self.datapackets[-1])
            self.mapfromSIDtoItem[name+SID] = self.datapackets[-1]
            item = self.datapackets[-1]
        path_str = '-'.join(map(lambda x:f"<{x:08x}>",paths))
        if (type&0xff) == 0x72:
            item.addChild(QTreeWidgetItem([f"来源nid={nid:032x}", str(size), "PIDs="+path_str]))
            self.graphicwindow.graphics_global.setMatchedPIDs(path_str, flag=False, size=size)
            self.totalsize += size # 统计总收包大小，speedline需要使用
        elif (type&0xff) == 0x73:
            num = item.childCount()
            item.addChild(QTreeWidgetItem([f"包片段{num+1}", str(size), "PIDs="+path_str]))
            self.graphicwindow.graphics_global.setMatchedPIDs(path_str, flag=False, pkttype=1, size=size)
            totsize = int(item.text(1))
            item.setText(1, str(totsize+size))
            self.totalsize += size # 统计总收包大小，speedline需要使用
        else:
            num = item.childCount()
            item.addChild(QTreeWidgetItem([f"包片段{num+1}", str(size), ""]))

    def showMatchedPIDs(self, item, column):
        ''' docstring: 选中物体，显示匹配 '''
        # print(item.text(column))
        pitem = item.parent()
        if not pitem or 'Control' in pitem.text(0):
            self.setStatus('选择正确的包可显示匹配')
            return
        else:
            self.setStatus('')
        if not self.graphicwindow.graphics_global.setMatchedPIDs(item.text(2)):
            self.setStatus('匹配失败')

    def handleMessageFromPkt(self, messageType, message):
        ''' docstring: 显示后端发送的信息，添加log记录 '''
        if messageType == 0:
            # 收到hint
            self.logWidget.addLog("<消息> 后端提示", f"消息码={messageType}\n消息内容\n{message}\n", True)
        elif messageType == 1:
            # 收到warning
            self.logWidget.addLog("<警告> 后端警告", f"消息码={messageType}\n消息内容\n{message}\n", True)
        elif messageType == 2:
            # 收到攻击警告
            self.logWidget.addLog("<警告> 收到攻击警告", f"消息码={messageType}\n消息内容\n{message}\n", True)
            if not self.messagebox:
                self.messagebox = QMessageBox(self)
                self.messagebox.setWindowTitle('<Attacking>')
                self.messagebox.setText(message)
                self.messagebox.setModal(False)
                self.messagebox.buttonClicked.connect(self.timerMessageClear)
                self.messagebox.show()
                self.timer_message.start(3000)
        else:
            self.setStatus('无效的后端信息')

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
            self.setStatus(status)

    def modelViewUpdate(self):
        ''' docstring: 强制刷新视图 '''
        self.listmodel.layoutChanged.emit()
        self.tablemodel.layoutChanged.emit()

    def setStatus(self, s):
        ''' docstring: 状态栏信息显示 '''
        self.statusbar.showMessage(s)

    def addItem(self):
        ''' docstring: 添加条目（仅支持单体添加） '''
        self.additemwindow = AddItemWindow(self.fd, self)
        ret = self.additemwindow.exec_()
        row = self.additemwindow.newitemrow
        needReg = self.additemwindow.needReg
        # ret 可用于后续判断返回结果
        if (ret) and (row != None):
            self.modelViewUpdate()
            filename = self.fd.getData(row, 0)
            self.graphicwindow.chooseFile.addItem(filename)
            # 添加log记录
            self.logWidget.addLog("<添加> 文件或服务", filename, True)
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
        ''' docstring: 批量拖入文件，TODO：拉起额外线程处理 '''
        nowitems = items.copy()
        tmplog = ''
        if len(nowitems):
            lastrow = self.fd.rowCount()
            for item_str in nowitems:
                if os.path.isfile(item_str):
                    item = item_str.replace('\\', '/')
                    pos = item.rfind('/')
                    self.fd.addItem(filename=item[pos+1:], filepath=item)
                    self.graphicwindow.chooseFile.addItem(item[pos+1:])
                    # 添加log记录
                    self.logWidget.addLog("<添加> 文件或服务", item[pos+1:], True)
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
        ''' docstring: 计算hash并更新视图（这是一个返回函数的函数） '''
        def result(s):
            s = self.nid + s
            # print(s)
            self.fd.setData(row, 2, s)
            a = self.tablemodel.createIndex(row, 2)
            self.tablemodel.dataChanged.emit(a, a)
        return result

    def delItem(self):
        ''' docstring: 删除选中条目（拉起额外线程处理） '''
        if len(self.selectItems) == 0:
            self.setStatus('未选中任何条目')
        else:
            nowSelectItems = self.selectItems.copy()
            delitemworker = worker(1, self.delItem_multi, nowSelectItems)
            delitemworker.signals.finished.connect(lambda: self.modelViewUpdate())
            delitemworker.signals.finished.connect(lambda: self.setStatus('条目已删除'))
            delitemworker.signals.message.connect(self.logWidget.addLog)
            self.threadpool.start(delitemworker)

    def delItem_multi(self, items, message_callback, **kwargs):
        ''' docstring: 删除条目线程实际处理函数 '''
        items.sort(reverse=True)
        for item in items:
            if not self.fd.getData(item, 0):
                continue
            # 添加log记录
            message_callback.emit('<删除> 文件或服务', f'file {self.fd.getData(item, 0)}')
            self.fd.removeItem(item)
            self.graphicwindow.chooseFile.removeItem(item)
            self.selectItems.remove(item)

    def dowItem(self):
        ''' docstring: 从远端下载数据（拉起额外线程处理） '''
        if len(self.selectItems) == 0:
            self.setStatus('未选中任何条目')
        else:
            nowSelectItems = self.selectItems.copy()
            dowitemworker = worker(1, self.dowItem_multi, nowSelectItems)
            for item in nowSelectItems:
                dowitemworker.signals.progress.connect(
                    self.updateProgress(item, 4))
            dowitemworker.signals.finished.connect(
                lambda: self.setStatus('条目已下载'))
            dowitemworker.signals.message.connect(self.logWidget.addLog)
            self.threadpool.start(dowitemworker)

    def dowItem_multi(self, items, progress_callback, message_callback):
        ''' docstring: 下载数据线程实际处理函数 '''
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
            # 添加log记录
            message_callback.emit('<下载> 文件或服务', f'file {self.fd.getData(item, 0)}\n')
        # TODO：涉及进度条完成状态需要通过color monitor精确判断

    def regItem(self):
        ''' docstring: 文件通告（拉起额外线程处理） '''
        if len(self.selectItems) == 0:
            self.setStatus('未选中条目')
        else:
            nowSelectItem = self.selectItems.copy()
            regitemworker = worker(1, self.regItem_multi, nowSelectItem)
            for item in nowSelectItem:
                regitemworker.signals.progress.connect(
                    self.updateProgress(item, 3))
            regitemworker.signals.finished.connect(
                lambda: self.setStatus('条目已通告'))
            regitemworker.signals.message.connect(self.logWidget.addLog)
            self.threadpool.start(regitemworker)

    def showAdvancedReg(self):
        ''' docstring: 高级通告页面跳转 '''
        if len(self.selectItems) == 0:
            self.setStatus('未选中条目')
        elif len(self.selectItems) > 1:
            self.setStatus('选中要素过多')
        else:
            nowSelectItem = self.selectItems[0]
            if not self.button_showtopo.isChecked():
                self.button_showtopo.trigger()
            self.graphicwindow.chooseFile.setCurrentIndex(nowSelectItem)
            self.graphicwindow.showAdvancedRegrow(nowSelectItem)
            if not self.graphicwindow.Toolbar.isVisible():
                self.graphicwindow.actionReopenToolbar.trigger()
            if not self.graphicwindow.pushButtonAdvancedReg.isChecked():
                self.graphicwindow.pushButtonAdvancedReg.click()

    def advancedRegItem(self, nowSelectItem):
        ''' docstring: 高级通告（拉起额外线程处理，单体） '''
        if nowSelectItem<0 or nowSelectItem>=self.fd.rowCount():
            return
        filepath = self.fd.getData(nowSelectItem, 1)
        level = self.fd.getData(nowSelectItem, 5)
        whitelist = self.fd.getData(nowSelectItem, 6)
        kwargs = {}
        if level:
            kwargs['level'] = int(level)
        if whitelist:
            kwargs['WhiteList'] = list(map(int,whitelist.split(',')))
        regitemworker = worker(0, AddCacheSidUnit, filepath, 1,1,1,1, **kwargs)
        regitemworker.signals.finished.connect(lambda:self.updateProgress(nowSelectItem, 3)(100))
        regitemworker.signals.finished.connect(lambda:self.setStatus('条目已通告'))
        regitemworker.signals.finished.connect(SidAnn)
        self.threadpool.start(regitemworker)

    def regItem_multi(self, items, progress_callback, message_callback):
        ''' docstring: 文件通告线程实际处理函数 '''
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
            # 添加log记录
            message_callback.emit('<注册> 文件或服务', f'file {self.fd.getData(item, 0)}\n')
        SidAnn()
        progress_callback.emit(100)

    def undoRegItem(self):
        ''' docstring: 取消通告（拉起额外线程处理） '''
        if len(self.selectItems) == 0:
            self.setStatus('未选中条目')
        else:
            nowSelectItem = self.selectItems.copy()
            undoregworker = worker(1, self.undoRegItem_multi, nowSelectItem)
            for item in nowSelectItem:
                undoregworker.signals.progress.connect(
                    self.updateProgress(item, 3))
            undoregworker.signals.finished.connect(
                lambda: self.setStatus('条目已取消通告'))
            undoregworker.signals.message.connect(self.logWidget.addLog)
            self.threadpool.start(undoregworker)

    def undoRegItem_multi(self, items, progress_callback, message_callback):
        ''' docstring: 取消通告线程实际处理函数 TODO：没有考虑高级通告的处理参数 '''
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
            # 添加log记录
            message_callback.emit('<取消注册> 文件或服务', f'file {self.fd.getData(item, 0)}\n')
        SidAnn()
        progress_callback.emit(0)

    def updateProgress(self, row, column):
        ''' docstring: 进度条刷新显示函数（返回函数） '''
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
            self.setStatus('切换到列表视图')
        else:
            self.listView.show()
            self.tableView.hide()
            self.setStatus('切换到图标视图')

    def resetView(self):
        ''' docstring: 恢复初始视图格式 '''
        if not self.toolBar.toggleViewAction().isChecked():
            self.toolBar.toggleViewAction().trigger()
        self.splitter_horizontal.setSizes([200, 200, 500])
        self.splitter_vertical.setSizes([350, 450])

    def openHub(self):
        ''' docstring: 打开本地仓库 '''
        openhubworker = worker(0, os.startfile, HOME_DIR)
        self.threadpool.start(openhubworker)

    def openFolder(self):
        ''' docstring: 打开所选文件所在文件夹（拉起额外线程处理） '''
        nowSelectItem = self.selectItems.copy()
        if len(nowSelectItem) == 0:
            self.setStatus('未选中文件')
            return
        elif len(nowSelectItem) != 1:
            self.setStatus('选中文件过多')
            return
        # print(nowSelectItem[0])
        tmp = self.fd.getData(nowSelectItem[0], 1)
        # print(tmp)
        if not os.path.exists(tmp) or not tmp:
            self.setStatus('文件不存在')
            return
        filepath = tmp[:tmp.rfind('/')]
        openfolderworker = worker(0, os.startfile, filepath)
        openfolderworker.signals.finished.connect(
            lambda: self.setStatus('文件已打开'))
        self.threadpool.start(openfolderworker)

    def importData(self):
        ''' docstring: 导入其他数据文件 '''
        fpath = QFileDialog.getOpenFileName(self, '打开文件', HOME_DIR)
        if fpath[0]:
            lastlen = self.fd.rowCount()
            ret = self.fd.load(fpath[0])
            if ret:
                self.setStatus(ret)
            else:
                self.modelViewUpdate()
                for i in range(lastlen, self.fd.rowCount()):
                    filename = self.fd.getData(i)
                    # 添加log记录
                    # self.logText.append(f'<add> file {filename}\n')

    def closeEvent(self, event):
        ''' docstring: 关闭窗口时弹出警告 '''
        status = QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        reply = QMessageBox.question(self, '警告：是否保存数据', '保存并退出?', status)
        if reply == QMessageBox.Yes:
            # 做出保存操作
            self.fd.save()
            self.graphicwindow.saveTopo(DATA_PATH)
            self.graphicwindow.close()
            self.cmdwindow = None
            self.videowindow = None
            self.saveLog()
            event.accept()
        elif reply == QMessageBox.No:
            self.graphicwindow.close()
            self.cmdwindow = None
            self.videowindow = None
            event.accept()
        else:
            event.ignore()

    def saveLog(self):
        ''' docstring: 保存日志文件 '''
        with open(LOG_PATH, 'w', encoding='utf-8') as f:
            # s = self.logText.toPlainText()
            # f.write(s)
            pass

    def viewInfo(self, index):
        ''' docstring: 双击条目显示文件内容 '''
        filepath = self.fd.getData(index.row(), 1)
        filename = self.fd.getData(index.row(), 0)
        filepid = self.fd.getData(index.row(), 2)
        viewjsonworker = worker(0, self.viewJson, filename, filepath, filepid)
        # viewjsonworker.signals.result.connect(self.logText.append)
        self.threadpool.start(viewjsonworker)

    def viewJson(self, filename, filepath, filepid):
        ''' docstring: 双击显示Json格式文件 '''
        ret = f'<double click> {filename} (SID:{filepid}) = '
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
                    if len(fcontent) > 512 * 3:
                        return ret + '{...(内容过长)...}\n'
            data = json.loads(fcontent)
        except:
            return ret + '非JSON格式文件\n'
        ret += '\n' + json.dumps(data, sort_keys=True, indent=4, separators=(',', ':')) + '\n'
        return ret

    def timerMessageClear(self):
        ''' docstring: 告警窗清空 '''
        self.timer_message.stop()
        self.messagebox.done(1)
        self.messagebox = None


if __name__ == '__main__':
    from random import randint
    import qdarkstyle as qds

    app = QApplication(sys.argv)
    # app.setStyleSheet(qds.load_stylesheet_pyqt5())
    window = MainWindow()
    window.show()

    # 测试收包匹配功能
    window.getPathFromPkt(0x72, '123', [0x11222695], 100, 0x12)
    window.getPathFromPkt(0x72, '123', [0x33446217,0x11222695], 1500, 0x23)
    window.getPathFromPkt(0x73, 'abc', [0x11222695,0x11221211,0x33446217,0x55661234], 1000, 0)
    window.getPathFromPkt(0x173, 'abc', [0x11222695,0x55661234], 1000, 0)
    window.getPathFromPkt(0x173, 'abc', [0x11227788], 100, 0)
    window.getPathFromPkt(0x73, 'abc', [0x11227788,0x11227788,0x33441234,0x77880000], 100, 0)
    window.getPathFromPkt(0x74, '', [], 20, 0)
    # 测试告警信息显示功能
    window.handleMessageFromPkt(2, 'test1\ncontent1\n')
    window.handleMessageFromPkt(2, 'test2\ncontent2\n')
    # log添加测试
    for i in range(3):
        window.logWidget.addLog("Hello", f"world{i}", randint(1,5)==1)

    sys.exit(app.exec_())
