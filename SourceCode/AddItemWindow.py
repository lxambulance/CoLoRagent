# coding=utf-8
''' docstring: CoLoR Pan 添加条目对话 '''

# 添加文件路径../
import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
sys.path.append(BASE_DIR)

from addItemDialog import Ui_Dialog

from PyQt5.QtCore import *
from PyQt5.QtWidgets import QDialog

class AddItemWindow(QDialog, Ui_Dialog):
    ''' docstring: class addItemDialog '''
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setupUi(self)

        # 设置默认拓扑隐藏
        self.graphwidget.hide()

        # 设置信号与槽连接
        self.mapVisible.stateChanged.connect(self.showMap)

    def showMap(self, s):
        ''' docstring: 实现拓扑图的显示与关闭 '''
        if s == Qt.Checked:
            self.graphwidget.show()
        else:
            self.graphwidget.hide()
