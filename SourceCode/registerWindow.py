# coding=utf-8
''' docstring: CoLoR Pan 通告对话 '''

from registerDialog import Ui_Dialog

from PyQt5.QtWidgets import QDialog
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import resource_rc

from FileData import FileData
from PointLine import Node, Line
import math

class registerWindow(QDialog, Ui_Dialog):
    ''' docstring: class RegisterWindow '''
    def __init__(self, filedata, fileindex, parent = None):
        super().__init__(parent)
        self.setupUi(self)

        self.fd = filedata
        self.id = fileindex
        self.returnValue = (None)
        # TODO: 将fileName改成一个comboBox
        self.fileName.setText(str(self.fd.getData(self.id)))
        self.filePath.setText(str(self.fd.getData(self.id, 1)))
        self.fileHash.setText(str(self.fd.getData(self.id, 2)))
        self.regArgs.setText('-N 0\n-L 0\n-I 0\n')
        # TODO: 文件描述暂无
        self.fileAddtion.setText('暂无')

        isReg = self.fd.getData(self.id, 3)
        if isReg:
            self.isReg.setPixmap(QPixmap(':/icon/tick'))
        else:
            self.isReg.setPixmap(QPixmap(':/icon/cross'))
        isDow = self.fd.getData(self.id, 4)
        if isDow:
            self.isDow.setPixmap(QPixmap(':/icon/tick'))
        else:
            # 不属于本地的文件没有通告权
            self.isDow.setPixmap(QPixmap(':/icon/cross'))
            self.graphics.hide()
        
        self.timer = QTimer()
        self.showSave.setPixmap(QPixmap(':/icon/minus'))

        # 设置图形显示比例
        self.splitter.setSizes([600, 250])

        # 人工设置拓扑图
        self.node = [0] * 5
        for i in range(5):
            self.node[i] = Node()
            self.graphics.scene().addItem(self.node[i])
            a = math.pi * 2 / 5
            R = 250
            x, y = round(math.cos(a*3/4+a*i) * R), round(math.sin(a*3/4+a*i) * R)
            self.node[i].setPos(x, y)
        self.line = [0] * 5
        for i in range(5):
            j = (i + 2) % 5
            self.line[i] = Line(self.node[i],self.node[j],self.graphics)
            self.graphics.scene().addItem(self.line[i])

        # 设置信号与槽连接
        self.saveButton.clicked.connect(self.checkDataChange)
        self.timer.timeout.connect(self.changeSaveShow)

    def checkDataChange(self):
        self.showSave.setPixmap(QPixmap(':/icon/tick'))
        self.timer.setInterval(1500)
        self.timer.start()
        # TODO: 通告参数检查与返回
    
    def changeSaveShow(self):
        self.timer.stop()
        self.showSave.setPixmap(QPixmap(':/icon/minus'))

if __name__ == '__main__':
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    import sys
    fd = FileData()
    fd.load()
    app = QApplication(sys.argv)
    window = registerWindow(fd, 0)
    window.show()
    app.exec_()
