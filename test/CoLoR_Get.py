from scapy.all import *
from useful_func import (
    CalcChecksum, int2BytesLE, int2Bytes)


class CoLoR_Get(Packet):
    name = "CoLoR_Get"
    fields_desc=[
        BitField("Version", 7, 4, tot_size=1),
        BitField("Package", 2, 4, end_tot_size=1),
        ByteField("TTL", 64),
        ShortField("pkg_length", None),
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
