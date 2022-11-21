# coding=utf-8
""" docstring: 后端连接处理模块 """


import json
import asyncio
import signal
import time
from CoLoRProtocol.frontendBackendConnection import *
from PyQt5.QtCore import pyqtSignal, QObject


try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ModuleNotFoundError:
    pass


CONNECTION_TIME = 3
CLOSE_DELAY = 0.5
SEND_INTERVAL = 0.1
server_key = None
server_list = {}
flag_term_sig = False
background_tasks = set()


class signals(QObject):
    # 一次性信号，记得解绑
    connected = pyqtSignal()
    configdata = pyqtSignal(object)
    hashdata = pyqtSignal(dict)
    dowitemprogress = pyqtSignal(dict)
    regitemprogress = pyqtSignal(dict)
    # 周期信号
    message = pyqtSignal(object)
    pathdata = pyqtSignal(object)

# message用于输出信号
# message = pyqtSignal(int, object)
# messageType, message
# pathdata用于输出路径相关信息
# pathdata = pyqtSignal(int, str, list, int, str)
# pkttype, SID, paths, size, NID

backendmessage = signals()


async def test(key):
    # 测试 getconfig request
    await asyncio.sleep(3)
    request = {"type": "getconfig"}
    request_packet = bytes(json.dumps(request), "utf-8")
    await server_list[key][ConnectionEnum.QUEUE].put(request_packet)


example_server_packet = """{
    "type": "getconfigreply",
    "data": {}
}"""


async def parse_server_packet(dict_list, key, packet):
    enddevice = dict_list[key]
    # 1. parse
    json_packet = json.loads(packet)
    # 2. work
    print(json_packet["type"], json_packet.get("data", None))
    return
    match json_packet["type"]:
        case "getconfigreply":
            backendmessage.configdata.emit(json_packet["data"])
        case "receivecolorpacket":
            backendmessage.pathdata.emit(json_packet["data"])
        case "receivebackendmessage":
            backendmessage.message.emit(json_packet["data"])
        case "hashret":
            backendmessage.hashdata.emit(json_packet["data"])
        case "dowitemprogress":
            backendmessage.dowitemprogress.emit(json_packet["data"])
        case "regitemprogress":
            backendmessage.regitemprogress.emit(json_packet["data"])
    print(json_packet["type"], json_packet.get("data", None))
    return


async def connect_server():
    # TODO: reconnect
    connectcount = 0
    while connectcount < CONNECTION_TIME:
        try:
            r, w = await asyncio.open_connection(HOST, PORT)
        except ConnectionRefusedError:
            connectcount += 1
            print(f"connection refused. Retry(total = {connectcount})")
            if connectcount == CONNECTION_TIME or flag_term_sig:
                return
            continue
        else:
            connectcount = CONNECTION_TIME

    pb = await hello(server_list, "client", r, w)
    if pb:
        global server_key
        server_key = pb
        backendmessage.connected.emit()
        await asyncio.gather(
            sender(server_list, background_tasks, pb, time=SEND_INTERVAL),
            receiver(server_list, background_tasks, pb, parse_server_packet),
            test(pb)
        )
    w.close()
    await w.wait_closed()


def main():
    asyncio.run(connect_server())


def put_request(request):
    """ docstring: put操作可能会阻塞，需要另起一个线程 """
    request_packet = bytes(json.dumps(request), "utf-8")
    asyncio.run(server_list[server_key][ConnectionEnum.QUEUE].put(request_packet))
    print("put ok")


def normal_stop():
    global flag_term_sig
    flag_term_sig = True
    time.sleep(CLOSE_DELAY)
    for _, v in server_list.items():
        v[ConnectionEnum.CONTROL_FLAG] = False
        v[ConnectionEnum.WRITER].close()
    try:
        asyncio.get_event_loop().stop()
    except Exception:
        print("loop has already stopped!")


def my_term_sig_handler(signum, frame):
    global flag_term_sig
    flag_term_sig = True
    term_sig_handler(server_list, signum, frame)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, my_term_sig_handler)
    signal.signal(signal.SIGINT, my_term_sig_handler)
    main()
