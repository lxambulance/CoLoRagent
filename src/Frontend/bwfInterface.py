# coding=utf-8
""" docstring: 后端反馈前端接口 """


import socket
from PyQt5.QtCore import QObject, pyqtSignal


class pktSignals(QObject):
    """ docstring: 包处理的信号 """
    # finished用于任务结束信号
    finished = pyqtSignal()
    # output用于输出信号
    output = pyqtSignal(int, object)
    # pathdata用于输出路径相关信息
    pathdata = pyqtSignal(int, str, list, int, str)


class mySocket:
    """ docstring: 前后端通信类，如果跨机器需要处理网络包分片，当前未处理。 """
    __MAX_RECV_LEN__ = 64*1024

    def __init__(self, ip="127.0.0.1", port=50000):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip, port))

    def send(self, msg: bytes):
        return self.sock.send(msg)
        msglen = len(msg)
        self.sock.send(msglen.to_bytes(4, byteorder='big'))
        now = 0
        while now<msglen:
            ret = self.sock.send(msg[now:])
            now += ret
    
    def recv(self) -> bytes:
        return self.sock.recv(self.__MAX_RECV_LEN__)
        msglen = int.from_bytes(self.sock.recv(4), byteorder='big')
        msg = b''
        while len(msg)<msglen:
            msg += self.sock.recv(1024*4)
        return msg


if __name__=='__main__':
    s = mySocket()
    print(s.send(b"hello world"))
    t = s.recv()
    print(len(t))
