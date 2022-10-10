""" docstring: 测试CoLoR协议生成包速度 """


import os
import time
from CoLoRProtocol.CoLoRpacket import ColorData


if __name__ == '__main__':
    testN_sid = b'\x12\x34\x56\x78'*4
    testL_sid = b'\x87\x65\x43\x21'*5
    testnid_cus = b'\x11\x22'*8
    testnid_pro = b'\x99\x00' * 8
    testpayload = os.urandom(2000)

    ret = []
    start_time = time.time()
    for i in range(10000):
        j = i % 16
        k = i % 20
        l = i % 1000
        cd = ColorData()
        cd.N_sid = testN_sid[j:] + testN_sid[:j]
        cd.L_sid = testL_sid[k:] + testL_sid[:k]
        cd.nid_cus = testnid_cus[j:] + testnid_cus[:j]
        cd.nid_pro = testnid_pro[j:] + testnid_pro[:j]
        cd.Flags.R = True
        cd.Flags.C = True
        cd.HMAC = os.urandom(4)
        cd.PIDs = [int('98765432', 16), int(
            '01234567', 16), int('10987456', 16), 0]
        cd = cd/testpayload[l:l+1000]
        ret.append(cd.__bytes__().hex())
    print("generate data packet speed: ", 10000/(time.time()-start_time))
    # print(ret)

# result:
#   2162 data packet(with 1000 bytes payload) per second
#   3270 data packet per second
