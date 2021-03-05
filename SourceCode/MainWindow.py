# coding=utf-8
''' docstring: CoLoR Pan主页 '''

# 添加文件路径../
import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
sys.path.append(BASE_DIR)

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from PageUI.mainPage import Ui_MainWindow

from serviceTableModel import serviceTableModel
from serviceListModel import serviceListModel
import FileData

class MainWindow(QMainWindow, Ui_MainWindow):
    ''' docstring: class MainWindow '''

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # 添加右键菜单
        for i in range(5):
            eval('self.listView.addAction(self.action_'+str(i+1)+')')
            eval('self.tableView.addAction(self.action_'+str(i+1)+')')
        
        # 使用自定义模型
        test = [[1,2,1,2],[2,1,2,1],[1,2,1,2],[2,1,2,1]]
        self.fd = FileData.FileData(test)
        self.model1 = serviceListModel(self.fd)
        self.model2 = serviceTableModel(self.fd)

        # 设置模型对应的view
        self.treeView.hide()
        self.listView.setModel(self.model1)
        self.listView.setViewMode(self.listView.IconMode)
        self.tableView.setModel(self.model2)

        # 设置listview(0)与tableview(1)的视图转换
        self.switchlistortable = 1
        self.tableView.hide()

        # 设置信号与槽的连接
        self.pushButton_3.clicked.connect(self.switchView)

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

if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
