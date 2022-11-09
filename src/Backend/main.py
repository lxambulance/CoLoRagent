# coding=utf-8
""" docstring: 后端主程序 """


import threading


class CoLoRBackend(threading.Thread):
    """ docstring: 后端类 """

    def __init__(self):
        # 初始化后端
        # CM.PL.IPv4 = self.loginwindow.myIPv4
        # CM.PL.Nid = int('0x'+self.loginwindow.myNID, 16)
        # CM.PL.rmIPv4 = self.loginwindow.rmIPv4
        
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
        # CM.PL.RegFlag = 1
        # nid = "b0cd69ef142db5a471676ad710eebf3a"
        # CM.PL.PeerProxys[int(nid, 16)] = '10.134.149.183'
        # nid = "d23454d19f307d8b98ff2da277c0b546"
        # CM.PL.PeerProxys[int(nid, 16)]='10.134.148.137'

        # # 尝试新建文件仓库
        # if not os.path.exists(HOME_DIR):
        #     os.mkdir(HOME_DIR)
        pass

    def run(self):
        pass


if __name__=="__main__":
    cb = CoLoRBackend()
    cb.start()

