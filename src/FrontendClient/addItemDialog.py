# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'd:\CodeHub\CoLoRagent\PageUI\addItemDialog.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(500, 300)
        self.horizontalLayout = QtWidgets.QHBoxLayout(Dialog)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.tabWidget = QtWidgets.QTabWidget(Dialog)
        self.tabWidget.setObjectName("tabWidget")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.formLayout_2 = QtWidgets.QFormLayout(self.tab_2)
        self.formLayout_2.setObjectName("formLayout_2")
        self.label_6 = QtWidgets.QLabel(self.tab_2)
        self.label_6.setObjectName("label_6")
        self.formLayout_2.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_6)
        self.inputFileName = QtWidgets.QLineEdit(self.tab_2)
        self.inputFileName.setObjectName("inputFileName")
        self.formLayout_2.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.inputFileName)
        self.label_7 = QtWidgets.QLabel(self.tab_2)
        self.label_7.setObjectName("label_7")
        self.formLayout_2.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.label_7)
        self.inputSID = QtWidgets.QLineEdit(self.tab_2)
        self.inputSID.setObjectName("inputSID")
        self.formLayout_2.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.inputSID)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.formLayout_2.setItem(0, QtWidgets.QFormLayout.LabelRole, spacerItem)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.formLayout_2.setItem(4, QtWidgets.QFormLayout.LabelRole, spacerItem1)
        self.label = QtWidgets.QLabel(self.tab_2)
        self.label.setObjectName("label")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label)
        self.filetypeChoose = QtWidgets.QComboBox(self.tab_2)
        self.filetypeChoose.setObjectName("filetypeChoose")
        self.filetypeChoose.addItem("")
        self.filetypeChoose.addItem("")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.filetypeChoose)
        self.tabWidget.addTab(self.tab_2, "")
        self.tab_1 = QtWidgets.QWidget()
        self.tab_1.setObjectName("tab_1")
        self.formLayout = QtWidgets.QFormLayout(self.tab_1)
        self.formLayout.setObjectName("formLayout")
        self.label_1 = QtWidgets.QLabel(self.tab_1)
        self.label_1.setObjectName("label_1")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_1)
        self.fileName = QtWidgets.QLineEdit(self.tab_1)
        self.fileName.setObjectName("fileName")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.fileName)
        self.label_2 = QtWidgets.QLabel(self.tab_1)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.choosePath = QtWidgets.QPushButton(self.tab_1)
        self.choosePath.setObjectName("choosePath")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.choosePath)
        self.label_3 = QtWidgets.QLabel(self.tab_1)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_3)
        self.addtionText = QtWidgets.QTextEdit(self.tab_1)
        self.addtionText.setObjectName("addtionText")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.addtionText)
        self.label_4 = QtWidgets.QLabel(self.tab_1)
        self.label_4.setObjectName("label_4")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.label_4)
        self.needRegister = QtWidgets.QCheckBox(self.tab_1)
        self.needRegister.setText("")
        self.needRegister.setObjectName("needRegister")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.needRegister)
        self.label_5 = QtWidgets.QLabel(self.tab_1)
        self.label_5.setObjectName("label_5")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.label_5)
        self.needCopy = QtWidgets.QCheckBox(self.tab_1)
        self.needCopy.setText("")
        self.needCopy.setObjectName("needCopy")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.needCopy)
        self.tabWidget.addTab(self.tab_1, "")
        self.horizontalLayout.addWidget(self.tabWidget)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Vertical)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.horizontalLayout.addWidget(self.buttonBox)
        self.label_7.setBuddy(self.inputSID)
        self.label_1.setBuddy(self.fileName)
        self.label_2.setBuddy(self.choosePath)
        self.label_3.setBuddy(self.addtionText)
        self.label_4.setBuddy(self.needRegister)
        self.label_5.setBuddy(self.needCopy)

        self.retranslateUi(Dialog)
        self.tabWidget.setCurrentIndex(0)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label_6.setText(_translate("Dialog", "文件名"))
        self.label_7.setText(_translate("Dialog", "SID"))
        self.label.setText(_translate("Dialog", "类型"))
        self.filetypeChoose.setItemText(0, _translate("Dialog", "普通文件"))
        self.filetypeChoose.setItemText(1, _translate("Dialog", "视频流服务"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("Dialog", "从网络添加"))
        self.label_1.setText(_translate("Dialog", "文件名"))
        self.label_2.setText(_translate("Dialog", "文件路径"))
        self.choosePath.setText(_translate("Dialog", "..."))
        self.label_3.setText(_translate("Dialog", "文件说明"))
        self.label_4.setText(_translate("Dialog", "是否通告"))
        self.label_5.setText(_translate("Dialog", "是否拷贝到主目录"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_1), _translate("Dialog", "从本地添加"))