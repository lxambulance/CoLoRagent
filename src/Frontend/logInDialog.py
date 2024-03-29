# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'd:\codehub\CoLoRagent\PageUI\logInDialog.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(400, 287)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icon/color"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        Dialog.setWindowIcon(icon)
        self.formLayout = QtWidgets.QFormLayout(Dialog)
        self.formLayout.setObjectName("formLayout")
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.formLayout.setItem(0, QtWidgets.QFormLayout.LabelRole, spacerItem)
        self.configpath_label = QtWidgets.QLabel(Dialog)
        self.configpath_label.setObjectName("configpath_label")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.configpath_label)
        self.configpath_horizontalLayout = QtWidgets.QHBoxLayout()
        self.configpath_horizontalLayout.setObjectName("configpath_horizontalLayout")
        self.showpath_config = QtWidgets.QLineEdit(Dialog)
        self.showpath_config.setReadOnly(True)
        self.showpath_config.setObjectName("showpath_config")
        self.configpath_horizontalLayout.addWidget(self.showpath_config)
        self.choosepath_config = QtWidgets.QPushButton(Dialog)
        self.choosepath_config.setMaximumSize(QtCore.QSize(20, 20))
        self.choosepath_config.setObjectName("choosepath_config")
        self.configpath_horizontalLayout.addWidget(self.choosepath_config)
        self.formLayout.setLayout(1, QtWidgets.QFormLayout.FieldRole, self.configpath_horizontalLayout)
        self.agentNID_label = QtWidgets.QLabel(Dialog)
        self.agentNID_label.setObjectName("agentNID_label")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.agentNID_label)
        self.generateNid_horizontalLayout = QtWidgets.QHBoxLayout()
        self.generateNid_horizontalLayout.setObjectName("generateNid_horizontalLayout")
        self.agentNID = QtWidgets.QLineEdit(Dialog)
        self.agentNID.setReadOnly(True)
        self.agentNID.setObjectName("agentNID")
        self.generateNid_horizontalLayout.addWidget(self.agentNID)
        self.generateNid = QtWidgets.QPushButton(Dialog)
        self.generateNid.setMaximumSize(QtCore.QSize(20, 20))
        self.generateNid.setObjectName("generateNid")
        self.generateNid_horizontalLayout.addWidget(self.generateNid)
        self.formLayout.setLayout(2, QtWidgets.QFormLayout.FieldRole, self.generateNid_horizontalLayout)
        self.agentIPv4_label = QtWidgets.QLabel(Dialog)
        self.agentIPv4_label.setObjectName("agentIPv4_label")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.agentIPv4_label)
        self.agentIPv4 = QtWidgets.QLineEdit(Dialog)
        self.agentIPv4.setObjectName("agentIPv4")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.agentIPv4)
        self.filetmp_label = QtWidgets.QLabel(Dialog)
        self.filetmp_label.setObjectName("filetmp_label")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.filetmp_label)
        self.filetmppath_horizontalLayout = QtWidgets.QHBoxLayout()
        self.filetmppath_horizontalLayout.setObjectName("filetmppath_horizontalLayout")
        self.showpath_filetmp = QtWidgets.QLineEdit(Dialog)
        self.showpath_filetmp.setReadOnly(True)
        self.showpath_filetmp.setObjectName("showpath_filetmp")
        self.filetmppath_horizontalLayout.addWidget(self.showpath_filetmp)
        self.choosepath_filetmp = QtWidgets.QPushButton(Dialog)
        self.choosepath_filetmp.setMaximumSize(QtCore.QSize(20, 20))
        self.choosepath_filetmp.setObjectName("choosepath_filetmp")
        self.filetmppath_horizontalLayout.addWidget(self.choosepath_filetmp)
        self.formLayout.setLayout(4, QtWidgets.QFormLayout.FieldRole, self.filetmppath_horizontalLayout)
        self.RMIPv4_label = QtWidgets.QLabel(Dialog)
        self.RMIPv4_label.setObjectName("RMIPv4_label")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.LabelRole, self.RMIPv4_label)
        self.RMIPv4 = QtWidgets.QLineEdit(Dialog)
        self.RMIPv4.setObjectName("RMIPv4")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.FieldRole, self.RMIPv4)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.formLayout.setItem(6, QtWidgets.QFormLayout.LabelRole, spacerItem1)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Close|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName("buttonBox")
        self.formLayout.setWidget(7, QtWidgets.QFormLayout.SpanningRole, self.buttonBox)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "CoLoR代理-登录"))
        self.configpath_label.setText(_translate("Dialog", "配置文件"))
        self.choosepath_config.setToolTip(_translate("Dialog", "选择文件路径"))
        self.choosepath_config.setText(_translate("Dialog", "..."))
        self.agentNID_label.setText(_translate("Dialog", "代理NID"))
        self.generateNid.setToolTip(_translate("Dialog", "随机nid"))
        self.generateNid.setText(_translate("Dialog", "..."))
        self.agentIPv4_label.setText(_translate("Dialog", "代理IPv4"))
        self.filetmp_label.setText(_translate("Dialog", "文件存储目录"))
        self.choosepath_filetmp.setToolTip(_translate("Dialog", "选择存储目录"))
        self.choosepath_filetmp.setText(_translate("Dialog", "..."))
        self.RMIPv4_label.setText(_translate("Dialog", "RM.IPv4"))
import resource_rc
