# coding=utf-8
''' docstring: 主程序 '''

import sys
import qdarkstyle as qds
import ColorMonitor as CM
import MainWindow as mw
from logInWindow import logInWindow
from PyQt5.QtWidgets import QApplication, QStyleFactory

# import time

try:
    # Include in try/except block if you're also targeting Mac/Linux
    from PyQt5.QtWinExtras import QtWin
    myappid = 'mycompany.myproduct.subproduct.version'
    QtWin.setCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass


class CoLoRApp(QApplication):
    ''' docstring: CoLoR应用类 '''

    def __init__(self, argv):
        ''' docstring: 初始化应用 '''
        super().__init__(argv)
        self.setStyle('Fusion')

        self.loginwindow = logInWindow()
        self.loginwindow.show()

        # 设置信号与槽连接
        self.loginwindow.buttonBox.accepted.connect(self.start_main)

    def start_main(self):
        # 初始化本终端信息
        CM.PL.IPv4 = self.loginwindow.myIPv4
        CM.PL.Nid = int('0x'+self.loginwindow.myNID, 16)
        CM.PL.rmIPv4 = self.loginwindow.rmIPv4
        mw.HOME_DIR = self.loginwindow.filetmppath
        mw.DATA_PATH = self.loginwindow.configpath
        # print(f'before HOME_DIR{mw.HOME_DIR} DATA_PATH{mw.DATA_PATH}')
        self.window = mw.MainWindow()
        self.window.actionWindows.triggered.connect(self._setStyle)
        self.window.actionwindowsvista.triggered.connect(self._setStyle)
        self.window.actionFusion.triggered.connect(self._setStyle)
        self.window.actionQdarkstyle.triggered.connect(self._setStyle)
        self.window.show()
        thread_monitor = CM.Monitor(
            message = app.window.handleMessageFromPkt,
            path = app.window.getPathFromPkt
        )
        thread_monitor.setDaemon(True)
        thread_monitor.start()
        # CM.PL.RegFlag=1
        # time.sleep(2)
        # CM.PL.AddCacheSidUnit('F:\\ProjectCloud\\test\\testfile1.txt',1,1,1,1)
        # CM.PL.SidAnn()
        # time.sleep(2)
        # SID = hex(CM.PL.Nid).replace('0x', '').zfill(32) + CM.PL.Sha1Hash('F:\\ProjectCloud\\test\\testfile1.txt')
        # CM.PL.Get(SID, 'F:\\ProjectCloud\\test.txt')

    def _setStyle(self):
        ''' docstring: 切换格式 '''
        # 取消qss格式
        self.setStyleSheet('')
        # self.window.graphics_global.setBackground('#eee5ff')
        self.window.speedGraph.setBackground('w')
        # 获取信号发起者名称，前6位为action，后面是相应主题名
        tmp = self.sender().objectName()[6:]
        # print(tmp)
        if tmp in QStyleFactory.keys():
            self.setStyle(tmp)
        elif tmp == 'Qdarkstyle':
            self.setStyleSheet(qds.load_stylesheet_pyqt5())
            # self.window.graphics_global.setBackground('#4d4d4d')
            self.window.speedGraph.setBackground('#000000')
        else:
            self.window.showStatus('该系统下没有 主题 <' + tmp + '>')

if __name__ == '__main__':
    app = CoLoRApp(sys.argv)
    sys.exit(app.exec_())
