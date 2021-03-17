# coding=utf-8
''' docstring: service table model to handle data '''

# 添加文件路径../
import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
sys.path.append(BASE_DIR)

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
            return str(value)

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
