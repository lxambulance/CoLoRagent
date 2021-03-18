# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'd:\CodeHub\ProjectCloud\PageUI\mainPage.ui'
#
# Created by: PyQt5 UI code generator 5.15.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.splitter_2 = QtWidgets.QSplitter(self.centralwidget)
        self.splitter_2.setOrientation(QtCore.Qt.Horizontal)
        self.splitter_2.setObjectName("splitter_2")
        self.treeView = QtWidgets.QTreeView(self.splitter_2)
        self.treeView.setObjectName("treeView")
        self.splitter = QtWidgets.QSplitter(self.splitter_2)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName("splitter")
        self.tableView = MyTableView(self.splitter)
        self.tableView.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.tableView.setObjectName("tableView")
        self.listView = MyListView(self.splitter)
        self.listView.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.listView.setObjectName("listView")
        self.horizontalLayout.addWidget(self.splitter_2)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.pushButton_add = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_add.setObjectName("pushButton_add")
        self.verticalLayout.addWidget(self.pushButton_add)
        self.pushButton_reg = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_reg.setObjectName("pushButton_reg")
        self.verticalLayout.addWidget(self.pushButton_reg)
        self.pushButton_dow = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_dow.setObjectName("pushButton_dow")
        self.verticalLayout.addWidget(self.pushButton_dow)
        self.pushButton_swi = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_swi.setObjectName("pushButton_swi")
        self.verticalLayout.addWidget(self.pushButton_swi)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout.addLayout(self.verticalLayout)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 23))
        self.menubar.setObjectName("menubar")
        self.menu = QtWidgets.QMenu(self.menubar)
        self.menu.setObjectName("menu")
        self.menu_2 = QtWidgets.QMenu(self.menubar)
        self.menu_2.setObjectName("menu_2")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.action_2 = QtWidgets.QAction(MainWindow)
        self.action_2.setObjectName("action_2")
        self.action_3 = QtWidgets.QAction(MainWindow)
        self.action_3.setObjectName("action_3")
        self.action_4 = QtWidgets.QAction(MainWindow)
        self.action_4.setObjectName("action_4")
        self.action_6 = QtWidgets.QAction(MainWindow)
        self.action_6.setObjectName("action_6")
        self.action_cmd = QtWidgets.QAction(MainWindow)
        self.action_cmd.setObjectName("action_cmd")
        self.action_video = QtWidgets.QAction(MainWindow)
        self.action_video.setObjectName("action_video")
        self.action_hub = QtWidgets.QAction(MainWindow)
        self.action_hub.setObjectName("action_hub")
        self.action_1 = QtWidgets.QAction(MainWindow)
        self.action_1.setObjectName("action_1")
        self.action_import = QtWidgets.QAction(MainWindow)
        self.action_import.setObjectName("action_import")
        self.action_5 = QtWidgets.QAction(MainWindow)
        self.action_5.setObjectName("action_5")
        self.menu.addAction(self.action_import)
        self.menu.addAction(self.action_hub)
        self.menu.addAction(self.action_cmd)
        self.menu.addAction(self.action_video)
        self.menu_2.addAction(self.action_1)
        self.menu_2.addSeparator()
        self.menu_2.addAction(self.action_2)
        self.menu_2.addAction(self.action_3)
        self.menu_2.addAction(self.action_4)
        self.menu_2.addAction(self.action_6)
        self.menu_2.addAction(self.action_5)
        self.menubar.addAction(self.menu.menuAction())
        self.menubar.addAction(self.menu_2.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.pushButton_add.setText(_translate("MainWindow", "添加"))
        self.pushButton_reg.setText(_translate("MainWindow", "通告"))
        self.pushButton_dow.setText(_translate("MainWindow", "下载"))
        self.pushButton_swi.setText(_translate("MainWindow", "切换"))
        self.menu.setTitle(_translate("MainWindow", "菜单"))
        self.menu_2.setTitle(_translate("MainWindow", "编辑"))
        self.action_2.setText(_translate("MainWindow", "通告"))
        self.action_3.setText(_translate("MainWindow", "取消通告"))
        self.action_4.setText(_translate("MainWindow", "下载"))
        self.action_6.setText(_translate("MainWindow", "删除"))
        self.action_cmd.setText(_translate("MainWindow", "命令行"))
        self.action_video.setText(_translate("MainWindow", "视频"))
        self.action_hub.setText(_translate("MainWindow", "仓库目录"))
        self.action_1.setText(_translate("MainWindow", "添加"))
        self.action_import.setText(_translate("MainWindow", "导入数据"))
        self.action_5.setText(_translate("MainWindow", "打开文件所在位置"))
from MyListView import MyListView
from MyTableView import MyTableView
import resource_rc
