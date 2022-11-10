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
SLEEP_TIME = 0.5


class ConnectionEnum(IntEnum):
    READER = 0
    WRITER = 1
    CONTROL_FLAG = 2
    QUEUE = 3


async def send_packet(dict_list, key, packet):
    enddevice = dict_list[key]
    # write
    enddevice[ConnectionEnum.WRITER].write(struct.pack(">I", len(packet)))
    await enddevice[ConnectionEnum.WRITER].drain()
    enddevice[ConnectionEnum.WRITER].write(packet)
    await enddevice[ConnectionEnum.WRITER].drain()


async def receiver(dict_list, background_tasks, key, parse_packet):
    enddevice = dict_list[key]
    while enddevice[ConnectionEnum.CONTROL_FLAG]:
        # TODO: start to read, task(parse)
        try:
            l = await enddevice[ConnectionEnum.READER].readexactly(DATA_LENGTH)
            l, = struct.unpack(">I", l)
            p = await enddevice[ConnectionEnum.READER].readexactly(l)
        except asyncio.IncompleteReadError as e:
            enddevice[ConnectionEnum.WRITER].close()
            await enddevice[ConnectionEnum.WRITER].wait_closed()
            return
        task = asyncio.create_task(parse_packet(dict_list, key, p))
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)


async def sender(dict_list, background_tasks, key, time=SLEEP_TIME):
    enddevice = dict_list[key]
    while enddevice[ConnectionEnum.CONTROL_FLAG]:
        # start to task(write)
        try:
            data = enddevice[ConnectionEnum.QUEUE].get_nowait()
        except asyncio.QueueEmpty:
            await asyncio.sleep(time)
            continue
        task = asyncio.create_task(send_packet(dict_list, key, data))
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
        # print(f"get new connection[{len(dict_list)+1}]!")
    elif enddevice == "client":
        b = secrets.token_bytes(KEY_LENGTH)
        w.write(b)
        await w.drain()
        # print(f"send<{b}> ok!")
        try:
            p = await r.readexactly(KEY_LENGTH)
        except asyncio.IncompleteReadError as e:
            traceback.print_exc()
            return None
        # print(f"receive<{p}> ok!")
    else:
        # print("wrong arguments in hello!")
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
