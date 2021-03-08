# coding=utf-8
''' docstring: service list model to handle data '''

# 添加文件路径../
import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
sys.path.append(BASE_DIR)

from PyQt5.QtCore import *
from PyQt5.QtGui import *

import FileData

class serviceListModel(QAbstractListModel):
    ''' docstring: service model class '''
    def __init__(self, filedata, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.services = filedata

    def data(self, index, role):
        ''' docstring: main function to get data as a role '''
        if role == Qt.DisplayRole:
            value = self.services.getData(index.row())
            return str(value)

        if role == Qt.DecorationRole:
            value = self.services.getData(index.row(), 1)
            if (value&1) == 1:
                return QIcon(':/icon/folder.png')
            else:
                return QIcon(':/icon/document.png')

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Vertical:
                return 'r' + str(section+1)

    def rowCount(self, index):
        return self.services.rowCount()

    def flags(self, index):
        return Qt.ItemIsDragEnabled | super().flags(index)
