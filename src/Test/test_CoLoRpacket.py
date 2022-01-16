
''' docstring: color协议包模块单元测试 '''

import os
import sys
import pytest
__BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))).replace('\\', '/')
sys.path.append(__BASE_DIR)


getpkt_bytes = bytes.fromhex(
    "72404800d94c000002080000ffffffffffffffffffffffffffffffff0101010101010101010101010101010101010101a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a50123456798765432")
datpkt_bytes = bytes.fromhex(
    "73404a008b544a000300ffffffffffffffffffffffffffffffff0101010101010101010101010101010101010101a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5000000009876543201234567")
annpkt_bytes = bytes.fromhex(
    "7140820053e60020e83d0201010101010101010101010101010101020202020202020202020202020202020202020203030303030303030303030303030303010112010112e83d0201010101010101010101010101010101020202020202020202020202020202020202020203030303030303030303030303030303010112010112")
ctlpkt_proxyregister_bytes = bytes.fromhex(
    "74400140080514003e32a8c0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0")
ctlpkt_proxyregisterreply_bytes = bytes.fromhex(
    "7440252e08065e0000033e32a8c0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f03e32a8c0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f03e32a8c0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0000522112632a8c022112632a8c022112632a8c022112632a8c022112632a8c0")
ctlpkt_attackwarning_bytes = bytes.fromhex(
    "74401c7a08121f0000000000000000000000000000000000050a1a0000050a1a0000050a1a0000")
ctlpkt_odcwarning_bytes = bytes.fromhex(
    "74406fae081114004500001400010000400074e40101010102020202")


def test_CalcChecksum():
    from CoLoRProtocol.CoLoRpacket import CalcChecksum
    assert CalcChecksum(getpkt_bytes) == 0
    assert CalcChecksum(datpkt_bytes) == 0
    assert CalcChecksum(annpkt_bytes) == 0
    assert CalcChecksum(ctlpkt_proxyregister_bytes) == 0
    assert CalcChecksum(ctlpkt_proxyregisterreply_bytes) == 0
    assert CalcChecksum(ctlpkt_attackwarning_bytes) == 0
    assert CalcChecksum(ctlpkt_odcwarning_bytes) == 0


if __name__ == '__main__':
    test_CalcChecksum()
