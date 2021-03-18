# coding=utf-8
''' docstring: main program '''

import sys

import ColorMonitor as CM

from PyQt5.QtWidgets import QApplication

from MainWindow import MainWindow

if __name__ == '__main__':
    thread_monitor = CM.Monitor()
    thread_monitor.setDaemon(True)
    thread_monitor.start()

    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
