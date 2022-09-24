# coding=utf-8
""" docstring: Get包格式 """

from scapy.all import (
    Packet,BitField,ByteField,ShortField,XShortField,LEShortField,
    FieldLenField,FlagsField,StrFixedLenField,FieldListField,
    ConditionalField,StrLenField,IntField,bind_layers,IP)
from useful_func import (CalcChecksum, int2BytesLE, int2Bytes)


class CoLoR_Get(Packet):
    name = "CoLoR_Get"
    fields_desc=[
        BitField("Version", 7, 4, tot_size=1),
        BitField("Package", 2, 4, end_tot_size=1),
        ByteField("TTL", 64),
        LEShortField("pkg_length", None),
        XShortField("checksum", None),
        ShortField("MTU", None),
        FieldLenField("PID_num", None, fmt="B", count_of="PIDs"),
        FlagsField("Flags", 8, 8, "rrrASQKF"),
        ShortField("Minimal_PID_CP", None),
        StrFixedLenField("N_sid", "", 16),
        StrFixedLenField("L_sid", "", 20),
        StrFixedLenField("nid", "", 16),
        ConditionalField(
            FieldLenField("Public_key_len", None, fmt="H", length_of="Public_key"),
            lambda pkt:pkt.Flags.K==True),
        ConditionalField(
            StrLenField("Public_key", "", length_from=lambda pkt:pkt.Public_key_len),
            lambda pkt:pkt.Flags.K==True),
        ConditionalField(
            FieldLenField("QoS_len", None, fmt="B", length_of="QoS_requirements"),
            lambda pkt:pkt.Flags.Q==True),
        ConditionalField(
            StrLenField("QoS_requirements", "", length_from=lambda pkt:pkt.QoS_len),
            lambda pkt:pkt.Flags.Q==True),
        ConditionalField(
            IntField("Seg_ID", None),
            lambda pkt:pkt.Flags.S==True),
        FieldListField("PIDs", None, StrFixedLenField("", "", 4), count_from=lambda pkt:pkt.PID_num)
    ]
    def post_build(self, pkt, pay):
        if self.pkg_length is None:
            self.pkg_length = len(pkt)
            pkt = pkt[:2] + int2BytesLE(self.pkg_length,2) + pkt[4:]
        if self.checksum is None:
            self.checksum = CalcChecksum(pkt)
            pkt = pkt[:4] + int2Bytes(self.checksum, 2) + pkt[6:]
        return pkt + pay


if __name__ == '__main__':
    from scapy.all import *
    bind_layers(IP, CoLoR_Get, proto=150)
    bind_layers(IP, CoLoR_Get, {'proto':150})
    a = CoLoR_Get()
    a.N_sid = b'\xff'*16
    a.L_sid = b'\x01'*20
    a.nid = b'\xf0'*16
    a.PIDs = [b'\x99\x01\x66\x55',b'\x90\x01\x22\x11']
    pkt = IP(dst="192.168.50.192")/a
    send(pkt, verbose=0)
