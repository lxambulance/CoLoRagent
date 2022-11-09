# coding=utf-8
""" docstring: 后端监听程序 """


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
client_list = {}
background_tasks = set()


example_request = """{
    "type": "request",
    "op": "getconfig",
    "data": {}
}"""


async def parse_client_packet(dict_list, key, packet):
    client = dict_list[key]
    # 1. parse
    json_packet = json.loads(packet)
    # 2. work
    reply = {"type": "reply"}
    if json_packet["type"] == "request":
        match json_packet["op"]:
            case "getconfig":
                reply["op"] = "getconfig"
                async with aiofiles.open(DATA_PATH, 'br') as f:
                    data = await f.read()
                # TODO: 修改配置文件路径信息
                reply["data"] = json.loads(data)
                reply_packet = bytes(json.dumps(reply), "utf-8")
                await client[ConnectionEnum.QUEUE].put(reply_packet)
                print(packet)
                print(reply_packet)
            case "setconfig":
                data = bytes(json.dumps(json_packet["data"]), "utf-8")
                async with aiofiles.open(DATA_PATH, "bw") as f:
                    await f.write(data)
                print("save config ok!")
    return


async def client_connected(r, w):
    # TODO: reconnect
    pb = await hello(client_list, "server", r, w)
    if pb:
        await asyncio.gather(
            sender(client_list, background_tasks, pb),
            receiver(client_list, background_tasks, pb, parse_client_packet)
        )
    w.close()
    await w.wait_closed()


async def backend_server():
    s = await asyncio.start_server(client_connected, HOST, PORT, family=socket.AF_INET, reuse_address=True)
    await s.serve_forever()


def my_term_sig_handler(signum, frame):
    for k, v in client_list.items():
        print(f"connection<{k}>")
    term_sig_handler(client_list, signum, frame)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, my_term_sig_handler)
    signal.signal(signal.SIGINT, my_term_sig_handler)
    asyncio.run(backend_server())
