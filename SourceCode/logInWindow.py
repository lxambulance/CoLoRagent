# coding=utf-8
''' docstring: CoLoR 登录对话 '''

from PyQt5.QtWidgets import QDialog, QApplication, QFileDialog
from logInDialog import Ui_Dialog
import os
import sys
import json
BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))).replace('\\', '/')
DATA_PATH = BASE_DIR + '/data.db'
HOME_DIR = BASE_DIR + '/.tmp'
sys.path.append(BASE_DIR)


class logInWindow(QDialog, Ui_Dialog):
    ''' docstring: 登录窗口类 '''

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        if not os.path.exists(DATA_PATH):
            self.configpath = None
            self.filetmppath = None
            self.myNID = None
            self.myIPv4 = None
        else:
            self.autoFillForm(DATA_PATH)
            self.filetmppath = HOME_DIR
            self.showpath_filetmp.setText(HOME_DIR)
        # 设置信号与槽连接
        self.choosepath_config.clicked.connect(self.getConfigPath)
        self.choosepath_filetmp.clicked.connect(self.getFiletmpPath)
        self.buttonBox.accepted.connect(self.checkInput)
        self.agentNID.textChanged.connect(self.setNID)
        self.agentIPv4.textChanged.connect(self.setIPv4)

    def setNID(self, text):
        self.myNID = text

    def setIPv4(self, text):
        self.myIPv4 = text

    def checkInput(self):
        ''' docstring: TODO 验证输入合法性 '''
        flag = True
        pass
        if flag:
            with open(self.configpath, 'r') as f:
                __raw_data = json.load(f)
            __raw_data['filetmppath'] = self.filetmppath
            __raw_data['myNID'] = self.myNID
            __raw_data['myIPv4'] = self.myIPv4
            with open(self.configpath, 'w') as f:
                json.dump(__raw_data, f)

    def autoFillForm(self, path):
        ''' docstring: 根据*.db文件内容填写表单剩余项 '''
        self.configpath = path
        self.showpath_config.setText(self.configpath)
        with open(self.configpath, 'r') as f:
            __raw_data = json.load(f)
            self.filetmppath = __raw_data.get('filetmppath', None)
            self.showpath_filetmp.setText(self.filetmppath)
            self.myNID = __raw_data.get('myNID', None)
            self.agentNID.setText(self.myNID)
            self.myIPv4 = __raw_data.get('myIPv4', None)
            self.agentIPv4.setText(self.myIPv4)

    def getConfigPath(self):
        configpath = QFileDialog.getOpenFileName(self, '请选择配置文件', BASE_DIR)
        if configpath[0] and configpath[0][-3:] == '.db':
            self.autoFillForm(configpath[0])

    def getFiletmpPath(self):
        filetmppath = QFileDialog.getExistingDirectory(self, '请选择存储目录', BASE_DIR)
        if filetmppath:
            self.filetmppath = filetmppath
            self.showpath_filetmp.setText(self.filetmppath)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = logInWindow()
    window.show()
    sys.exit(app.exec_())

'''
f = open('./test/datatest_human.db','w')
json.dump(a,f, indent=4, sort_keys=True, separators=(',', ':'))
f.close()
'''
