# coding=utf-8
""" docstring: 后端监听前端程序 """


import asyncio
import socket
import signal
import sys
from CoLoRProtocol.frontendBackendConnection import *


try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ModuleNotFoundError:
    pass


client_list = {}
background_tasks = set()


async def client_connected(r, w):
    # TODO: reconnect
    pb = await hello(client_list, "server", r, w)
    if pb:
        await asyncio.gather(
            hander(client_list, background_tasks, pb),
            generator(client_list, background_tasks, pb)
        )
    w.close()
    await w.wait_closed()


def my_term_sig_handler(signum, frame):
    for k, v in client_list.items():
        print(f"connection<{k}>")
    term_sig_handler(client_list, signum, frame)


async def backend_server():
    signal.signal(signal.SIGTERM, my_term_sig_handler)
    signal.signal(signal.SIGINT, my_term_sig_handler)
    s = await asyncio.start_server(client_connected, HOST, PORT, family=socket.AF_INET, reuse_address=True)
    await s.serve_forever()


if __name__ == '__main__':
    asyncio.run(backend_server())
