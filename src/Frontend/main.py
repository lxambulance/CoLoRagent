# coding=utf-8
""" docstring: 前端主程序 """


import signal
import qdarkstyle as qds
import MainWindow as mw
import InnerConnection as ic
from LogInWindow import logInWindow

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


class CoLoRFrontend(QApplication):
    """ docstring: 前端类 """

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

        # 设置登录界面接受、拒绝信号/槽连接
        self.loginwindow.buttonBox.accepted.connect(self.start_main)
        self.loginwindow.buttonBox.rejected.connect(stop_main)

        # 设置结束信号操作
        signal.signal(signal.SIGTERM, ic.my_term_sig_handler)
        signal.signal(signal.SIGINT, ic.my_term_sig_handler)

    def start_main(self):
        # 未连接到后端禁止启动
        if self.loginwindow.configdata is None:
            stop_main()

        # 初始化本终端信息
        self.window = mw.MainWindow(self.threadpool, self.loginwindow.myNID, configpath=self.loginwindow.configpath,
                                    filetmppath=self.loginwindow.filetmppath, configdata=self.loginwindow.configdata)

        # 设置主界面风格切换动作信号/槽连接
        self.window.actionWindows.triggered.connect(self._setStyle)
        self.window.actionwindowsvista.triggered.connect(self._setStyle)
        self.window.actionFusion.triggered.connect(self._setStyle)
        self.window.actionQdarkstyle.triggered.connect(self._setStyle)
        self.window.show()


def stop_main():
    ic.normal_stop()
    sys.exit()


if __name__ == '__main__':
    import sys
    threadpool = QThreadPool()
    app = CoLoRFrontend(sys.argv, threadpool)
    sys.exit(app.exec_())
