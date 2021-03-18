# coding=utf-8
''' docstring: my list view '''

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class MyListView(QListView):
    ''' docstring: class MyListView '''
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
