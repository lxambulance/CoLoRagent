# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'd:\CodeHub\CoLoRagent\PageUI\mainPage.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(850, 700)
        icon = QtGui.QIcon.fromTheme(":/icon/color")
        MainWindow.setWindowIcon(icon)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.filelist_label = QtWidgets.QLabel(self.centralwidget)
        self.filelist_label.setObjectName("filelist_label")
        self.verticalLayout.addWidget(self.filelist_label)
        self.splitter_horizontal = QtWidgets.QSplitter(self.centralwidget)
        self.splitter_horizontal.setOrientation(QtCore.Qt.Vertical)
        self.splitter_horizontal.setObjectName("splitter_horizontal")
        self.tableView = MyTableView(self.splitter_horizontal)
        self.tableView.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.tableView.setObjectName("tableView")
        self.listView = MyListView(self.splitter_horizontal)
        self.listView.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.listView.setObjectName("listView")
        self.splitter_vertical = QtWidgets.QSplitter(self.splitter_horizontal)
        self.splitter_vertical.setOrientation(QtCore.Qt.Horizontal)
        self.splitter_vertical.setObjectName("splitter_vertical")
        self.layoutWidget = QtWidgets.QWidget(self.splitter_vertical)
        self.layoutWidget.setObjectName("layoutWidget")
        self.verticalLayout_1 = QtWidgets.QVBoxLayout(self.layoutWidget)
        self.verticalLayout_1.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_1.setObjectName("verticalLayout_1")
        self.log_label = QtWidgets.QLabel(self.layoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.log_label.sizePolicy().hasHeightForWidth())
        self.log_label.setSizePolicy(sizePolicy)
        self.log_label.setObjectName("log_label")
        self.verticalLayout_1.addWidget(self.log_label)
        self.searchLog = QtWidgets.QLineEdit(self.layoutWidget)
        self.searchLog.setObjectName("searchLog")
        self.verticalLayout_1.addWidget(self.searchLog)
        self.logView = QtWidgets.QWidget(self.layoutWidget)
        self.logView.setObjectName("logView")
        self.verticalLayout_1.addWidget(self.logView)
        self.layoutWidget1 = QtWidgets.QWidget(self.splitter_vertical)
        self.layoutWidget1.setObjectName("layoutWidget1")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.layoutWidget1)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.pktReceive_label = QtWidgets.QLabel(self.layoutWidget1)
        self.pktReceive_label.setObjectName("pktReceive_label")
        self.verticalLayout_2.addWidget(self.pktReceive_label)
        self.dataPktReceive = QtWidgets.QTreeWidget(self.layoutWidget1)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dataPktReceive.sizePolicy().hasHeightForWidth())
        self.dataPktReceive.setSizePolicy(sizePolicy)
        self.dataPktReceive.setObjectName("dataPktReceive")
        self.dataPktReceive.headerItem().setText(0, "文件/包")
        self.dataPktReceive.header().setStretchLastSection(False)
        self.verticalLayout_2.addWidget(self.dataPktReceive)
        self.speed_label = QtWidgets.QLabel(self.layoutWidget1)
        self.speed_label.setObjectName("speed_label")
        self.verticalLayout_2.addWidget(self.speed_label)
        self.speedGraph = PlotWidget(self.layoutWidget1)
        self.speedGraph.setObjectName("speedGraph")
        self.verticalLayout_2.addWidget(self.speedGraph)
        self.verticalLayout.addWidget(self.splitter_horizontal)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 850, 23))
        self.menubar.setObjectName("menubar")
        self.menu = QtWidgets.QMenu(self.menubar)
        self.menu.setObjectName("menu")
        self.menu_2 = QtWidgets.QMenu(self.menubar)
        self.menu_2.setObjectName("menu_2")
        self.menu_3 = QtWidgets.QMenu(self.menubar)
        self.menu_3.setObjectName("menu_3")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QtWidgets.QToolBar(MainWindow)
        self.toolBar.setMinimumSize(QtCore.QSize(16, 16))
        self.toolBar.setObjectName("toolBar")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.action_reg = QtWidgets.QAction(MainWindow)
        self.action_reg.setObjectName("action_reg")
        self.action_undoReg = QtWidgets.QAction(MainWindow)
        self.action_undoReg.setObjectName("action_undoReg")
        self.action_dow = QtWidgets.QAction(MainWindow)
        self.action_dow.setObjectName("action_dow")
        self.action_del = QtWidgets.QAction(MainWindow)
        self.action_del.setObjectName("action_del")
        self.action_hub = QtWidgets.QAction(MainWindow)
        self.action_hub.setObjectName("action_hub")
        self.action_add = QtWidgets.QAction(MainWindow)
        self.action_add.setObjectName("action_add")
        self.action_import = QtWidgets.QAction(MainWindow)
        self.action_import.setObjectName("action_import")
        self.action_openDir = QtWidgets.QAction(MainWindow)
        self.action_openDir.setObjectName("action_openDir")
        self.action_swi = QtWidgets.QAction(MainWindow)
        self.action_swi.setObjectName("action_swi")
        self.action_reset = QtWidgets.QAction(MainWindow)
        self.action_reset.setObjectName("action_reset")
        self.actionWindows = QtWidgets.QAction(MainWindow)
        self.actionWindows.setObjectName("actionWindows")
        self.actionFusion = QtWidgets.QAction(MainWindow)
        self.actionFusion.setObjectName("actionFusion")
        self.actionQdarkstyle = QtWidgets.QAction(MainWindow)
        self.actionQdarkstyle.setObjectName("actionQdarkstyle")
        self.actionwindowsvista = QtWidgets.QAction(MainWindow)
        self.actionwindowsvista.setObjectName("actionwindowsvista")
        self.action_advancedreg = QtWidgets.QAction(MainWindow)
        self.action_advancedreg.setObjectName("action_advancedreg")
        self.action_video = QtWidgets.QAction(MainWindow)
        self.action_video.setObjectName("action_video")
        self.action_cmdline = QtWidgets.QAction(MainWindow)
        self.action_cmdline.setObjectName("action_cmdline")
        self.menu.addAction(self.action_import)
        self.menu.addAction(self.action_swi)
        self.menu.addAction(self.action_reset)
        self.menu.addAction(self.action_hub)
        self.menu.addAction(self.action_video)
        self.menu.addAction(self.action_cmdline)
        self.menu_2.addAction(self.action_add)
        self.menu_2.addAction(self.action_reg)
        self.menu_2.addAction(self.action_advancedreg)
        self.menu_2.addAction(self.action_undoReg)
        self.menu_2.addAction(self.action_dow)
        self.menu_2.addAction(self.action_del)
        self.menu_2.addAction(self.action_openDir)
        self.menu_3.addAction(self.actionWindows)
        self.menu_3.addAction(self.actionwindowsvista)
        self.menu_3.addAction(self.actionFusion)
        self.menu_3.addAction(self.actionQdarkstyle)
        self.menubar.addAction(self.menu.menuAction())
        self.menubar.addAction(self.menu_2.menuAction())
        self.menubar.addAction(self.menu_3.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "CoLoRagent"))
        self.filelist_label.setText(_translate("MainWindow", "文件列表"))
        self.log_label.setText(_translate("MainWindow", "日志消息"))
        self.pktReceive_label.setText(_translate("MainWindow", "收包信息"))
        self.dataPktReceive.headerItem().setText(1, _translate("MainWindow", "大小"))
        self.dataPktReceive.headerItem().setText(2, _translate("MainWindow", "数据"))
        self.speed_label.setText(_translate("MainWindow", "收包速率"))
        self.menu.setTitle(_translate("MainWindow", "菜单"))
        self.menu_2.setTitle(_translate("MainWindow", "编辑"))
        self.menu_3.setTitle(_translate("MainWindow", "主题"))
        self.toolBar.setWindowTitle(_translate("MainWindow", "toolBar"))
        self.action_reg.setText(_translate("MainWindow", "通告"))
        self.action_undoReg.setText(_translate("MainWindow", "取消通告"))
        self.action_dow.setText(_translate("MainWindow", "下载"))
        self.action_del.setText(_translate("MainWindow", "删除"))
        self.action_hub.setText(_translate("MainWindow", "仓库目录"))
        self.action_add.setText(_translate("MainWindow", "添加"))
        self.action_import.setText(_translate("MainWindow", "导入数据"))
        self.action_openDir.setText(_translate("MainWindow", "打开文件夹"))
        self.action_swi.setText(_translate("MainWindow", "切换视图"))
        self.action_reset.setText(_translate("MainWindow", "还原视图"))
        self.actionWindows.setText(_translate("MainWindow", "Windows"))
        self.actionFusion.setText(_translate("MainWindow", "Fusion"))
        self.actionQdarkstyle.setText(_translate("MainWindow", "Qdarkstyle"))
        self.actionwindowsvista.setText(_translate("MainWindow", "WindowsVista"))
        self.action_advancedreg.setText(_translate("MainWindow", "高级通告"))
        self.action_video.setText(_translate("MainWindow", "视频通信"))
        self.action_cmdline.setText(_translate("MainWindow", "命令行（仅测试）"))
from pyqtgraph import PlotWidget
from serviceList import MyListView
from serviceTable import MyTableView
import resource_rc
