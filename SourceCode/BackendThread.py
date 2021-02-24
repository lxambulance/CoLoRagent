from PyQt5.QtCore import QThread, pyqtSignal

class BackendThread(QThread):
    msgSignal = pyqtSignal(msg)
    
    def run(self):
        self.msgSignal.emit("BackendThread base class")
