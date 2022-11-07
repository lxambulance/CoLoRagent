# coding=utf-8
""" docstring: 后端连接处理模块 """


import asyncio
import signal
from CoLoRProtocol.frontendBackendConnection import *


try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ModuleNotFoundError:
    pass


server_list = {}
background_tasks = set()


def my_term_sig_handler(signum, frame):
    term_sig_handler(server_list, signum, frame)


async def connect_server():
    signal.signal(signal.SIGTERM, my_term_sig_handler)
    signal.signal(signal.SIGINT, my_term_sig_handler)

    # TODO: reconnect
    r, w = await asyncio.open_connection(HOST, PORT)

    pb = await hello(server_list, "client", r, w)
    if pb:
        await asyncio.gather(
            hander(server_list, background_tasks, pb),
            generator(server_list, background_tasks, pb)
        )
    w.close()
    await w.wait_closed()


if __name__ == '__main__':
    asyncio.run(connect_server())
