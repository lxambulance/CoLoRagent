# coding=utf-8
""" docstring: 主程序 """


import signal
import qdarkstyle as qds
import MainWindow as mw
import InnerConnection as ic
from logInWindow import logInWindow

from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QApplication, QStyleFactory
from PyQt5.QtCore import QThreadPool


try:
    from PyQt5.QtWinExtras import QtWin
    # appid = 'company.product.subproduct.version'
    appid = 'zeusnet.color.coloragent.v3.0'
    QtWin.setCurrentProcessExplicitAppUserModelID(appid)
except ImportError:
    print("Not Windows System")
    pass


class CoLoRApp(QApplication):
    """ docstring: CoLoR应用类 """

    def _setStyle(self):
        """ docstring: 切换应用界面风格（改qss文件） """
        # 取消qss格式
        self.setStyleSheet('')
        self.window.graphicwindow.setStyleSheet('')
        # 获取信号发起者名称，前6位为action，后面是相应主题名
        tmp = self.sender().objectName()[6:]
        if tmp in QStyleFactory.keys():
            self.setStyle(tmp)
        elif tmp == 'Qdarkstyle':
            self.setStyleSheet(qds.load_stylesheet_pyqt5())
            self.window.graphicwindow.setStyleSheet(qds.load_stylesheet_pyqt5())
        else:
            self.window.showStatus('该系统下没有 主题 <' + tmp + '>')
        color = self.window.palette().color(QPalette.Background).name()
        color = '#ffffff' if color == '#f0f0f0' else color
        self.window.graphicwindow.graphics_global.setBackground(
            "#6d6d6d" if tmp == 'Qdarkstyle' else color)  # 455364
        self.window.speedGraph.setBackground(color)

    def __init__(self, argv, threadpool):
        """ docstring: 初始化应用，打开开始界面 """
        super().__init__(argv)
        self.threadpool = threadpool

        # 设置界面格式
        self.setStyle('Fusion')
        # 设置窗口退出模式
        self.setQuitOnLastWindowClosed(True)
        # 开启登录界面
        self.loginwindow = logInWindow(threadpool)
        self.loginwindow.show()

        # 设置登录界面跳转信号/槽连接
        self.loginwindow.buttonBox.accepted.connect(self.start_main)

        # 设置结束信号操作
        signal.signal(signal.SIGTERM, self.stop_main)
        signal.signal(signal.SIGINT, self.stop_main)

    def start_main(self):
        # 未连接到后端禁止启动
        if ic.server_key is None:
            return

        # 初始化本终端信息
        # CM.PL.IPv4 = self.loginwindow.myIPv4
        # CM.PL.Nid = int('0x'+self.loginwindow.myNID, 16)
        # CM.PL.rmIPv4 = self.loginwindow.rmIPv4
        mw.HOME_DIR = self.loginwindow.filetmppath
        mw.DATA_PATH = self.loginwindow.configpath
        self.window = mw.MainWindow(self.threadpool)

        # 设置主界面风格切换动作信号/槽连接
        self.window.actionWindows.triggered.connect(self._setStyle)
        self.window.actionwindowsvista.triggered.connect(self._setStyle)
        self.window.actionFusion.triggered.connect(self._setStyle)
        self.window.actionQdarkstyle.triggered.connect(self._setStyle)

        self.window.show()

        # 连接后端信号槽
        # ESS.ESSsignal.output.connect(self.window.handleMessageFromPkt)
        # thread_monitor = CM.Monitor(
        #     message=app.window.handleMessageFromPkt,
        #     path=app.window.getPathFromPkt
        # )
        # thread_monitor.setDaemon(True)
        # thread_monitor.daemon = True
        # thread_monitor.start()

        # 特殊测试，伪造RM条目
        pass
        # CM.PL.RegFlag = 1
        # nid = "b0cd69ef142db5a471676ad710eebf3a"
        # CM.PL.PeerProxys[int(nid, 16)] = '10.134.149.183'
        # nid = "d23454d19f307d8b98ff2da277c0b546"
        # CM.PL.PeerProxys[int(nid, 16)]='10.134.148.137'

    def stop_main(self, signum, frame):
        ic.my_term_sig_handler(signum, frame)


if __name__ == '__main__':
    import sys
    threadpool = QThreadPool()
    app = CoLoRApp(sys.argv, threadpool)
    sys.exit(app.exec_())
