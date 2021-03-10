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
from serviceTableModel import serviceTableModel
from serviceListModel import serviceListModel
import FileData
from worker import worker

class MainWindow(QMainWindow, Ui_MainWindow):
    ''' docstring: class MainWindow '''

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # 添加右键菜单
        for i in range(5):
            eval('self.listView.addAction(self.action_'+str(i+1)+')')
            eval('self.tableView.addAction(self.action_'+str(i+1)+')')
        
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
        self.pushButton_1.clicked.connect(self.addItem)
        self.action_1.triggered.connect(self.addItem)
        self.pushButton_3.clicked.connect(self.switchView)
        self.action_cmd.triggered.connect(self.openCmdLinePage)
        self.action_video.triggered.connect(self.openVideoPage)
        self.action_hub.triggered.connect(self.openHub)
        self.action_import.triggered.connect(self.importData)
        self.listView.clicked.connect(self.clickItem)
        self.tableView.clicked.connect(self.clickItem)
        self.listView.doubleClicked.connect(self.doubleClickItem)
        self.tableView.doubleClicked.connect(self.doubleClickItem)

    def addItem(self):
        ''' docstring: 按下添加按钮 '''
        self.additemwindow = AddItemWindow()
        ret = self.additemwindow.exec_()
        # ret 可用于后续判断返回结果
        print('additemwindow return', ret)

    def switchView(self):
        ''' docstring: 切换视图按钮 '''
        if self.switchlistortable:
            self.listView.hide()
            self.tableView.show()
            self.statusBar().showMessage('切换到列表视图')
        else:
            self.listView.show()
            self.tableView.hide()
            self.statusBar().showMessage('切换到图标视图')
        self.switchlistortable ^= 1

    def openHub(self):
        ''' docstring: 打开本地仓库 '''
        self.openHubWorker = worker(0, os.startfile, HOME_DIR)
        self.threadpool.start(self.openHubWorker)

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
            self.model1.layoutChanged.emit()
            self.model2.layoutChanged.emit()

    def clickItem(self, index):
        ''' docstring: 选中条目 '''
        self.selectItem = index.row()
        self.statusBar().showMessage('选中条目' + str(self.selectItem + 1))

    def doubleClickItem(self, index):
        ''' docstring: 双击条目 '''
        result = self.fd.getItem(self.selectItem)
        QMessageBox.information(self, 'info', str(result))

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
