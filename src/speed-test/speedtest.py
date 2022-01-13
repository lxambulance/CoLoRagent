# coding = utf-8
''' docstring: scapy库发包速度 '''


import time
from scapy.all import IP, send
from CoLoR_Get import CoLoR_Get
from CoLoR_Data import CoLoR_Data


def SendIpv4(ipdst, data):
    ''' docstring: 封装IPv4网络包并发送
    ipdst: 目标IP地址，data: IP包正文内容，proto: 约定值150 '''
    pkt = IP(dst=ipdst, proto=150) / data
    send(pkt, verbose=0)


if __name__ == '__main__':
    pkt_CG = CoLoR_Get()
    pkt_CG.N_sid = b'\xff'*16
    pkt_CG.L_sid = b'\x01'*20
    pkt_CG.nid = b'\xf0'*16
    pkt_CG.PIDs = [b'\x99\x01\x66\x55',b'\x90\x01\x22\x11']

    pkt_CD = CoLoR_Data() / (b'\x61'*1000)
    pkt_CD.N_sid = b'\xff'*16
    pkt_CD.L_sid = b'\x01'*20
    pkt_CD.nid_cus = b'\xf0'*16
    pkt_CD.PIDs = [b'\x90\x01\x22\x11',b'\x99\x01\x66\x55']

    start_time = time.time()
    for i in range(10000):
        SendIpv4("127.0.0.1", pkt_CG)
        if (i+1) % 2000 == 0:
            print(time.time()-start_time)
    print("get sending speed: ", 10000/(time.time()-start_time))
    
    start_time = time.time()
    for i in range(10000):
        SendIpv4("127.0.0.1", pkt_CD)
        if (i+1) % 2000 == 0:
            print(time.time()-start_time)
    print("data sending speed: ", 10000/(time.time()-start_time))

# result(original, just use send):
#   939 get packet per second
#   798 data packet(with 1000 bytes payload) per second
