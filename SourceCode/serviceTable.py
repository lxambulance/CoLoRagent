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
            if index.column() == 4:
                return str(value)+'%'
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
                return '条目' + str(section + 1)

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
    signal = pyqtSignal(int)
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
    
    def mouseReleaseEvent(self, event):
        mouseBtn = event.button()
        if mouseBtn == Qt.MouseButton.RightButton or mouseBtn == Qt.MouseButton.LeftButton:
            rows = self.selectionModel().selectedRows()
            if len(rows):
                self.signal.emit(rows[0].row())
            else:
                self.signal.emit(-1)
        super().mouseReleaseEvent(event)
