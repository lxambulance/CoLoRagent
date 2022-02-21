''' docstring: 监听泄露 '''

import os
import sys
__BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))).replace('\\', '/')
sys.path.append(__BASE_DIR)

if __name__ == '__main__':
    from CoLoRProtocol.CoLoRpacket import ColorData
    from scapy.all import IP, send
    import time
    pkt = IP(dst = "10.0.1.1")

    cd = ColorData()
    cd.N_sid = b'\xff'*16
    cd.L_sid = b'\x01'*20
    cd.nid_cus = b'\xa5'*16
    cd.nid_pro = b'\x5a'*16
    cd.PIDs = [b'\x00\x00\x00\x00', b'\x98\x76\x54\x32', b'\x01\x23\x45\x67']
    
    while True:
        send(pkt/cg, verbose=0)
        time.sleep(2)
