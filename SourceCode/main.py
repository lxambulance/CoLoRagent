# coding=utf-8
''' docstring: 主程序 '''

import sys

import ColorMonitor as CM

from MainWindow import MainWindow, CoLoRApp

# import time

try:
    # Include in try/except block if you're also targeting Mac/Linux
    from PyQt5.QtWinExtras import QtWin
    myappid = 'mycompany.myproduct.subproduct.version'
    QtWin.setCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass

if __name__ == '__main__':
    # 初始化本终端信息
    CM.PL.IPv4 = '10.0.0.5'
    CM.PL.Nid = 0x11111111111111111111111111111110

    app = CoLoRApp(sys.argv)

    thread_monitor = CM.Monitor(app.window.handleMessageFromPkt)
    thread_monitor.setDaemon(True)
    thread_monitor.start()

    # time.sleep(2)
    # CM.PL.AddCacheSidUnit('F:\\ProjectCloud\\test\\testfile1.txt',1,1,1,1)
    # CM.PL.SidAnn()
    # time.sleep(2)
    # SID = hex(CM.PL.Nid).replace('0x', '').zfill(32) + CM.PL.Sha1Hash('F:\\ProjectCloud\\test\\testfile1.txt')
    # CM.PL.Get(SID, 'F:\\ProjectCloud\\test.txt')

    sys.exit(app.exec_())
