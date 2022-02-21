''' docstring: 数据泄露攻击 '''

import os
import sys
__BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))).replace('\\', '/')
sys.path.append(__BASE_DIR)

if __name__ == '__main__':
    from CoLoRProtocol.CoLoRpacket import ColorData
    from scapy.all import IP, send
    import os
    pkt = IP(dst = "10.0.1.1", src = "10.0.1.99")

    cd = ColorData()
    cd.N_sid = bytes.fromhex("d23454d19f307d8b98ff2da277c0b546")
    cd.L_sid = bytes.fromhex("4b666674869389c74721b58447d787c924c56289")
    cd.nid_cus = bytes.fromhex("b0cd69ef142db5a471676ad710eebf3a ")
    cd.PIDs = [bytes.fromhex("abcd6655"), bytes.fromhex("dcba4433")]
    cd.Flags.S = True
    cd.PID_pt = 2

    i = 0
    while True:
        cd.Seg_ID = i
        i += 1
        payload = os.urandom(1000)
        send(pkt/cd/payload, verbose=0)
        op = input("发送完成，等待再次攻击（按q退出，按其他键继续）")
        if (op == 'q'):
            break
