# coding=utf-8
''' docstring: service list model to handle data '''

# 添加文件路径../
import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
sys.path.append(BASE_DIR)

from PyQt5.QtWidgets import *
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
            value = self.services.getData(index.row(), 0)
            if value.find('.') == -1:
                return QIcon(':/icon/rar')
            else:
                return QIcon(':/icon/document')

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Vertical:
                return 'r' + str(section+1)

    def rowCount(self, index):
        return self.services.rowCount()

    def flags(self, index):
        default = super().flags(index)
        if index.isValid():
            return Qt.ItemIsDropEnabled | Qt.ItemIsDragEnabled | default
        else:
            return Qt.ItemIsDropEnabled | default
    
    def supportedDropActions(self):
        return Qt.CopyAction | Qt.MoveAction

class MyListView(QListView):
    ''' docstring: class MyListView '''
    signal_select = pyqtSignal(object)
    signal_add = pyqtSignal(object)
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(self.ExtendedSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(self.DragDrop)
        self.setMovement(self.Snap)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super().dragEnterEvent(event)
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            super().dragMoveEvent(event)
    
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
            urls = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    urls.append(url.toLocalFile())
            self.signal_add.emit(urls)
        else:
            super().dropEvent(event)

    def mouseReleaseEvent(self, event):
        mouseBtn = event.button()
        if mouseBtn == Qt.MouseButton.RightButton or mouseBtn == Qt.MouseButton.LeftButton:
            items = self.selectionModel().selectedRows()
            self.signal_select.emit(list(items))
        super().mouseReleaseEvent(event)
