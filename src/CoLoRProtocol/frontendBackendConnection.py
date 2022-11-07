# coding=utf-8
""" docstring: 前后端连接公共函数 """


import sys
import json
import struct
import secrets
import asyncio
import traceback
from enum import IntEnum


HOST, PORT = "127.0.0.1", 50001
DATA_LENGTH = 4
KEY_LENGTH = 10
SLEEP_TIME = 1


class ConnectionEnum(IntEnum):
    READER = 0
    WRITER = 1
    CONTROL_FLAG = 2
    QUEUE = 3


example_request = """{
    "type": "request",
    "op":
}"""


example_reply = """{
    "type": "reply",
}"""


async def parse_packet(dict_list, key, packet):
    enddevice = dict_list[key]
    # 1. parse
    raw_data = json.loads(packet)
    # 2. work
    if raw_data["type"] == "request":
        pass
    elif raw_data["type"] == "reply":
        pass
    return


async def generate_packet(dict_list, key, packet):
    enddevice = dict_list[key]
    # 1. generate
    raw_data = json.dumps(packet)
    # 2. write
    enddevice[ConnectionEnum.WRITER].write(struct.pack(">I", len(raw_data)))
    await enddevice[ConnectionEnum.WRITER].drain()
    enddevice[ConnectionEnum.WRITER].write(raw_data)
    await enddevice[ConnectionEnum.WRITER].drain()


async def hander(dict_list, background_tasks, key):
    enddevice = dict_list[key]
    while enddevice[ConnectionEnum.CONTROL_FLAG]:
        # TODO: start to read, task(parse, work)
        try:
            l = await enddevice[ConnectionEnum.READER].readexactly(DATA_LENGTH)
            l = struct.unpack(">I", l)
            p = await enddevice[ConnectionEnum.READER].readexactly(l)
        except asyncio.IncompleteReadError as e:
            enddevice[ConnectionEnum.WRITER].close()
            await enddevice[ConnectionEnum.WRITER].wait_closed()
            return
        task = asyncio.create_task(parse_packet(dict_list, key, p))
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)


async def generator(dict_list, background_tasks, key):
    enddevice = dict_list[key]
    while enddevice[ConnectionEnum.CONTROL_FLAG]:
        # TODO: start to task(generate, write)
        try:
            data = enddevice[ConnectionEnum.QUEUE].get_nowait()
        except asyncio.QueueEmpty:
            await asyncio.sleep(SLEEP_TIME)
            continue
        task = asyncio.create_task(generate_packet(dict_list, key, data))
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)


async def hello(dict_list, enddevice, r, w):
    if enddevice == "server":
        try:
            p = await r.readexactly(KEY_LENGTH)
        except asyncio.IncompleteReadError as e:
            traceback.print_exc()
            return None
        b = secrets.token_bytes(KEY_LENGTH)
        while b+p in dict_list.keys():
            b = secrets.token_bytes(KEY_LENGTH)
        w.write(b)
        await w.drain()
        print(f"get new connection[{len(dict_list)+1}]!")
    elif enddevice == "client":
        b = secrets.token_bytes(KEY_LENGTH)
        w.write(b)
        await w.drain()
        print(f"send<{b}> ok!")
        try:
            p = await r.readexactly(KEY_LENGTH)
        except asyncio.IncompleteReadError as e:
            traceback.print_exc()
            return None
        print(f"receive<{p}> ok!")
    else:
        print("wrong arguments in hello!")
        return None
    dict_list[p+b] = [r, w, True, asyncio.Queue(maxsize=1024)]
    return p+b


def term_sig_handler(dict_list, signum, frame):
    # print(f"signal number:{signum} Frame:{frame}")
    for k, v in dict_list.items():
        v[ConnectionEnum.CONTROL_FLAG] = False
        v[ConnectionEnum.WRITER].close()
    asyncio.get_event_loop().stop()
    sys.exit()
