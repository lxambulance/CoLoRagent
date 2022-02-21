''' docstring: 发送非本机nid的get报文 '''

import os
import sys
__BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))).replace('\\', '/')
sys.path.append(__BASE_DIR)

if __name__ == '__main__':
    from CoLoRProtocol.CoLoRpacket import ColorGet
    from scapy.all import IP, send
    import time
    pkt = IP(dst = "10.0.1.1")

    cg = ColorGet()
    cg.N_sid = bytes.fromhex("d23454d19f307d8b98ff2da277c0b546")
    cg.L_sid = bytes.fromhex("a9dd379c69638ad6656b2df1dec4804ce760106a")
    cg.nid = bytes.fromhex("b0cd69ef142db5a471676ad710eebf3a")
    cg.PIDs = [b'\x01\x23\x45\x67', b'\x98\x76\x54\x32']
    
    while True:
        send(pkt/cg, verbose=0)
        time.sleep(2)
