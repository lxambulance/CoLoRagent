# coding=utf-8
''' docstring: CoLoR Pan 添加条目对话 '''

# 添加文件路径../
import os
import sys
__BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
sys.path.append(__BASE_DIR)
HOME_DIR = __BASE_DIR + '/.tmp'
from shutil import copyfile

from addItemDialog import Ui_Dialog

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import FileData
import resource_rc
import sys

class AddItemWindow(QDialog, Ui_Dialog):
    ''' docstring: class addItemDialog '''
    def __init__(self, filedata, parent = None):
        super().__init__(parent)
        self.setupUi(self)
        self.fd = filedata
        self.newitemrow = None
        self.addtionText.setText('(请输入附加说明文字)')

        # 设置信号槽与信号的连接
        self.choosePath.clicked.connect(self.chooseFilePath)
        self.buttonBox.accepted.connect(self.addItem)
    
    def chooseFilePath(self):
        fpath = QFileDialog.getOpenFileName(self, 'Open file', HOME_DIR)
        if fpath[0]:
            # print(fpath[0], fpath[0].split('/'))
            nametmplist = fpath[0].split('/')
            self.fileName.setText(nametmplist[-1])
            self.addtionText.setText('(请输入附加说明文字)')
            self.choosePath.setText(fpath[0])
    
    def addItem(self):
        ''' docstring: 添加文件项到数据库结构 '''
        a = self.fileName.text()
        if a == '':
            print('没有待添加文件')
            return
        b = self.choosePath.text()
        # 考虑到异步拷贝后续步骤可能出错，这里阻塞窗口。TODO: 处理异步
        if self.needCopy.checkState():
            try:
                copyfile(b, HOME_DIR + '/' + a)
            except IOError:
                print("Unable to copy file %s" % a)
            else:
                b = HOME_DIR + '/' + a

        ctmp = self.addtionText.document().toRawText()
        c = ctmp.split('(')[0]
        c += ctmp.split(')')[1]
        self.fd.setItem(filename = a, filepath = b, fileadd = c,
                        needReg = int(self.needRegister.checkState() > 0))
        self.newitemrow = self.fd.rowCount()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    fd = FileData.FileData()
    window = AddItemWindow(fd)
    window.show()
    app.exec_()
