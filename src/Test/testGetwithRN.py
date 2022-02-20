''' 测试带RN的get包收包情况 '''


import os
import sys
__BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
sys.path.append(__BASE_DIR)


if __name__ == '__main__':
    from scapy.all import send, IP
    from CoLoRProtocol.CoLoRpacket import ColorGet
    pkt = IP(dst="192.168.50.62")

    cg = ColorGet()
    cg.N_sid = bytes.fromhex("d23454d19f307d8b98ff2da277c0b546")
    cg.L_sid = bytes.fromhex("fc12850558c3e2719d6a6e297b4a61002ea408f3")
    cg.nid = bytes.fromhex("b0cd69ef142db5a471676ad710eebf3a")
    cg.PIDs = [b'\x01\x23\x45\x67', b'\x98\x76\x54\x32']
    cg.Flags.R = True
    cg.Random_num = bytes.fromhex("12345678")
    # cg.show2()

    send(pkt/cg, verbose = 0)
