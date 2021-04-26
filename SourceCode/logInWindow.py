# coding=utf-8
''' docstring: CoLoR 登录对话 '''

from PyQt5.QtWidgets import QDialog, QApplication, QFileDialog
from logInDialog import Ui_Dialog
import os
import sys
import json
BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))).replace('\\', '/')
DATAPATH = BASE_DIR + '/data.db'
sys.path.append(BASE_DIR)


class logInWindow(QDialog, Ui_Dialog):
    ''' docstring: 登录窗口类 '''

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        if not os.path.exists(DATAPATH):
            self.configpath = None
            self.filetmppath = None
            self.myNID = None
        else:
            self.autoFillForm(DATAPATH)
        # 设置信号与槽连接
        self.choosepath_config.clicked.connect(self.getConfigPath)
        self.choosepath_filetmp.clicked.connect(self.getFiletmpPath)

    def autoFillForm(self, path):
        self.configpath = path
        self.showpath_config.setText(self.configpath)
        with open(self.configpath, 'r') as f:
            __raw_data = json.load(f)
            self.filetmppath = __raw_data.get('filetmppath', None)
            self.showpath_filetmp.setText(self.filetmppath)
            self.myNID = __raw_data.get('myNID', None)
            self.agentNID.setText(self.myNID)

    def getConfigPath(self):
        configpath = QFileDialog.getOpenFileName(self, '请选择配置文件', BASE_DIR)
        if configpath[0] and configpath[0][-3:] == '.db':
            self.autoFillForm(configpath[0])

    def getFiletmpPath(self):
        filetmppath = QFileDialog.getExistingDirectory(
            self, '请选择存储目录', BASE_DIR)
        if filetmppath:
            self.filetmppath = filetmppath
            self.showpath_filetmp.setText(self.filetmppath)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = logInWindow()
    window.show()
    sys.exit(app.exec_())
