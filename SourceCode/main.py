# 主调度进程
import ColorMonitor as CM

from PyQt5.QtWidgets import QApplication

from MainWindow import MainWindow

import sys

if __name__ == '__main__':
    thread_monitor = CM.Monitor()
    thread_monitor.start()

    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
