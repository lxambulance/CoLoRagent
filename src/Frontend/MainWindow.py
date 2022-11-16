# coding=utf-8
""" docstring: CoLoR 网盘功能主页 """


import os
import sys
import time
import json
from worker import worker
import InnerConnection as ic
import FileData as fd
from ServiceTable import serviceTableModel, progressBarDelegate
from ServiceList import serviceListModel
from addItemWindow import AddItemWindow
from GraphicWindow import GraphicWindow
from VideoWindow import videoWindow
from CmdWindow import cmdWindow
from ui_MainPage import Ui_MainWindow
import pyqtgraph as pg
from PyQt5.QtGui import QIcon, QPalette
from PyQt5.QtCore import QSize, QThreadPool, QTimer, QObject, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QMainWindow, QAction,
                             QMessageBox, QTreeWidgetItem, QHeaderView)


__BASE_DIR = "."
HOME_DIR = __BASE_DIR + "/.tmp"
DATA_PATH = __BASE_DIR + "/data.json"
starttime = time.strftime("%y-%m-%d_%H_%M_%S", time.localtime())
LOG_PATH = HOME_DIR + f"/{starttime}.log"


class MainWindowSignals(QObject):
    """ docstring: signals class """

    finished = pyqtSignal()
    calchashfinished = pyqtSignal(int)


