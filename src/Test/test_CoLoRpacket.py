
''' docstring: color协议包模块单元测试 '''

import importsrc
import pytest


getpkt_bytes = bytes.fromhex(
    "72404800d94c000002080000ffffffffffffffffffffffffffffffff0101010101010101010101010101010101010101a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a56745230132547698")
getpkt_RN_bytes = bytes.fromhex(
    "72404c00ffad0000020c0000d23454d19f307d8b98ff2da277c0b546fc12850558c3e2719d6a6e297b4a61002ea408f3b0cd69ef142db5a471676ad710eebf3a012345679876543212345678")
datpkt_bytes = bytes.fromhex(
    "73404a008b544a000300ffffffffffffffffffffffffffffffff0101010101010101010101010101010101010101a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5325476986745230100000000")
datpkt_hmac_bytes = bytes.fromhex(
    "ffffffffffffffffffffffffffffffff0101010101010101010101010101010101010101a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a55a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a00000000000000009876543201234567")
datpkt_postbuild_bytes = bytes.fromhex(
    "73405e0038385e000224ffffffffffffffffffffffffffffffff0101010101010101010101010101010101010101a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a55a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a98eec036000000009876543201234567")
annpkt_bytes = bytes.fromhex(
    "7140820053e60020e83d0201010101010101010101010101010101020202020202020202020202020202020202020203030303030303030303030303030303010112010112e83d0201010101010101010101010101010101020202020202020202020202020202020202020203030303030303030303030303030303010112010112")
ctlpkt_proxyregister_bytes = bytes.fromhex(
    "74400140080514003e32a8c0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0")
ctlpkt_proxyregisterreply_bytes = bytes.fromhex(
    "7440005508065c00033e32a8c0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f03e32a8c0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f03e32a8c0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f00522112632a8c022112632a8c022112632a8c022112632a8c022112632a8c0")
ctlpkt_attackwarning_bytes = bytes.fromhex(
    "74401c7a08121f0000000000000000000000000000000000050a1a0000050a1a0000050a1a0000")
ctlpkt_odcwarning_bytes = bytes.fromhex(
    "74406fae081114004500001400010000400074e40101010102020202")
ip_control_pkt_bytes = bytes.fromhex(
    "45000038000000004096642b0a0001010a0001057480677908061c0001d23454d19f307d8b98ff2da277c0b5460501000a0144330201000a")


def test_CalcChecksum():
    from CoLoRProtocol.CoLoRpacket import CalcChecksum
    assert CalcChecksum(getpkt_bytes) == 0
    assert CalcChecksum(datpkt_bytes) == 0
    assert CalcChecksum(annpkt_bytes) == 0
    assert CalcChecksum(ctlpkt_proxyregister_bytes) == 0
    assert CalcChecksum(ctlpkt_proxyregisterreply_bytes) == 0
    assert CalcChecksum(ctlpkt_attackwarning_bytes) == 0
    assert CalcChecksum(ctlpkt_odcwarning_bytes) == 0


def test_ipv4_int():
    from CoLoRProtocol.CoLoRpacket import Ipv42Int, Int2Ipv4
    assert Int2Ipv4(Ipv42Int("0.0.0.0")) == "0.0.0.0"
    assert Int2Ipv4(Ipv42Int("255.255.255.255")) == "255.255.255.255"
    assert Int2Ipv4(Ipv42Int("0.0.0.0")) != "255.255.255.255"


def test_ColorPacketDissect():
    from scapy.all import IP
    from CoLoRProtocol.CoLoRpacket import ColorGet, ColorData, ColorAnn, ColorControl, IP_NID, ASinfo, AttackInfo
    cg = ColorGet(getpkt_bytes)
    assert cg.PIDs[0] == int('01234567', 16)
    cg = ColorGet(getpkt_RN_bytes)
    assert cg.Random_num == b'\x12\x34\x56\x78'
    cd = ColorData(datpkt_bytes)
    assert cd.PIDs[0] == int('98765432', 16)
    ca = ColorAnn(annpkt_bytes)
    assert ca.Announce_unit_list[1].Strategy_unit_list[1].value == b'\x12'
    cc = ColorControl(ctlpkt_proxyregister_bytes)
    assert cc[IP_NID].nid == b"\xf0"*16
    cc = ColorControl(ctlpkt_proxyregisterreply_bytes)
    assert cc[ASinfo].px_ip_list[2].PX == 0x1122
    cc = ColorControl(ctlpkt_attackwarning_bytes)
    assert cc[AttackInfo].attack_list[2].attack_num == 6666
    cc = ColorControl(ctlpkt_odcwarning_bytes)
    assert cc[IP].src == "1.1.1.1"
    assert cc[IP].dst == "2.2.2.2"


def test_CalcHMAC():
    from CoLoRProtocol.CoLoRpacket import CalcHMAC, ColorData
    rn = b'\x12\x34\x56\x78'
    assert CalcHMAC(datpkt_hmac_bytes + rn)[-4:] == b'\x98\xee\xc0\x36'
    cd = ColorData(datpkt_postbuild_bytes)
    cd.HMAC = rn
    assert datpkt_postbuild_bytes == cd.__bytes__()


def test_IPguess():
    from scapy.all import IP
    from CoLoRProtocol.CoLoRpacket import ColorControl
    pkt = IP(ip_control_pkt_bytes)
    assert type(pkt.payload) == ColorControl


if __name__ == '__main__':
    test_CalcChecksum()
    test_ipv4_int()
    test_ColorPacketDissect()
    test_CalcHMAC()
    test_IPguess()
