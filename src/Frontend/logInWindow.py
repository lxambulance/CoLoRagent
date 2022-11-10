# coding=utf-8
""" docstring: CoLoR 登录对话页 """


from PyQt5.QtWidgets import QDialog, QApplication
from logInDialog import Ui_Dialog
from worker import worker
import InnerConnection as ic


class logInWindow(QDialog, Ui_Dialog):
    """ docstring: 登录窗口类 """

    def __init__(self, threadpool):
        super().__init__()
        self.setupUi(self)
        self.threadpool = threadpool
        self.configpath = None
        self.filetmppath = None
        self.myNID = None
        self.myIPv4 = None
        self.rmIPv4 = None
        self.configdata = None

        # 设置结束、重生成NID、ED IP修改、RM IP修改的信号/槽连接
        self.buttonBox.accepted.connect(self.writeConfig)
        self.generateNID.clicked.connect(self.regenerateNID)
        self.agentIPv4.textChanged.connect(self.setIPv4)
        self.RMIPv4.textChanged.connect(self.setRMIPv4)

        # 设置前端连接模块在另外一个线程运行
        InnerConnectionworker = worker(0, ic.main)
        ic.backendmessage.connected.connect(self.startReadConfig)
        self.threadpool.start(InnerConnectionworker)

    def regenerateNID(self):
        """ docstring: 重新生成NID """
        # TODO: 后端重新生成
        pass

    def setIPv4(self, text):
        self.myIPv4 = text

    def setRMIPv4(self, text):
        self.rmIPv4 = text

    def writeConfig(self):
        """ docstring: 保存配置文件 """
        # TODO: 生成配置文件返回
        pass

    def startReadConfig(self):
        """ docstring: 设置发送线程，连接返回读取配置文件信号 """
        ic.backendmessage.connected.disconnect()
        self.sendworker = worker(0, self.sendGetConfigRequest)
        ic.backendmessage.configdata.connect(self.readConfig)
        self.threadpool.start(self.sendworker)

    def sendGetConfigRequest(self):
        """ docstring: 生成配置请求并发送。put操作可能会阻塞，需要另起一个线程 """
        request = {"type": "getconfig"}
        ic.put_request(request)

    def readConfig(self, data):
        """ docstring: 处理后端配置文件，填写表单项 """
        ic.backendmessage.configdata.disconnect()
        self.configdata = data
        self.configpath = data.get("configpath", None)
        self.showpath_config.setText(self.configpath)
        self.filetmppath = data.get("filetmppath", None)
        self.showpath_filetmp.setText(self.filetmppath)
        self.myNID = data.get("myNID", None)
        self.agentNID.setText(self.myNID)
        self.myIPv4 = data.get("myIPv4", None)
        self.agentIPv4.setText(self.myIPv4)
        self.rmIPv4 = data.get("RMIPv4", None)
        self.RMIPv4.setText(self.rmIPv4)


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = logInWindow()
    window.show()
    sys.exit(app.exec_())
