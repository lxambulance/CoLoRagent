# coding=utf-8
""" docstring: CoLoR拓扑图窗口 """


from PyQt5.QtCore import QObject, Qt, pyqtSignal
from PyQt5.QtWidgets import QMainWindow

from ui_GraphicPage import Ui_MainWindow
from GraphicsItem import Node, Edge, Text


class GraphicSignals(QObject):
    """ docstring: 拓扑图专用信号组 """
    hide_window_signal = pyqtSignal(bool)
    message_signal = pyqtSignal(int, str)
    advencedRegrow_signal = pyqtSignal(int)


class GraphicWindow(QMainWindow, Ui_MainWindow):
    """ docstring: CoLoR拓扑图窗口类 """

    def __init__(self, fd, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.fd = fd
        self.GS = GraphicSignals()
        self.graphics_global.setMessageSignal(self.GS.message_signal)
        self.flagModifyTopo = False

        # 暂时隐藏部分按钮
        self.actionModifyTopo.setVisible(False)
        self.pushButtonModifyTopo.setVisible(False)
        self.showModifyButton(False)
        self.showAdvancedReg(False)
        # 初始化不开启工具栏
        self.Toolbar.setVisible(False)

        # 设置禁止自添加
        self.nodelist.setAcceptDrops(False)

        # 设置信号槽连接
        self.actionReopenToolbar.triggered.connect(self.resetToolbar) # 设置按钮还原工具栏
        self.pushButtonModifyTopo.clicked.connect(self.showModifyButton)
        self.pushButtonAdvancedReg.clicked.connect(self.showAdvancedReg)
        self.pushButtonShowBaseinfo.clicked.connect(self.showInfoText)
        self.pushButtonShowASThroughput.clicked.connect(self.graphics_global.showThroughput)
        self.pushButtonShowNode.clicked.connect(lambda x:self.nodelist.setVisible(x))
        self.actionModifyTopo.triggered.connect(self.pushButtonModifyTopo.click) # 将动作与对应按钮绑定
        self.actionAdvancedReg.triggered.connect(self.pushButtonAdvancedReg.click)
        self.actionShowBaseinfo.triggered.connect(self.pushButtonShowBaseinfo.click)
        self.actionShowASThroughput.triggered.connect(self.pushButtonShowASThroughput.click)
        # 通告信号相关
        self.chooseFile.currentIndexChanged.connect(self.showAdvancedRegrow)
        self.secretLevel.valueChanged[int].connect(
            lambda x:self.changeAdvancedReg(self.chooseFile.currentIndex(), level=x)
        )
        self.ASlist.returnPressed.connect(
            lambda:self.changeAdvancedReg(self.chooseFile.currentIndex(),
            whitelist=self.ASlist.text())
        )
        self.pushButtonChooseAS.clicked.connect(self.chooseASs)
        self.pushButtonReg.clicked.connect(
            lambda:self.GS.advencedRegrow_signal.emit(self.chooseFile.currentIndex())
        )
        # 自定义内部信号
        self.GS.message_signal.connect(self.messageTest)
        # 拓扑修改信号
        self.pushButtonSetColor.clicked.connect(self.textSetColor)
        self.pushButtonSetFont.clicked.connect(self.textSetFont)
        self.pushButtonDelete.clicked.connect(self.delItem)

    def textSetColor(self, flag):
        if not self.graphics_global.view.selectedText:
            return
        self.graphics_global.view.selectedText.changeColor()
    
    def textSetFont(self, flag):
        if not self.graphics_global.view.selectedText:
            return
        self.graphics_global.view.selectedText.changeFont()

    def delItem(self, flag):
        if self.graphics_global.view.selectedItem:
            if isinstance(self.graphics_global.view.selectedItem, Node):
                self.graphics_global.view.removeNode(self.graphics_global.view.selectedItem)
            elif isinstance(self.graphics_global.view.selectedItem, Edge):
                self.graphics_global.view.removeEdge(self.graphics_global.view.selectedItem)
            self.graphics_global.view.selectedItem = None
            self.GS.message_signal.emit(2, "信息显示框")

    def showInfoText(self, flag):
        """ docstring: 显示基础信息框 """
        if flag:
            self.graphics_global.scene.baseinfo.show()
            self.graphics_global.view.resetNodeInfoPos()
        else:
            self.graphics_global.scene.baseinfo.hide()

    def resetToolbar(self):
        """ docstring: 还原工具栏位置，采用删除后重填加的方式 """
        self.removeDockWidget(self.Toolbar)
        if not self.Toolbar.isVisible(): # visible是自身属性，可以直接修改
            self.Toolbar.toggleViewAction().trigger()
        self.addDockWidget(Qt.DockWidgetArea(Qt.RightDockWidgetArea), self.Toolbar)
        if self.Toolbar.isFloating(): # floating属性涉及到外部dock位置，需要先确定父widget
            self.Toolbar.setFloating(False)

    def closeEvent(self, event):
        """ docstring: 自定义关闭事件信号 """
        self.GS.hide_window_signal.emit(False)
        if self.Toolbar.isFloating():
            self.removeDockWidget(self.Toolbar)
        super().closeEvent(event)

    def keyPressEvent(self, event):
        """ docstring: 自定义键盘按事件 """
        key = event.key()
        if key == Qt.Key_M:
            self.flagModifyTopo = not self.flagModifyTopo
            self.actionModifyTopo.setVisible(self.flagModifyTopo)
            self.pushButtonModifyTopo.setVisible(self.flagModifyTopo)
    
    def showModifyButton(self, flag):
        """ docstring: 显示拓扑修改相关按钮 """
        # print(flag) # 测试输出
        self.pushButtonAddSolidLine.setVisible(flag)
        self.pushButtonAddDottedLine.setVisible(flag)
        self.pushButtonEdit.setVisible(flag)
        self.pushButtonDelete.setVisible(flag)
        self.pushButtonSetFont.setVisible(flag)
        self.pushButtonReset.setVisible(flag)
        self.pushButtonSetColor.setVisible(flag)
        self.pushButtonShowNode.setVisible(flag)
        self.nodelist.setVisible(flag and self.pushButtonShowNode.isChecked())
        self.line2.setVisible(flag)

    def showAdvancedReg(self, flag):
        """ docstring: 显示高级通告相关按钮 """
        self.chooseFile.setVisible(flag)
        self.secretLevel.setVisible(flag)
        self.ASlist.setVisible(flag)
        self.pushButtonChooseAS.setVisible(flag)
        self.pushButtonReg.setVisible(flag)
        self.line3.setVisible(flag)

    def messageTest(self, mType, message):
        """ docstring: 测试消息信号 """
        if mType == 1:
            self.setStatus(message)
        elif mType == 2:
            self.graphics_global.scene.baseinfo.changeText(message)
            self.graphics_global.view.resetNodeInfoPos()
        else:
            print("unexpected message<", mType, ">", message)

    def loadTopo(self, configdata):
        """ docstring: 载入拓扑 """
        if configdata is None:
            return
        self.graphics_global.scene.initTopo(configdata)
        self.graphics_global.view.scaleView(0.45)

    def saveTopo(self):
        """ docstring: 保存拓扑 """
        return self.graphics_global.scene.saveTopo()

    def showAdvancedRegrow(self, row):
        """ docstring: 高级通告条目切换 """
        if row<0 and row>=self.chooseFile.count():
            return
        level = self.fd.getData(row, 5)
        self.secretLevel.setValue(int(level) if level else 1)
        whitelist = self.fd.getData(row, 6)
        self.ASlist.setText(whitelist if whitelist else "")
        # TODO: 如何避免下面的蠢方法
        self.keepVisible(self.Toolbar.isVisible())
    
    def keepVisible(self, flag):
        self.Toolbar.setVisible(flag)

    def changeAdvancedReg(self, nowSelectItem, level=None, whitelist=None):
        """ docstring: 修改高级通告策略 """
        if nowSelectItem<0 or nowSelectItem>=self.fd.rowCount():
            return
        newItem = self.fd.getItem(nowSelectItem)
        while len(newItem)<7:
            newItem.append(None)
        if level != None:
            newItem[5] = level
            self.fd.setItem(nowSelectItem, newItem)
        if whitelist != None:
            newItem[6] = whitelist
            self.fd.setItem(nowSelectItem, newItem)

    def setStatus(self, s):
        """ docstring: 状态栏信息显示 """
        self.statusBar.showMessage(s)

    def chooseASs(self, flag):
        """docstring: 高级通告选择 """
        row = self.chooseFile.currentIndex()
        # print(row, flag)
        if row == -1:
            self.setStatus('请选择高级通告条目')
            self.pushButtonChooseAS.setChecked(False)
            return
        if flag:
            self.ASlist.setToolTip('确认选择完毕')
            self.graphics_global.startChooseAS(self.ASlist.text())
        else:
            self.ASlist.setToolTip('在图中选择通告路径')
            ret = self.graphics_global.endChooseAS()
            self.ASlist.setText(ret)
            self.changeAdvancedReg(row, whitelist=ret)


if __name__ == "__main__":
    """ 模块测试将所有能开启的按钮全部打开，方便展示 """

    from PyQt5.QtWidgets import QApplication
    import os
    import sys

    __BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
    app = QApplication([])
    from FileData import FileData
    fd = FileData()
    window = GraphicWindow(fd)
    window.show()
    DATAPATH = __BASE_DIR+"/data.json"
    window.loadTopo(DATAPATH)    
    window.actionReopenToolbar.trigger()
    window.pushButtonAdvancedReg.click()
    window.pushButtonShowBaseinfo.click()
    window.pushButtonShowASThroughput.click()
    from PyQt5.QtCore import QCoreApplication
    from PyQt5.QtGui import QGuiApplication, QKeyEvent, QFont, QColor
    QCoreApplication.postEvent(window,
        QKeyEvent(QKeyEvent.KeyPress, Qt.Key_M, QGuiApplication.keyboardModifiers()))
    window.pushButtonModifyTopo.click()
    window.pushButtonShowNode.click()
    
    window.chooseFile.addItem("testfile")
    ret = app.exec_()
    # window.saveTopo(DATAPATH)
    sys.exit(ret)
