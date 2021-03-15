# coding=utf-8
''' docstring: CoLoR Pan 命令行页 '''

from cmdlinePage import Ui_Form

from PyQt5.QtWidgets import QWidget

class CmdlineWindow(QWidget, Ui_Form):
    ''' docstring: class CmdlineWindow '''
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setupUi(self)
