# coding=utf-8
""" docstring: 后端主程序 """


import signal
import ColorMonitor as cm
import InnerConnectionServer as ics


def my_term_sig_handler(signum, frame):
    # TODO: 处理其他线程退出
    ics.my_term_sig_handler(signum, frame)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, my_term_sig_handler)
    signal.signal(signal.SIGINT, my_term_sig_handler)
    monitor = cm.Monitor()
    monitor.start()
    ics.main()
