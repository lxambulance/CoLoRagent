# coding=utf-8
''' docstring: 主程序 '''

import sys

import ColorMonitor as CM

from PyQt5.QtWidgets import QApplication

from MainWindow import MainWindow

import time

if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()

    # 初始化本终端信息
    CM.PL.IPv4 = '10.0.0.5'
    CM.PL.Nid = 0x11111111111111111111111111111110

    thread_monitor = CM.Monitor(window.handleMessageFromPkt)
    thread_monitor.setDaemon(True)
    thread_monitor.start()
    
    # time.sleep(2)
    # CM.PL.AddCacheSidUnit('F:\\ProjectCloud\\test\\testfile1.txt',1,1,1,1)
    # CM.PL.SidAnn()
    # time.sleep(2)
    # SID = hex(CM.PL.Nid).replace('0x', '').zfill(32) + CM.PL.Sha1Hash('F:\\ProjectCloud\\test\\testfile1.txt')
    # CM.PL.Get(SID, 'F:\\ProjectCloud\\test.txt')
    
    window.show()
    sys.exit(app.exec_())
