# coding=utf-8
''' docstring: CoLoR Pan 视频页 '''

# 添加文件路径../
import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
sys.path.append(BASE_DIR)

from PageUI.videoPage import Ui_Form

from PyQt5.QtWidgets import QWidget

class VideoWindow(QWidget, Ui_Form):
    ''' docstring: class VideoWindow '''
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setupUi(self)
