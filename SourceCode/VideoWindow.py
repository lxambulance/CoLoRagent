# coding=utf-8
''' docstring: CoLoR Pan 视频页 '''

from videoPage import Ui_Form

from PyQt5.QtWidgets import QWidget

class VideoWindow(QWidget, Ui_Form):
    ''' docstring: class VideoWindow '''
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setupUi(self)
