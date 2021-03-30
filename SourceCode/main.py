# coding=utf-8
''' docstring: 主程序 '''

import sys

import ColorMonitor as CM

from PyQt5.QtWidgets import QApplication

from MainWindow import MainWindow

if __name__ == '__main__':
    # 初始化本终端信息
    CM.PL.IPv4 = '192.168.50.219'
    CM.PL.Nid = 1

    thread_monitor = CM.Monitor()
    thread_monitor.setDaemon(True)
    thread_monitor.start()
    
    # 向RM发送注册报文
    # CM.PL.AnnProxy()
    
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
