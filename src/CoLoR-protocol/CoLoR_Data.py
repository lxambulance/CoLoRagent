# coding=utf-8
''' docstring: Data包格式 '''

from scapy.all import (
    Packet,BitField,ByteField,ShortField,XShortField,LEShortField,
    FieldLenField,FlagsField,StrFixedLenField,FieldListField,
    ConditionalField,StrLenField,IntField,bind_layers,IP)
from useful_func import (CalcChecksum, int2BytesLE, int2Bytes)


class CoLoR_Data(Packet):
    name='CoLoR_Data'
    fields_desc=[
        BitField("Version", 7, 4, tot_size=1),
        BitField("Package", 3, 4, end_tot_size=1),
        ByteField("TTL", 64),
        LEShortField("pkg_length", None),
        XShortField("checksum", None),
        ByteField("header_length", None),
        ByteField("PID_pt", None),
        FieldLenField("PID_num", None, fmt="B", count_of="PIDs",
            adjust=lambda pkt,x:x-(pkt.Flags.R==True)),
        FlagsField("Flags", 0, 8, "rSCQMRBF"),
        ConditionalField(ShortField("Minimal_PID_CP", None),
            lambda pkt:pkt.Flags.M),
        StrFixedLenField("N_sid", "", 16),
        StrFixedLenField("L_sid", "", 20),
        StrFixedLenField("nid_cus", "", 16),
        ConditionalField(StrFixedLenField("nid_pro", "", 16),
            lambda pkt:pkt.Flags.B==False and pkt.Flags.R==True),
        ConditionalField(
            FieldLenField("QoS_len", None, fmt="B", length_of="QoS_requirements"),
            lambda pkt:pkt.Flags.Q==True),
        ConditionalField(
            StrLenField("QoS_requirements", "", length_from=lambda pkt:pkt.QoS_len),
            lambda pkt:pkt.Flags.Q==True),
        ConditionalField(IntField("HMAC", None),
            lambda pkt:pkt.Flags.C==True),
        ConditionalField(IntField("Seg_ID", None),
            lambda pkt:pkt.Flags.S==True),
        FieldListField("PIDs", [""], StrFixedLenField("", "", 4),
            count_from=lambda pkt:pkt.PID_num+(pkt.Flags.R==True))
    ]
    def post_build(self, pkt, pay):
        if self.header_length is None:
            self.header_length = len(pkt)
            pkt = pkt[:6] + int2Bytes(self.header_length, 1) + pkt[7:]
        if self.pkg_length is None:
            self.pkg_length = len(pkt) + len(pay)
            pkt = pkt[:2] + int2BytesLE(self.pkg_length, 2) + pkt[4:]
        if self.checksum is None:
            self.checksum = CalcChecksum(pkt)
            pkt = pkt[:4] + int2Bytes(self.checksum, 2) + pkt[6:]
        # print(self.pkg_length, self.header_length, self.checksum)
        return pkt + pay


if __name__ == '__main__':
    from scapy.all import *
    bind_layers(IP, CoLoR_Data, proto=150)
    bind_layers(IP, CoLoR_Data, {'proto':150})
    a = CoLoR_Data()
    a.N_sid = b'\xff'*16
    a.L_sid = b'\x01'*20
    a.nid_cus = b'\xf0'*16
    a.PIDs = [b'\x90\x01\x22\x11',b'\x99\x01\x66\x55']
    pkt = IP(dst="192.168.50.192")/a
    send(pkt, verbose=0)
