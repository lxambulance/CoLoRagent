# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'd:\codehub\CoLoRagent\PageUI\GraphicsPage.ui'
#
# Created by: PyQt5 UI code generator 5.15.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(700, 700)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icon/color"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.graphics_global = GraphicWindow(self.centralwidget)
        self.graphics_global.setObjectName("graphics_global")
        self.horizontalLayout.addWidget(self.graphics_global)
        MainWindow.setCentralWidget(self.centralwidget)
        self.toolBar = QtWidgets.QToolBar(MainWindow)
        self.toolBar.setObjectName("toolBar")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.actiona = QtWidgets.QAction(MainWindow)
        self.actiona.setObjectName("actiona")
        self.actionb = QtWidgets.QAction(MainWindow)
        self.actionb.setObjectName("actionb")
        self.actionc = QtWidgets.QAction(MainWindow)
        self.actionc.setObjectName("actionc")
        self.actiond = QtWidgets.QAction(MainWindow)
        self.actiond.setObjectName("actiond")
        self.actione = QtWidgets.QAction(MainWindow)
        self.actione.setObjectName("actione")
        self.toolBar.addAction(self.actiona)
        self.toolBar.addAction(self.actionb)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionc)
        self.toolBar.addAction(self.actiond)
        self.toolBar.addAction(self.actione)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "网络拓扑"))
        self.toolBar.setWindowTitle(_translate("MainWindow", "toolBar"))
        self.actiona.setText(_translate("MainWindow", "a"))
        self.actionb.setText(_translate("MainWindow", "b"))
        self.actionc.setText(_translate("MainWindow", "c"))
        self.actiond.setText(_translate("MainWindow", "d"))
        self.actione.setText(_translate("MainWindow", "e"))
from GraphicWindow import GraphicWindow
import resource_rc