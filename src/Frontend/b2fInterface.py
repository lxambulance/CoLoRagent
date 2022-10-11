# coding=utf-8
""" docstring: 后端反馈前端接口 """


from PyQt5.QtCore import QObject, pyqtSignal


class pktSignals(QObject):
    """ docstring: 包处理的信号 """
    # finished用于任务结束信号
    finished = pyqtSignal()
    # output用于输出信号
    output = pyqtSignal(int, object)
    # pathdata用于输出路径相关信息
    pathdata = pyqtSignal(int, str, list, int, str)
