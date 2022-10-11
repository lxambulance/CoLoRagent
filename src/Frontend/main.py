# coding=utf-8
""" docstring: 主程序 """


import sys
import qdarkstyle as qds
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QApplication, QStyleFactory


import Backend.ColorMonitor as CM
import Backend.establishSecureSession as ESS
import Frontend.MainWindow as mw
from Frontend.logInWindow import logInWindow


try:
    # Include in try/except block if you're also targeting Mac/Linux
    from PyQt5.QtWinExtras import QtWin
    myappid = 'mycompany.myproduct.subproduct.version'
    QtWin.setCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass


class CoLoRApp(QApplication):
    """ docstring: CoLoR应用类 """

    def __init__(self, argv):
        """ docstring: 初始化应用 """
        super().__init__(argv)
        self.setStyle('Fusion')

        self.setQuitOnLastWindowClosed(True)
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

        self.window = mw.MainWindow(self.loginwindow.myNID)
        ESS.ESSsignal.output.connect(self.window.handleMessageFromPkt)
        self.window.actionWindows.triggered.connect(self._setStyle)
        self.window.actionwindowsvista.triggered.connect(self._setStyle)
        self.window.actionFusion.triggered.connect(self._setStyle)
        self.window.actionQdarkstyle.triggered.connect(self._setStyle)
        self.window.show()
        # 连接后端信号槽
        thread_monitor = CM.Monitor(
            message=app.window.handleMessageFromPkt,
            path=app.window.getPathFromPkt
        )
        # thread_monitor.setDaemon(True)
        thread_monitor.daemon = True
        thread_monitor.start()

        # 测试
        CM.PL.RegFlag = 1
        # nid = "b0cd69ef142db5a471676ad710eebf3a"
        # CM.PL.PeerProxys[int(nid, 16)]='192.168.56.1'
        nid = "d23454d19f307d8b98ff2da277c0b546"
        CM.PL.PeerProxys[int(nid, 16)]='192.168.56.2'
        # time.sleep(2)
        # Sql provider
        # CM.PL.AddCacheSidUnit(3,1,1,1,1)
        # CM.PL.SidAnn()
        # Sql customer
        # CM.GetSql(nid, "SELECT * from employee;")

    def _setStyle(self):
        """ docstring: 切换qss格式 """
        # 取消qss格式
        self.setStyleSheet('')
        self.window.graphicwindow.setStyleSheet('')
        # 获取信号发起者名称，前6位为action，后面是相应主题名
        tmp = self.sender().objectName()[6:]
        if tmp in QStyleFactory.keys():
            self.setStyle(tmp)
        elif tmp == 'Qdarkstyle':
            self.setStyleSheet(qds.load_stylesheet_pyqt5())
            self.window.graphicwindow.setStyleSheet(
                qds.load_stylesheet_pyqt5())
        else:
            self.window.showStatus('该系统下没有 主题 <' + tmp + '>')
        color = self.window.palette().color(QPalette.Background).name()
        color = '#ffffff' if color == '#f0f0f0' else color
        self.window.graphicwindow.graphics_global.setBackground(
            "#6d6d6d" if tmp == 'Qdarkstyle' else color)  # 455364
        self.window.speedGraph.setBackground(color)


if __name__ == '__main__':
    # import os
    # os.environ['PYQTGRAPH_QT_LIB'] = 'PyQt5'
    # os.environ['QT_API'] = 'pyqt5'

    app = CoLoRApp(sys.argv)
    sys.exit(app.exec_())
