# coding=utf-8
''' docstring: CoLoR Pan 命令行页 '''

# 添加文件路径../
import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
sys.path.append(BASE_DIR)

from PageUI.cmdlinePage import Ui_Form

from PyQt5.QtWidgets import QWidget

class CmdlineWindow(QWidget, Ui_Form):
    ''' docstring: class CmdlineWindow '''
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setupUi(self)
