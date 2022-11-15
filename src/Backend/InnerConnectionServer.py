# coding=utf-8
""" docstring: 后端监听程序 """


import json
import asyncio
import aiofiles
import socket
import signal
from CoLoRProtocol.frontendBackendConnection import *


try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ModuleNotFoundError:
    pass


# 调用者需要负责修改BASE_DIR或DATA_PATH、HOME_DIR到正确路径
BASE_DIR = '.'
DATA_PATH = BASE_DIR + '/data.json'
HOME_DIR = BASE_DIR + '/.tmp'
SEND_INTERVAL = 0.1
client_list = {}
background_tasks = set()


async def test(key):
    """ docstring: 测试 server 发送 reply """
    await asyncio.sleep(5)
    reply = {"type": "receivecolorpacket"}
    reply["data"] = {"pkttype": 0x72, "SID": "123", "paths": [0x11222695], "size": 100, "NID": 0}
    reply_packet = bytes(json.dumps(reply), "utf-8")
    await client_list[key][ConnectionEnum.QUEUE].put(reply_packet)
    reply = {"type": "receivebackendmessage"}
    reply["data"] = {"messageType": 1, "message": "hello, world!"}
    reply_packet = bytes(json.dumps(reply), "utf-8")
    await client_list[key][ConnectionEnum.QUEUE].put(reply_packet)
    reply = {"type": "hashret"}
    reply["data"] = {"retid": 1, "filehash": "a5"*20}
    reply_packet = bytes(json.dumps(reply), "utf-8")
    await client_list[key][ConnectionEnum.QUEUE].put(reply_packet)
    reply = {"type": "downprogress"}
    reply["data"] = {"row":0, "value":10}
    reply_packet = bytes(json.dumps(reply), "utf-8")
    await client_list[key][ConnectionEnum.QUEUE].put(reply_packet)



example_client_packet = """{
    "type": "getconfig"
}"""


async def parse_client_packet(dict_list, key, packet):
    client = dict_list[key]
    # 1. parse
    json_packet = json.loads(packet)
    # 2. work
    reply = {}
    match json_packet["type"]:
        case "getconfig":
            reply["type"] = "getconfigreply"
            async with aiofiles.open(DATA_PATH, 'br') as f:
                data = await f.read()
            # TODO: 修改配置文件路径信息
            reply["data"] = json.loads(data)
            reply_packet = bytes(json.dumps(reply), "utf-8")
            await client[ConnectionEnum.QUEUE].put(reply_packet)
        case "setconfig":
            data = bytes(json.dumps(json_packet["data"]), "utf-8")
            async with aiofiles.open(DATA_PATH, "bw") as f:
                await f.write(data)
        case "startvideoserver":
            # TODO
            # CM.PL.AddCacheSidUnit(1, 1, 1, 1, 1)
            # CM.PL.SidAnn()
            print("startvideoserver")
        case "stopvideoserver":
            print("stop")
        case "additem":
            # TODO 另起一个线程计算
            print(json_packet["data"])
        case "delitem":
            print(json_packet["data"])
        case "dowitem":
            # TODO:
            # CM.PL.Get(SID, 1)
            # CM.PL.Get(SID, filepath)
            # 另外需要控制接收进度条
            print(json_packet["data"])
    return


async def client_connected(r, w):
    # TODO: reconnect
    pb = await hello(client_list, "server", r, w)
    if pb:
        await asyncio.gather(
            sender(client_list, background_tasks, pb, time=SEND_INTERVAL),
            receiver(client_list, background_tasks, pb, parse_client_packet),
            test(pb)
        )
    w.close()
    await w.wait_closed()


async def backend_server():
    s = await asyncio.start_server(client_connected, HOST, PORT, family=socket.AF_INET, reuse_address=True)
    await s.serve_forever()


def my_term_sig_handler(signum, frame):
    for k, _ in client_list.items():
        print(f"connection<{k}>")
    term_sig_handler(client_list, signum, frame)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, my_term_sig_handler)
    signal.signal(signal.SIGINT, my_term_sig_handler)
    asyncio.run(backend_server())