class MainWindow(QMainWindow, Ui_MainWindow):
    """ docstring: class MainWindow """

    def __init__(self, threadpool, myNID, *, configpath=DATA_PATH, filetmppath=HOME_DIR, configdata=None):
        super().__init__()
        self.setupUi(self)
        self.threadpool = threadpool
        self.NID = myNID
        self.configpath = configpath
        self.filetmppath = filetmppath
        self.configdata = configdata or {}
        self.retidnow = 0
        self.retidexpected = 0
        self.id2rowmap = {}
        self.signals = MainWindowSignals()
        self.waitdowitemcount = 0
        self.waitregitemcount = 0
        self.waitunregitemcount = 0

        # 设置定时器用于统计收包速度和各自治域信息统计
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer_message = QTimer()
        self.messagebox = None
        # 用于收包显示的变量
        self.mapfromSIDtoItem = {}
        self.datapackets = []
        # 设置选中条目
        self.selectItems = []

        # 隐藏searchLog搜索框。TODO：搜索功能
        self.searchLog.hide()
        # 隐藏其他窗口视图（命令行、视频页）。TODO: 命令行待完善
        self.videowindow = None
        self.cmdwindow = None
        self.action_video.setVisible(False)
        self.action_cmdline.setVisible(False)
        # 定制展示窗口功能
        self.__set_filelistfunction()
        # 设置数据接收区表格头伸展方式
        self.dataPktReceive.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.dataPktReceive.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        # 设置速度图线格式
        self.speed_x = [x * 5 for x in range(20)]
        self.speed_y = [0] * 20
        self.totalsize = 0
        speedpen = pg.mkPen(color=(255, 0, 0))
        color = self.palette().color(QPalette.Background).name()
        color = "#ffffff" if color == "#f0f0f0" else color
        self.speedGraph.setBackground(color)
        self.speed_line = self.speedGraph.plot(self.speed_x, self.speed_y, pen=speedpen)
        # 设置网络拓扑窗口
        self.graphicwindow = GraphicWindow(self.fd)
        self.graphicwindow.loadTopo(self.configdata.get("topo map", None))
        self.graphicwindow.hide()
        # 设置日志记录
        for i in range(self.fd.rowCount()):
            filename = self.fd.getData(i)
            self.graphicwindow.chooseFile.addItem(filename)
            # 添加log记录
            self.logWidget.addLog("<导入> 文件或服务", filename, True)

        # 设置信号/槽的连接
        # 视图信号
        self.tableView.signal_select.connect(self.setSelectItem)
        self.listView.signal_select.connect(self.setSelectItem)
        self.listView.signal_add.connect(self.urlAddItems)
        self.tableView.doubleClicked.connect(self.viewInfo)
        self.listView.doubleClicked.connect(self.viewInfo)
        # 拓扑图信号
        self.graphicwindow.GS.hide_window_signal.connect(self.showTopo)
        self.graphicwindow.GS.advencedRegrow_signal.connect(self.advancedRegItem)
        # 动作信号
        self.action_add.triggered.connect(self.addItem)
        self.action_del.triggered.connect(self.delItem)
        self.action_dow.triggered.connect(self.dowItem)
        self.action_reg.triggered.connect(lambda: self.regItem(True))
        # logTexted不处理setText函数，textChanged处理所有改动
        self.action_undoReg.triggered.connect(lambda: self.regItem(False))
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
        self.button_startvideoserver.triggered.connect(self.startVideoServer)
        # 收包信号
        ic.backendmessage.pathdata.connect(lambda x: self.getPathFromPkt(**x))
        ic.backendmessage.message.connect(lambda x: self.handleMessageFromPkt(**x))
        self.dataPktReceive.itemClicked.connect(self.showMatchedPIDs)
        # 计时信号
        self.timer.timeout.connect(self.updateSpeedLine)
        self.timer_message.timeout.connect(self.timerMessageClear)

        # 计时器打开
        self.timer.start()

    def __set_filelistfunction(self):
        """ docstring: 文件列表展示窗口功能定制 """
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

        # 添加工具栏按钮
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
        self.button_startvideoserver = QAction(QIcon(":/icon/server-multi-button"), "启动视频服务", self)
        self.button_startvideoserver.setStatusTip("启动视频服务")
        self.button_startvideoserver.setCheckable(True)
        self.toolBar.addAction(self.button_startvideoserver)

        # 使用自定义模型
        self.fd = fd.FileData(NID=self.NID, initData=self.configdata.get("file data", None))
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

        # 设置listview(0)与tableview(1)的视图转换
        self.switchlistortable = 0
        self.tableView.hide()
        self.splitter_horizontal.setSizes([200, 200, 500])
        self.splitter_vertical.setSizes([350, 450])

    def startVideoServer(self, status):
        """ docstring: 启动视频应用服务 """
        print(status)
        if status:
            reply = QMessageBox.question(self, "通知", "是否开启摄像头服务？", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                self.button_startvideoserver.toggle()
                return
            request = {"type": "startvideoserver"}
        else:
            request = {"type": "stopvideoserver"}
        self.startvideoserverworker = worker(0, ic.put_request, request)
        self.threadpool.start(self.startvideoserverworker)

    def openCmdWindow(self):
        """ docstring: 打开命令行窗口。TODO：命令行未完成，暂时隐藏 """
        if not self.cmdwindow:
            self.cmdwindow = cmdWindow()
        else:
            self.cmdwindow.setGeometry(self.cmdwindow.geometry())
        self.cmdwindow.show()
        self.logWidget.addLog("<动作> 打开视频窗口", f"Geo = {self.cmdwindow.geometry()}", False)

    def openVideoWindow(self):
        """ docstring: 打开视频窗口。TODO：视频页未完成，暂时隐藏 """
        if not self.videowindow:
            self.videowindow = videoWindow()
        else:
            self.videowindow.setGeometry(self.videowindow.geometry())
        self.videowindow.show()
        self.logWidget.addLog("<动作> 打开视频窗口", f"Geo = {self.videowindow.geometry()}", False)

    def showTopo(self, status):
        """ docstring: 显示(status==True)/隐藏(False) 拓扑图 """
        if status:
            geo = self.graphicwindow.geometry()
            if geo.left() or geo.top():
                self.graphicwindow.setGeometry(geo)
            self.graphicwindow.show()
            if not self.graphicwindow.pushButtonShowBaseinfo.isChecked():
                self.graphicwindow.pushButtonShowBaseinfo.click()
            if not self.graphicwindow.pushButtonShowASThroughput.isChecked():
                self.graphicwindow.pushButtonShowASThroughput.click()
            self.logWidget.addLog("<动作> 打开拓扑窗口", f"Geo = {geo}", False)
        else:
            # 确保通过x关闭后，主窗口按钮状态同步
            if self.button_showtopo.isChecked():
                self.button_showtopo.toggle()
            self.graphicwindow.hide()

    def showAdvancedReg(self):
        """ docstring: 高级通告页面跳转 """
        if len(self.selectItems) == 0:
            self.setStatus("未选中条目")
            return
        if len(self.selectItems) > 1:
            self.setStatus("选中要素过多")
            return
        nowSelectItem = self.selectItems[0]
        if not self.button_showtopo.isChecked():
            self.button_showtopo.trigger()
        self.graphicwindow.chooseFile.setCurrentIndex(nowSelectItem)
        self.graphicwindow.showAdvancedRegrow(nowSelectItem)
        if not self.graphicwindow.Toolbar.isVisible():
            self.graphicwindow.actionReopenToolbar.trigger()
        if not self.graphicwindow.pushButtonAdvancedReg.isChecked():
            self.graphicwindow.pushButtonAdvancedReg.click()

    def updateSpeedLine(self):
        """ docstring: 设置折线图显示，1秒刷新一次 """
        self.speed_x = self.speed_x[1:]
        self.speed_x.append(self.speed_x[-1] + 1)
        self.speed_y = self.speed_y[1:]
        self.speed_y.append(self.totalsize / 1000)
        if self.totalsize:
            self.logWidget.addLog("<统计> 收包大小", f"Size = {self.totalsize} 字节", True)
        self.totalsize = 0
        speed_max = 0
        for i in range(len(self.speed_y)):
            speed_max = max(speed_max, self.speed_y[i])
        speed_max = (speed_max // 10 + 1) * 10
        self.speedGraph.setYRange(0, speed_max)
        self.speed_line.setData(self.speed_x, self.speed_y)

    def getPathFromPkt(self, pkttype, SID, paths, size, NID):
        """ docstring: 收包信息分类显示。type == 0x173表示data ack """
        name = "Unknown packet"
        for i in range(self.fd.rowCount()):
            if SID == self.fd.getData(i, 2):
                name = self.fd.getData(i, 0)
                break
        if (pkttype & 0xff) == 0x72:
            name = "<Get>" + name
        elif (pkttype & 0xff) == 0x73:
            if not ((pkttype >> 8) & 1):
                name = "<Data>" + name
                paths = paths[1:]
            else:
                name = "<Data Ack>" + name
            paths.reverse()
        else:
            name = "<Control> packet"
        item = self.mapfromSIDtoItem.get(name + SID, None)
        if not item:
            # 该SID下第一个包，建立顶层节点topItem
            self.datapackets.append(QTreeWidgetItem(None, [name, "0", SID]))
            self.dataPktReceive.addTopLevelItem(self.datapackets[-1])
            self.mapfromSIDtoItem[name + SID] = self.datapackets[-1]
            item = self.datapackets[-1]
        path_str = "-".join(map(lambda x: f"<{x:08x}>", paths))
        if (pkttype & 0xff) == 0x72:
            item.addChild(QTreeWidgetItem(
                [f"来源nid={NID}", str(size), "PIDs=" + path_str]))
            self.graphicwindow.graphics_global.setMatchedPIDs(
                path_str, flag=False, size=size)
            self.graphicwindow.graphics_global.getASid(path_str, False, size)
        elif (pkttype & 0xff) == 0x73:
            num = item.childCount()
            item.addChild(QTreeWidgetItem(
                [f"包片段{num + 1}", str(size), "PIDs=" + path_str]))
            self.graphicwindow.graphics_global.setMatchedPIDs(
                path_str, flag=False, pkttype=1, size=size)
            self.graphicwindow.graphics_global.getASid(path_str, True, size)
        else:
            num = item.childCount()
            item.addChild(QTreeWidgetItem([f"包片段{num + 1}", str(size), ""]))
        totsize = int(item.text(1))
        item.setText(1, str(totsize + size))
        self.totalsize += size  # 统计总收包大小，speedline需要使用

    def showMatchedPIDs(self, item, column):
        """ docstring: 选中物体，显示匹配 """
        # print(item.text(column))
        pitem = item.parent()
        if not pitem or "Control" in pitem.text(0):
            self.setStatus("选择正确的包可显示匹配")
            return
        else:
            self.setStatus("")
        if not self.graphicwindow.graphics_global.setMatchedPIDs(item.text(2)):
            self.setStatus("匹配失败")

    def handleMessageFromPkt(self, messageType, message):
        """ docstring: 显示后端发送的信息并添加log记录 """
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
                self.messagebox.setWindowTitle("<Attacking>")
                self.messagebox.setText(message)
                self.messagebox.setModal(False)
                self.messagebox.buttonClicked.connect(self.timerMessageClear)
                self.messagebox.show()
                self.timer_message.start(3000)
        else:
            self.setStatus("无效的后端信息")

    def setSelectItem(self, items):
        """ docstring: 通过列表和表格多选信号返回选择条目对象 """
        if len(items) == 0:
            self.selectItems = []
        else:
            status = "选中条目"
            self.selectItems = []
            for item in items:
                self.selectItems.append(item.row())
                status += " " + str(item.row() + 1)
            self.setStatus(status)

    def modelViewUpdate(self):
        """ docstring: 强制刷新视图 """
        self.listmodel.layoutChanged.emit()
        self.tablemodel.layoutChanged.emit()

    def setStatus(self, s):
        """ docstring: 状态栏信息显示 """
        self.statusbar.showMessage(s)

    def viewInfo(self, index):
        """ docstring: 双击条目显示文件内容 """
        filepath = self.fd.getData(index.row(), 1)
        filename = self.fd.getData(index.row(), 0)
        filepid = self.fd.getData(index.row(), 2)
        viewjsonworker = worker(0, self.viewJson, filename, filepath, filepid)
        # TODO: 信息窗显示文件内容。存在bug?
        viewjsonworker.signals.result.connect(self.logText.append)
        self.threadpool.start(viewjsonworker)

    def viewJson(self, filename, filepath, filepid):
        """ docstring: 双击显示Json格式文件 """
        ret = f"<double click> {filename} (SID:{filepid}) = "
        if not os.path.exists(filepath):
            return ret + "本地文件不存在\n"
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                fcontent = ""
                while True:
                    tmp = f.read(512)
                    if not tmp:
                        break
                    fcontent += tmp
                    if len(fcontent) > 512 * 3:
                        return ret + "{...(内容过长)...}\n"
            data = json.loads(fcontent)
        except Exception:
            return ret + "读文件失败\n"
        ret += "\n" + json.dumps(data, sort_keys=True, indent=4, separators=(",", ":")) + "\n"
        return ret

    def timerMessageClear(self):
        """ docstring: 告警窗清空 """
        self.timer_message.stop()
        self.messagebox.done(1)
        self.messagebox = None

    def switchView(self):
        """ docstring: 切换视图按钮 """
        self.switchlistortable ^= 1
        if self.switchlistortable:
            self.listView.hide()
            self.tableView.show()
            self.setStatus("切换到列表视图")
        else:
            self.listView.show()
            self.tableView.hide()
            self.setStatus("切换到图标视图")

    def resetView(self):
        """ docstring: 恢复初始视图格式 """
        if not self.toolBar.toggleViewAction().isChecked():
            self.toolBar.toggleViewAction().trigger()
        self.splitter_horizontal.setSizes([200, 200, 500])
        self.splitter_vertical.setSizes([350, 450])

    def openHub(self):
        """ docstring: 打开本地仓库 """
        if sys.platform == "win32":
            openhubworker = worker(0, os.startfile, HOME_DIR)
        elif sys.platform == "darwin":
            openhubworker = worker(0, os.system, f"open {HOME_DIR}")
        else:
            openhubworker = worker(0, os.system, f"xdg-open {HOME_DIR}")
        self.threadpool.start(openhubworker)

    def openFolder(self):
        """ docstring: 打开所选文件所在文件夹 """
        nowSelectItem = self.selectItems.copy()
        if len(nowSelectItem) == 0:
            self.setStatus("未选中文件")
            return
        if len(nowSelectItem) != 1:
            self.setStatus("选中文件过多")
            return
        # print(nowSelectItem[0])
        tmp = self.fd.getData(nowSelectItem[0], 1)
        # print(tmp)
        if not os.path.exists(tmp) or not tmp:
            self.setStatus("文件不存在")
            return
        filepath = tmp[:tmp.rfind("/")]
        if sys.platform == "win32":
            openfolderworker = worker(0, os.startfile, filepath)
        elif sys.platform == "darwin":
            openfolderworker = worker(0, os.system, f"open {filepath}")
        else:
            openfolderworker = worker(0, os.system, f"xdg-open {filepath}")
        openfolderworker.signals.finished.connect(lambda: self.setStatus("文件已打开"))
        self.threadpool.start(openfolderworker)

    def importData(self):
        """ docstring: 重新读取配置文件。"""
        # TODO: 从后端重新读配置文件，添加保存逻辑
        print("TODO: import data")

    def closeEvent(self, event):
        """ docstring: 关闭窗口时弹出警告 """
        status = QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        reply = QMessageBox.question(self, "警告：是否保存数据", "保存并退出?", status)
        if reply == QMessageBox.Cancel:
            event.ignore()
            return
        if reply == QMessageBox.Yes:
            # 处理保存操作
            self.configdata["topo map"] = self.graphicwindow.saveTopo()
            self.configdata["file data"] = self.fd.save()
            self.datasave()
        self.graphicwindow.close()
        self.cmdwindow = None
        self.videowindow = None
        ic.normal_stop()
        event.accept()

    def datasave(self):
        """ docstring: 保存日志文件 """
        # TODO: 额外保存用户操作以及后端提示信息
        request = {"type": "setconfig", "data": self.configdata}
        ic.put_request(request)

    def updateSID(self, retid, filehash, SID_prefix):
        """ docstring: 计算hash并更新视图 """
        row = self.id2rowmap.pop(retid, 0)
        # 关闭信号接收
        if len(self.id2rowmap) == 0 or self.retidnow == self.retidexpected:
            ic.backendmessage.hashdata.disconnect()
        if row == 0:
            return
        # 修改SID
        filehash = SID_prefix + filehash
        self.fd.setData(row, fd.FileDataEnum.FILEHASH, filehash)
        # 发出数据修改信号
        a = self.tablemodel.createIndex(row, 2)
        self.tablemodel.dataChanged.emit(a, a)
        self.signals.calchashfinished.emit(row)

    def addItem(self):
        """ docstring: 添加条目（单体添加，开额外窗口） """
        def regItem(receivedrow):
            if receivedrow != row:
                return
            else:
                self.signals.calchashfinished.disconnect()
            self.selectItems = [row]
            self.regItem(True)

        self.additemwindow = AddItemWindow(self.fd, self)
        ret = self.additemwindow.exec_()
        row = self.additemwindow.newitemrow
        needReg = self.additemwindow.needReg
        # ret用于判断返回结果
        if ret == 0 or row is None:
            return

        self.modelViewUpdate()
        filename = self.fd.getData(row, fd.FileDataEnum.FILENAME)
        # 添加记录
        self.logWidget.addLog("<添加> 文件或服务", filename, True)
        # 修改高级通告选项显示
        self.graphicwindow.chooseFile.addItem(filename)
        additemworker = worker(0, self.addItem_multi, [row])
        ic.backendmessage.hashdata.connect(lambda x: self.updateSID(**x, SID_prefix=self.NID))
        # 检查是否需要通告
        if needReg:
            self.signals.calchashfinished.connect(regItem)
        self.threadpool.start(additemworker)

    def urlAddItems(self, urls):
        """ docstring: urls批量处理存储 """
        # 添加数据，修改视图，添加log记录
        items = []
        for item_str in urls:
            if os.path.isfile(item_str):
                item = item_str.replace("\\", "/")
                pos = item.rfind("/")
                filename = item[pos + 1:]
                self.fd.addItem(filename=filename, filepath=item)
                items.append(self.fd.rowCount()-1)
                # 刷新数据展示
                self.modelViewUpdate()
                # 添加记录
                self.logWidget.addLog("<添加> 文件或服务", filename, True)
                # 修改高级通告选项显示
                self.graphicwindow.chooseFile.addItem(filename)
        additemworker = worker(0, self.addItem_multi, items)
        ic.backendmessage.hashdata.connect(lambda x: self.updateSID(**x, SID_prefix=self.NID))
        self.threadpool.start(additemworker)

    def addItem_multi(self, nowitems):
        """ docstring: 添加多个文件，修改显示，计算哈希。
            （要求文件条目已经存储到self.fd，此处参数传递为对应待添加文件在self.fd中的行号。暂时不考虑多操作并行冲突情况。） """
        if len(nowitems) == 0:
            return
        self.retidexpected += len(nowitems)
        for row in nowitems:
            # 生成后端请求
            filepath = self.fd.getData(row, fd.FileDataEnum.FILEPATH)
            request = {"type": "additem", "data": {"retid": self.retidnow+1, "filepath": filepath}}
            ic.put_request(request)
            self.id2rowmap[self.retidnow + 1] = row
            self.retidnow += 1

    def delItem(self):
        """ docstring: 删除选中条目（拉起额外线程处理） """
        if len(self.selectItems) == 0:
            self.setStatus("未选中任何条目")
            return
        nowSelectItems = self.selectItems.copy()
        delitemworker = worker(1, self.delItem_multi, nowSelectItems)
        delitemworker.signals.finished.connect(self.modelViewUpdate)
        delitemworker.signals.finished.connect(lambda: self.setStatus("条目已删除"))
        delitemworker.signals.message.connect(self.logWidget.addLog)
        self.threadpool.start(delitemworker)

    def delItem_multi(self, items, message_callback, **kwargs):
        """ docstring: 删除条目线程实际处理函数 """
        items.sort(reverse=True)
        for item in items:
            filename = self.fd.getData(item, fd.FileDataEnum.FILENAME)
            if not filename:
                continue
            # 发送后端消息
            filepath = self.fd.getData(item, fd.FileDataEnum.FILEPATH)
            request = {"type": "delitem", "data": filepath}
            ic.put_request(request)
            # 添加log记录
            message_callback.emit("<删除> 文件或服务", f"file {filename}")
            self.fd.removeItem(item)
            self.graphicwindow.chooseFile.removeItem(item)
            self.selectItems.remove(item)

    def updateProgress(self, row, value):
        """ docstring: 进度条刷新显示函数（返回函数） """
        if self.waitdowitemcount <= 0:
            return
        if value == fd.REG_OR_DOW_COMPLETED:
            self.waitdowitemcount -= 1
            if self.waitdowitemcount == 0:
                ic.backendmessage.dowitemprogress.disconnect()
            self.setStatus("条目已下载")
        self.fd.setData(row, fd.FileDataEnum.ISDOW, value)
        a = self.tablemodel.createIndex(row, fd.FileDataEnum.ISDOW)
        self.tablemodel.dataChanged.emit(a, a)

    def dowItem(self):
        """ docstring: 从远端下载数据（拉起额外线程处理） """
        if len(self.selectItems) == 0:
            self.setStatus("未选中任何条目")
            return
        nowSelectItems = self.selectItems.copy()
        ic.backendmessage.dowitemprogress.connect(lambda x: self.updateProgress(**x))
        self.waitdowitemcount = 0
        dowitemworker = worker(1, self.dowItem_multi, nowSelectItems)
        dowitemworker.signals.finished.connect(lambda: self.setStatus("服务已开始获取"))
        dowitemworker.signals.message.connect(self.logWidget.addLog)
        self.threadpool.start(dowitemworker)

    def dowItem_multi(self, items, message_callback, **kwargs):
        """ docstring: 下载数据线程实际处理函数 """
        for item in items:
            SID = self.fd.getData(item, fd.FileDataEnum.FILEHASH)
            if not SID:
                continue
            filename = self.fd.getData(item, fd.FileDataEnum.FILENAME)
            filepath = self.fd.getData(item, fd.FileDataEnum.FILEPATH)
            request = {"type": "dowitem", "data": {"SID": SID, "filepath": filepath, "row": item}}
            if filename == "video server":
                ic.put_request(request)
                self.waitdowitemcount += 1
                message_callback.emit("<获取> 服务", f"{filename}\n")
                continue
            isDow = self.fd.getData(item, fd.FileDataEnum.ISDOW)
            if isDow == fd.REG_OR_DOW_COMPLETED:
                continue
            ic.put_request(request)
            self.waitdowitemcount += 1
            # 添加log记录
            message_callback.emit("<下载> 文件", f"file {filename}\n")

    def updateReg(self, row, value):
        if value == fd.REG_OR_DOW_COMPLETED:
            if self.waitregitemcount <= 0:
                return
            self.waitregitemcount -= 1
            self.setStatus("条目已通告")
        if value == fd.UNREG_COMPLETED:
            if self.waitunregitemcount <= 0:
                return
            self.waitunregitemcount -= 1
            self.setStatus("条目已取消通告")
        if self.waitregitemcount == 0 and self.waitunregitemcount == 0:
            ic.backendmessage.regitemprogress.disconnect()
        self.fd.setData(row, fd.FileDataEnum.ISREG, value)
        a = self.tablemodel.createIndex(row, fd.FileDataEnum.ISREG)
        self.tablemodel.dataChanged.emit(a, a)

    def regItem(self, flag):
        """ docstring: 文件通告（拉起额外线程处理） """
        if len(self.selectItems) == 0:
            self.setStatus("未选中条目")
            return
        nowSelectItem = self.selectItems.copy()
        ic.backendmessage.regitemprogress.connect(lambda x: self.updateReg(**x))
        regitemworker = worker(1, self.regItem_multi, nowSelectItem, flag)
        regitemworker.signals.message.connect(self.logWidget.addLog)
        self.threadpool.start(regitemworker)

    def advancedRegItem(self, nowSelectItem):
        """ docstring: 高级通告（拉起额外线程处理，单体） """
        if nowSelectItem < 0 or nowSelectItem >= self.fd.rowCount():
            return
        filehash = self.fd.getData(nowSelectItem, fd.FileDataEnum.FILEHASH)
        if not filehash:
            return
        filepath = self.fd.getData(nowSelectItem, fd.FileDataEnum.FILEPATH)
        securitylevel = self.fd.getData(nowSelectItem, fd.FileDataEnum.SECURITYLEVEL)
        whitelist = self.fd.getData(nowSelectItem, fd.FileDataEnum.WHITELIST)
        request = {"type": "regitem", "data": {
            "filepath": filepath, "flag": 1, "row": nowSelectItem}}
        if securitylevel:
            request["data"]["securitylevel"] = int(securitylevel)
        if whitelist:
            request["data"]["whitelist"] = list(map(int, whitelist.split(',')))
        regitemworker = worker(0, ic.put_request, request)
        filename = self.fd.getData(nowSelectItem, fd.FileDataEnum.FILENAME)
        regitemworker.signals.finished.connect(
            lambda: self.logWidget.addLog("<注册> 文件或服务", f"file {filename}\n"))
        self.threadpool.start(regitemworker)

    def regItem_multi(self, items, flag, message_callback, **kwargs):
        """ docstring: 文件通告线程实际处理函数 """
        for item in items:
            filehash = self.fd.getData(item, fd.FileDataEnum.FILEHASH)
            if not filehash:
                continue
            isReg = self.fd.getData(item, fd.FileDataEnum.ISREG)
            if flag and isReg == fd.REG_OR_DOW_COMPLETED or not flag and isReg == fd.UNREG_COMPLETED:
                continue
            filepath = self.fd.getData(item, fd.FileDataEnum.FILEPATH)
            request = {"type": "regitem", "data": {
                "filepath": filepath, "flag": int(flag), "row": item}}
            # 添加log记录
            filename = self.fd.getData(item, fd.FileDataEnum.FILENAME)
            if flag:
                self.waitregitemcount += 1
                message_callback.emit("<注册> 文件或服务", f"file {filename}\n")
            else:
                self.waitunregitemcount += 1
                message_callback.emit("<取消注册> 文件或服务", f"file {filename}\n")
            ic.put_request(request)


if __name__ == "__main__":
    from random import randint
    # import qdarkstyle as qds
    # app.setStyleSheet(qds.load_stylesheet_pyqt5())

    app = QApplication(sys.argv)
    window = MainWindow(QThreadPool(), "a5"*16)
    window.show()

    # 测试收包匹配功能
    window.getPathFromPkt(0x72, "123", [0x11222695], 100,
                          int("b0cd69ef142db5a471676ad710eebf3a", 16))
    window.getPathFromPkt(0x72, "123", [0x33446217, 0x11222695],
                          1500, int("d23454d19f307d8b98ff2da277c0b546", 16))
    window.getPathFromPkt(0x73, "abc", [0x11222695, 0x11221211, 0x33446217, 0x55661234], 1000, 0)
    window.getPathFromPkt(0x173, "abc", [0x11222695, 0x55661234], 1000, 0)
    window.getPathFromPkt(0x173, "abc", [0x11227788], 100, 0)
    window.getPathFromPkt(0x73, "abc", [0x11227788, 0x11227788, 0x33441234, 0x77880000], 100, 0)
    window.getPathFromPkt(0x74, "", [], 20, 0)
    # 测试告警信息显示功能
    window.handleMessageFromPkt(2, "test1\ncontent1\n")
    window.handleMessageFromPkt(2, "test2\ncontent2\n")
    # log添加测试
    for i in range(3):
        window.logWidget.addLog("Hello", f"world{i}", randint(1, 5) == 1)

    sys.exit(app.exec_())
