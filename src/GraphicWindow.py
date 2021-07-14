# coding=utf-8
''' docstring: CoLoR拓扑图窗口 '''

from PyQt5.QtCore import QObject, Qt, pyqtSignal
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QMainWindow, QPushButton

from GraphicPage import Ui_MainWindow


class GraphicSignal(QObject):
    ''' docstring: 拓扑图专用信号返回 '''
    hide_window_signal = pyqtSignal(bool)

class GraphicWindow(QMainWindow, Ui_MainWindow):
    ''' docstring: CoLoR拓扑图窗口类 '''

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.GS = GraphicSignal()
        self.flagModifyTopo = False

        # 暂时隐藏部分按钮
        self.actionModifyTopo.setVisible(False)
        self.pushButtonModifyTopo.setVisible(False)
        self.showModifyButton(False)
        self.showAdvancedReg(False)

        # 设置禁止自添加
        self.nodelist.setAcceptDrops(False)

        # 设置信号槽连接
        self.actionReopenToolbar.triggered.connect(self.resetToolbar) # 设置按钮还原工具栏
        self.pushButtonModifyTopo.clicked.connect(self.showModifyButton)
        self.pushButtonAdvancedReg.clicked.connect(self.showAdvancedReg)
        self.actionModifyTopo.triggered.connect(self.pushButtonModifyTopo.click) # 将动作与对应按钮绑定
        self.actionAdvancedReg.triggered.connect(self.pushButtonAdvancedReg.click)
        self.actionShowBaseinfo.triggered.connect(self.pushButtonShowBaseinfo.click)
        self.actionShowASThroughput.triggered.connect(self.pushButtonShowASThroughput.click)

    def resetToolbar(self):
        ''' docstring: 还原工具栏位置，采用删除后重填加的方式 '''
        self.removeDockWidget(self.Toolbar)
        if not self.Toolbar.isVisible(): # visible是自身属性，可以直接修改
            self.Toolbar.toggleViewAction().trigger()
        self.addDockWidget(Qt.DockWidgetArea(Qt.RightDockWidgetArea), self.Toolbar)
        if self.Toolbar.isFloating(): # floating属性涉及到外部dock位置，需要先确定父widget
            self.Toolbar.setFloating(False)

    def closeEvent(self, event):
        ''' docstring: 自定义关闭事件信号 '''
        self.GS.hide_window_signal.emit(False)
        super().closeEvent(event)

    def keyPressEvent(self, event):
        ''' docstring: 自定义键盘按事件 '''
        key = event.key()
        if key == Qt.Key_M:
            if not self.pushButtonModifyTopo.isChecked():
                self.flagModifyTopo = not self.flagModifyTopo
                self.actionModifyTopo.setVisible(self.flagModifyTopo)
                self.pushButtonModifyTopo.setVisible(self.flagModifyTopo)
    
    def showModifyButton(self, flag):
        ''' docstring: 显示拓扑修改相关按钮 '''
        print(flag)
        self.pushButtonAddSolidLine.setVisible(flag)
        self.pushButtonAddDottedLine.setVisible(flag)
        self.pushButtonEdit.setVisible(flag)
        self.pushButtonDelete.setVisible(flag)
        self.pushButtonReset.setVisible(flag)
        self.nodelist.setVisible(flag)
        self.line2.setVisible(flag)

    def showAdvancedReg(self, flag):
        ''' docstring: 显示高级通告相关按钮 '''
        self.chooseFile.setVisible(flag)
        self.secretLevel.setVisible(flag)
        self.ASlist.setVisible(flag)
        self.pushButtonChooseAS.setVisible(flag)
        self.pushButtonReg.setVisible(flag)
        self.line3.setVisible(flag)


if __name__ == "__main__":
    import sys

    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    window = GraphicWindow()
    DATAPATH = "D:/CodeHub/CoLoRagent/data.db"
    # window.graphics_global.loadTopo(DATAPATH)
    window.show()
    
    # 新节点类型测试
    from NodeEdge import Text
    tmp = Text("Hello World")
    window.graphics_global.scene.addItem(tmp)

    ret = app.exec_()
    window.graphics_global.saveTopo(DATAPATH)
    sys.exit(ret)
