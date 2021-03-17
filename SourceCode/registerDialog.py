# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'd:\CodeHub\ProjectCloud\PageUI\registerDialog.ui'
#
# Created by: PyQt5 UI code generator 5.15.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(1000, 750)
        self.horizontalLayout = QtWidgets.QHBoxLayout(Dialog)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.splitter = QtWidgets.QSplitter(Dialog)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.graphics = GraphWidget(self.splitter)
        self.graphics.setObjectName("graphics")
        self.layoutWidget = QtWidgets.QWidget(self.splitter)
        self.layoutWidget.setObjectName("layoutWidget")
        self.formLayout = QtWidgets.QFormLayout(self.layoutWidget)
        self.formLayout.setContentsMargins(0, 0, 0, 0)
        self.formLayout.setObjectName("formLayout")
        self.label_1 = QtWidgets.QLabel(self.layoutWidget)
        self.label_1.setObjectName("label_1")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_1)
        self.label_2 = QtWidgets.QLabel(self.layoutWidget)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.filePath = QtWidgets.QLabel(self.layoutWidget)
        self.filePath.setObjectName("filePath")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.filePath)
        self.label_3 = QtWidgets.QLabel(self.layoutWidget)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_3)
        self.fileHash = QtWidgets.QLabel(self.layoutWidget)
        self.fileHash.setObjectName("fileHash")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.fileHash)
        self.label_4 = QtWidgets.QLabel(self.layoutWidget)
        self.label_4.setObjectName("label_4")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.label_4)
        self.fileAddtion = QtWidgets.QLabel(self.layoutWidget)
        self.fileAddtion.setObjectName("fileAddtion")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.fileAddtion)
        self.label_5 = QtWidgets.QLabel(self.layoutWidget)
        self.label_5.setObjectName("label_5")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.label_5)
        self.needReg = QtWidgets.QCheckBox(self.layoutWidget)
        self.needReg.setText("")
        self.needReg.setObjectName("needReg")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.needReg)
        self.label_6 = QtWidgets.QLabel(self.layoutWidget)
        self.label_6.setObjectName("label_6")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.LabelRole, self.label_6)
        self.isDow = QtWidgets.QLabel(self.layoutWidget)
        self.isDow.setObjectName("isDow")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.FieldRole, self.isDow)
        self.label_7 = QtWidgets.QLabel(self.layoutWidget)
        self.label_7.setObjectName("label_7")
        self.formLayout.setWidget(6, QtWidgets.QFormLayout.LabelRole, self.label_7)
        self.regArgs = QtWidgets.QTextEdit(self.layoutWidget)
        self.regArgs.setReadOnly(True)
        self.regArgs.setObjectName("regArgs")
        self.formLayout.setWidget(6, QtWidgets.QFormLayout.FieldRole, self.regArgs)
        self.saveButton = QtWidgets.QPushButton(self.layoutWidget)
        self.saveButton.setObjectName("saveButton")
        self.formLayout.setWidget(7, QtWidgets.QFormLayout.LabelRole, self.saveButton)
        self.showSave = QtWidgets.QLabel(self.layoutWidget)
        self.showSave.setObjectName("showSave")
        self.formLayout.setWidget(7, QtWidgets.QFormLayout.FieldRole, self.showSave)
        self.fileName = QtWidgets.QLabel(self.layoutWidget)
        self.fileName.setObjectName("fileName")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.fileName)
        self.horizontalLayout.addWidget(self.splitter)
        self.label_7.setBuddy(self.regArgs)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
        Dialog.setTabOrder(self.graphics, self.regArgs)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label_1.setText(_translate("Dialog", "文件名"))
        self.label_2.setText(_translate("Dialog", "文件路径"))
        self.filePath.setText(_translate("Dialog", "TextLabel"))
        self.label_3.setText(_translate("Dialog", "文件哈希"))
        self.fileHash.setText(_translate("Dialog", "TextLabel"))
        self.label_4.setText(_translate("Dialog", "文件描述"))
        self.fileAddtion.setText(_translate("Dialog", "TextLabel"))
        self.label_5.setText(_translate("Dialog", "添加到通告包"))
        self.label_6.setText(_translate("Dialog", "是否下载"))
        self.isDow.setText(_translate("Dialog", "TextLabel"))
        self.label_7.setText(_translate("Dialog", "通告参数"))
        self.saveButton.setText(_translate("Dialog", "保存修改"))
        self.showSave.setText(_translate("Dialog", "TextLabel"))
        self.fileName.setText(_translate("Dialog", "TextLabel"))
from GraphWidget import GraphWidget
