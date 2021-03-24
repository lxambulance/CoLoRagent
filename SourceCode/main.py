# coding=utf-8
''' docstring: 主程序 '''

import sys

import ColorMonitor as CM

from PyQt5.QtWidgets import QApplication

from MainWindow import MainWindow

if __name__ == '__main__':
    # 启动监听线程
    thread_monitor = CM.Monitor()
    thread_monitor.setDaemon(True)
    thread_monitor.start()
    # 主线程拉起窗口并阻塞
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
