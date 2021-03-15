# coding=utf-8
''' docstring: CoLoR Pan 注册对话 '''

from registerDialog import Ui_Dialog

from PyQt5.QtWidgets import QDialog

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
        self.fileName.setText(str(self.fd.getData(self.id)))
        self.filePath.setText(str(self.fd.getData(self.id, 1)))
        # todo: 文件描述暂无
        self.fileAddtion.setText('无')
        
        # 设置图形显示
        self.splitter.setSizes([700, 250])

        # 人工设置拓扑图
        self.node = [0] * 5
        for i in range(5):
            self.node[i] = Node()
            self.graphics.scene().addItem(self.node[i])
            a = math.pi * 2 / 5
            R = 300
            x, y = round(math.cos(a*3/4+a*i) * R), round(math.sin(a*3/4+a*i) * R)
            self.node[i].setPos(x, y)
        self.line = [0] * 5
        for i in range(5):
            j = (i + 2) % 5
            self.line[i] = Line(self.node[i],self.node[j],self.graphics)
            self.graphics.scene().addItem(self.line[i])

if __name__ == '__main__':
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    import sys
    fd = FileData()
    fd.load()
    app = QApplication(sys.argv)
    window = registerWindow(fd, 3)
    window.show()
    app.exec_()
