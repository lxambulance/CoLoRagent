# coding: utf-8
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from time import sleep
from pathlib import Path
import PyQt5
from PyQt5 import QtWidgets, QtGui, QtCore
from PageUI.mainPage import Ui_MainWindow
import PageUI.cmdlinePage
import PageUI.videoPage

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.statusBar().showMessage('就绪') # 状态栏
        self.selectItem = None # 保存选择对象
        self.home_dir = str(Path.cwd()).replace('\\','/') + '/.tmp'
        if not os.path.exists(self.home_dir):
            os.makedirs(self.home_dir)
        # print(self.home_dir)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.contextMenu = QtWidgets.QMenu(self)
        self.actionA = self.contextMenu.addAction('注册')
        self.actionD = self.contextMenu.addAction('取消注册')
        self.actionB = self.contextMenu.addAction('下载')
        self.actionE = self.contextMenu.addAction('取消下载')
        self.actionC = self.contextMenu.addAction('删除')

        self.customContextMenuRequested.connect(self.showContextMenu)
        self.ui.treeWidget.itemClicked.connect(self.onItemClicked)
        self.ui.treeWidget.itemDoubleClicked.connect(self.onItemDoubleClicked)
        self.ui.pushButton.clicked.connect(self.addItemsShowDialog)
        self.ui.pushButton_3.clicked.connect(self.announceItems)
        self.ui.pushButton_4.clicked.connect(self.importItems)
        self.ui.pushButton_5.clicked.connect(self.getItemsData)
        self.actionA.triggered.connect(self.announceItem)
        self.actionB.triggered.connect(self.getItemData)
        self.actionC.triggered.connect(self.delItem)
        self.actionD.triggered.connect(self.undoAnnounceItem)
        self.actionE.triggered.connect(self.undoGetItem)
        self.ui.action.triggered.connect(self.openConfigFile)
        self.ui.action_2.triggered.connect(self.openCmdLine)
        self.ui.action_3.triggered.connect(self.openVideo)
        
    # 打开仓库
    def openConfigFile(self):
        print('Open')
        os.startfile(self.home_dir)

    # 打开命令行
    def openCmdLine(self):
        self.clui = cmdlinePage.Ui_Form()
        self.clui.setupUi(self.clui)
        self.clui.show()

    # 打开视频页面
    def openVideo(self):
        self.vui = videoPage.Ui_Form()
        self.vui.setupUi(self.vui)
        self.vui.show()

    # 撤销通告包
    def undoAnnounceItem(self):
        if self.selectItem == None or self.selectItem.text(1) == '否':
            return
        print('undo ANN')
        self.selectItem.setText(1, '否')

    # 撤销本地缓存
    def undoGetItem(self):
        if self.selectItem == None or self.selectItem.text(2) == '否':
            return
        print('undo Get')
        self.selectItem.setText(2, '否')
        self.selectItem.setText(3, '...')

    # 删除item
    def delItem(self):
        if self.selectItem is None:
            return
        size = window.ui.treeWidget.topLevelItemCount()
        for i in range(size):
            item = window.ui.treeWidget.topLevelItem(i)
            if item == self.selectItem:
                window.ui.treeWidget.takeTopLevelItem(i)
                self.statusBar().showMessage('就绪')
                return

    # 显示右键菜单栏
    def showContextMenu(self, pos):
        # print(pos, QtGui.QCursor.pos())
        self.contextMenu.exec_(QtGui.QCursor.pos())
        # self.statusBar().showMessage('选中 ' + self.selectItem.text(0))

    # 单击items选中
    def onItemClicked(self, item):
        self.selectItem = item # 获取所选中的文件名
        self.statusBar().showMessage('选中 ' + item.text(0))

    # 双击items显示信息
    def onItemDoubleClicked(self, item):
        # print(item, item.text(0))
        s = ''
        if item.text(2) == '是':
            with open(item.text(3), 'r', encoding='utf-8') as f:
                tmp = f.read(50)
                s += tmp
                # print(tmp)
                f.close()
        QtWidgets.QMessageBox.information(self, 'info', s)

    # 添加文件
    def addItemsShowDialog(self):
        fpath = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', self.home_dir)
        if fpath[0]:
            # print(fpath[0], fpath[0].split('/'))
            fname = fpath[0].split('/')[-1]
            QtWidgets.QTreeWidgetItem(window.ui.treeWidget, [fname, '否', '是', fpath[0]])

    # 注册单个文件
    def announceItem(self):
        if self.selectItem is None or self.selectItem.text(1) == '是':
            return
        print('start anouncing item', self.selectItem)
        self.announcement(self.selectItem)
        
    # 注册多个文件
    def announceItems(self):
        print('start anouncing items')
        size = window.ui.treeWidget.topLevelItemCount()
        for i in range(size):
            item = window.ui.treeWidget.topLevelItem(i)
            if item.text(1) == '否':
                print(item.text(0))
                self.announcement(item)

    # 注册过程本体
    def announcement(self, item):
        if item.text(2) == '否':
            return
        sleep(1)
        # 计算sid，发送ann包
        item.setText(1, '是')
        self.statusBar().showMessage('注册 ' + item.text(0) + ' 完成')

    # 获取单个文件数据
    def getItemData(self):
        if self.selectItem is None or self.selectItem.text(2) == '是':
            return
        print('start getting item data', self.selectItem)
        self.getData(self.selectItem)
        
    # 获取多个文件数据
    def getItemsData(self):
        print('start getting items data')
        size = window.ui.treeWidget.topLevelItemCount()
        for i in range(size):
            item = window.ui.treeWidget.topLevelItem(i)
            if item.text(2) == '否':
                print(item.text(0))
                self.getData(item)

    # 获取数据本体
    def getData(self, item):
        if item.text(1) == '否':
            return
        sleep(1)
        # 计算sid，发送get包，收取data包
        item.setText(2, '是')
        fpath = self.home_dir+'/'+item.text(0)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write('Hello World!')
            f.close()
        item.setText(3, fpath)
        self.statusBar().showMessage('下载 ' + item.text(0) + ' 完成')

    # 主窗体关闭事件
    def closeEvent(self, event):
        self.saveConfig(self.home_dir + '/config.txt')
        # reply = QtWidgets.QMessageBox.question(self, '警告：记得保存配置', '确认退出?', QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        # if reply == QtWidgets.QMessageBox.Yes:
        #     event.accept() #关闭窗口
        # else:
        #     event.ignore() #忽视点击X事件
    
    # 导入其他配置文件
    def importItems(self):
        fpath = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', self.home_dir)
        if fpath[0]:
            self.readConfig(fpath[0])

    # 保存配置文件
    def saveConfig(self, name):
        with open(name, 'w', encoding='utf-8') as f:
            f.write('lxambulance\n')
            size = self.ui.treeWidget.topLevelItemCount()
            f.write(str(size) + '\n')
            for i in range(size):
                item = self.ui.treeWidget.topLevelItem(i)
                s = ''
                for j in range(4):
                    s = s + item.text(j) + ' '
                s = s[0:-1] + '\n'
                f.write(s)
            f.close()

    # 读取配置文件
    def readConfig(self, name):
        if not os.path.exists(name):
            print(name + '不存在')
            return
        with open(name, 'r', encoding='utf-8') as f:
            if f.readline() != 'lxambulance\n' :
                print('This is not a correct configuration.')
                f.close()
                return
            size = int(f.readline().strip(' \n'))
            while (size):
                size -= 1
                litem = list(f.readline().strip('\n').split(' '))
                QtWidgets.QTreeWidgetItem(self.ui.treeWidget, litem)
            f.close()
        
if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.readConfig(window.home_dir + '/config.txt')
    window.show()
    sys.exit(app.exec_())
