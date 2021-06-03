# coding=utf-8
''' docstring: service table model to handle data '''

# 添加文件路径../
import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
sys.path.append(BASE_DIR)

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import FileData

COLUMN = ['文件名', '路径', 'SID', '是否通告', '是否下载']

class serviceTableModel(QAbstractTableModel):
    ''' docstring: service table model class '''
    def __init__(self, filedata, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.services = filedata

    def data(self, index, role):
        ''' docstring: main function to get data as a role'''
        if role == Qt.DisplayRole:
            value = self.services.getData(index.row(), index.column())
            if index.column() >= 3:
                return str(value)+'%'
            elif index.column() == 2:
                tmpret = str(value)
                tmpret = 'n_sid:' + tmpret[:32] + '\nl_sid:' + tmpret[32:]
                return tmpret
            else:
                return str(value)
        elif role == Qt.FontRole:
            if index.column() == 2:
                return QFont("New Times Roman", 10)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(COLUMN[section])
            if orientation == Qt.Vertical:
                return str(section + 1)

    def rowCount(self, index):
        return self.services.rowCount()

    def columnCount(self, index):
        return len(COLUMN)

class progressBarDelegate(QStyledItemDelegate):
    ''' docstring: 模型进度条代理 '''
    def __init__(self, parent = None):
        super().__init__(parent)
        self.parent = parent

    def paint(self, painter, option, index):
        if index.column() == 3 or index.column() == 4:
            pid = index.row() * len(COLUMN) + index.column()
            progress = int(index.data().replace('%',''))
            if not (pid in self.parent.progressbarpool):
                progressbar = QStyleOptionProgressBar()
                self.parent.progressbarpool[pid] = progressbar
                progressbar.minimum = 0
                progressbar.maximum = 100
                progressbar.textVisible = True
            else:
                progressbar = self.parent.progressbarpool[pid]
            progressbar.rect = option.rect
            progressbar.progress = progress
            progressbar.text = str(progress) + '%'
            QApplication.style().drawControl(QStyle.CE_ProgressBar, progressbar, painter)
        else:
            return super().paint(painter, option, index)

class MyTableView(QTableView):
    ''' docstring: class MyTableView '''
    signal_select = pyqtSignal(object)
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(self.ExtendedSelection)
        self.setSortingEnabled(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # self.horizontalHeader().setStretchLastSection(True)
    
    def mouseReleaseEvent(self, event):
        mouseBtn = event.button()
        if mouseBtn == Qt.MouseButton.RightButton or mouseBtn == Qt.MouseButton.LeftButton:
            items = self.selectionModel().selectedRows()
            self.signal_select.emit(list(items))
        super().mouseReleaseEvent(event)
