# coding=utf-8
''' docstring: long time task base class '''

from PyQt5.QtCore import *
import traceback, sys

class workerSignals(QObject):
    ''' docstring: worker signals class '''

    # finished用于任务结束信号
    finished = pyqtSignal()
    # error用于出错信号
    error = pyqtSignal(tuple)
    # result用于返回任务结果
    result = pyqtSignal(object)
    # progress用于回调函数显示任务进度
    progress = pyqtSignal(int)

class worker(QRunnable):
    ''' docstring: worker class '''

    def __init__(self, option, func, *args, **kwargs):
        ''' docstring: store the initial val '''
        super().__init__()
        self.f = func
        self.args = args
        self.kwargs = kwargs
        self.signals = workerSignals()

        if (option & 1) == 1:
            # 添加回调函数
            self.kwargs['progress_callback'] = self.signals.progress
    
    @pyqtSlot()
    def run(self):
        ''' docstring: do main work '''
        try:
            result = self.f(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()
