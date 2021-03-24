# coding=utf-8
''' docstring: 主程序 '''

import sys

import ColorMonitor as CM

from PyQt5.QtWidgets import QApplication

from MainWindow import MainWindow

if __name__ == '__main__':
    CM.PL.Nid = 1 # 初始化本机NID
    
    thread_monitor = CM.Monitor()
    thread_monitor.setDaemon(True)
    thread_monitor.start()

    CM.PL.AnnProxy()# 向RM注册本代理

    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
