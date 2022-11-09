# coding=utf-8
""" docstring: 后端连接处理模块 """


import asyncio
import signal
from CoLoRProtocol.frontendBackendConnection import *
from PyQt5.QtCore import pyqtSignal, QObject


try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ModuleNotFoundError:
    pass


CONNECTION_TIME = 3
server_key = None
server_list = {}
background_tasks = set()


class signals(QObject):
    connected = pyqtSignal()
    configdata = pyqtSignal(object)


backendmessage = signals()


async def test(key):
    # 测试 getconfig request
    request = {"type": "request"}
    request["op"] = "getconfig"
    request_packet = bytes(json.dumps(request), "utf-8")
    await server_list[key][ConnectionEnum.QUEUE].put(request_packet)


example_reply = """{
    "type": "reply",
    "op": "getconfig",
    "data": {}
}"""


async def parse_server_packet(dict_list, key, packet):
    enddevice = dict_list[key]
    # 1. parse
    json_packet = json.loads(packet)
    # 2. work
    if json_packet["type"] == "reply":
        match json_packet["op"]:
            case "getconfig":
                backendmessage.configdata.emit(json_packet["data"])
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
            if connectcount == CONNECTION_TIME:
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
            sender(server_list, background_tasks, pb),
            receiver(server_list, background_tasks, pb, parse_server_packet)
        )
    w.close()
    await w.wait_closed()


def main():
    asyncio.run(connect_server())


def put_request(request):
    """ docstring: put操作可能会阻塞，需要另起一个线程 """
    request_packet = bytes(json.dumps(request), "utf-8")
    asyncio.run(server_list[server_key][ConnectionEnum.QUEUE].put(request_packet))


def my_term_sig_handler(signum, frame):
    term_sig_handler(server_list, signum, frame)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, my_term_sig_handler)
    signal.signal(signal.SIGINT, my_term_sig_handler)
    main()
