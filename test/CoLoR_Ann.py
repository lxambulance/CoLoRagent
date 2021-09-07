# coding = utf-8
''' docstring: 注册包格式 '''


from scapy.all import (
    Packet, ByteField, FieldLenField, StrLenField, BitField, ConditionalField,
    StrFixedLenField, PacketListField, LEShortField, XShortField, FlagsField, 
    FieldListField, XStrFixedLenField
)
from useful_func import (CalcChecksum, int2BytesLE, int2Bytes)


class Strategy_unit(Packet):
    name = "CoLoR_Ann_Strategy_unit"
    fields_desc = [
        ByteField("tag", 0),
        FieldLenField("length", None, fmt="B", length_of="value"),
        StrLenField("value", "", length_from=lambda pkt:pkt.length)
    ]
    def extract_padding(self, s):
        return "", s

class Ann_unit(Packet):
    name = "CoLoR_Ann_unit"
    fields_desc = [
        BitField("N", 1, 1, tot_size=1),
        BitField("L", 1, 1),
        BitField("I", 1, 1),
        BitField("AM", 1, 2), # 1注册，2更新，3取消
        BitField("r", 0, 3, end_tot_size=1),
        ByteField("Unit_length", None),
        FieldLenField("Strategy_N", None, fmt="B", count_of="Strategy_unit_list"),
        ConditionalField(
            XStrFixedLenField("N_sid", "", 16),
            lambda pkt: pkt.N == 1
        ),
        ConditionalField(
            XStrFixedLenField("L_sid", "", 20),
            lambda pkt: pkt.L == 1
        ),
        ConditionalField(
            XStrFixedLenField("nid", "", 16),
            lambda pkt: pkt.I == 1
        ),
        PacketListField("Strategy_unit_list", None, Strategy_unit, count_from=lambda pkt:pkt.Strategy_N)
    ]
    def post_build(self, pkt, pay):
        if self.Unit_length is None:
            self.Unit_length = len(pkt)
            pkt = pkt[:1] + int2Bytes(self.Unit_length,1) + pkt[2:]
        return pkt + pay

class CoLoR_Ann(Packet):
    name = "CoLoR_Ann"
    fields_desc = [
        BitField("Version", 7, 4, tot_size=1),
        BitField("Package", 1, 4, end_tot_size=1),
        ByteField("TTL", 64),
        LEShortField("pkg_length", None),
        XShortField("checksum", None),
        FlagsField("Flags", 0, 8, "rrrrrPKF"),
        BitField("unit_num", None, 4, tot_size=1),
        BitField("PX_num", None, 4, end_tot_size=1),
        PacketListField("Announce_unit_list", None, Ann_unit, count_from=lambda pkt:pkt.unit_num),
        ConditionalField(
            FieldLenField("Public_key_len", None, fmt="H", length_of="Public_key"),
            lambda pkt:pkt.Flags.K==True
        ),
        ConditionalField(
            StrLenField("Public_key", "", length_from=lambda pkt:pkt.Public_key_len),
            lambda pkt:pkt.Flags.K==True
        ),
        ConditionalField(
            FieldLenField("AS_PATH_len", None, fmt="B", count_of="AID_list"),
            lambda pkt:pkt.Flags.P==True
        ),
        ConditionalField(
            FieldListField("AID_list", None, StrFixedLenField("","",1), count_from=lambda pkt:pkt.AS_PATH_len),
            lambda pkt:pkt.Flags.P==True
        ),
        FieldListField("PX_list", None, StrFixedLenField("", "", 2), count_from=lambda pkt:pkt.PX_num)
    ]
    def post_build(self, pkt, pay):
        if self.pkg_length is None:
            self.pkg_length = len(pkt)
            pkt = pkt[:2] + int2BytesLE(self.pkg_length,2) + pkt[4:]
        if self.checksum is None:
            self.checksum = CalcChecksum(pkt)
            pkt = pkt[:4] + int2Bytes(self.checksum, 2) + pkt[6:]
        if self.unit_num is None and self.PX_num is None:
            self.unit_num = len(self.Announce_unit_list)
            self.PX_num = len(self.PX_list)
            pkt = pkt[:7] + int2Bytes(self.unit_num << 4 | self.PX_num, 1) + pkt[8:]
        return pkt + pay


if __name__ == '__main__':
    from scapy.all import *
    bind_layers(IP, CoLoR_Ann, proto=150)
    bind_layers(IP, CoLoR_Ann, {'proto':150})
    testpkt1 = "71403f0028750010e83700b0cd69ef142db5a471676ad710eebf3adb8ac1c259eb89d4a131b253bacfca5f319d54f2b0cd69ef142db5a471676ad710eebf3a"
    testpkt1 = bytes.fromhex(testpkt1)
    pkt1 = CoLoR_Ann(testpkt1)
    pkt1.show()
    testpkt2 = "71403f0018750010f83700b0cd69ef142db5a471676ad710eebf3adb8ac1c259eb89d4a131b253bacfca5f319d54f2b0cd69ef142db5a471676ad710eebf3a"
    testpkt2 = bytes.fromhex(testpkt2)
    pkt2 = CoLoR_Ann(testpkt2)
    pkt2.show()
    testpkt3 = "71404700155e0010e83f02b0cd69ef142db5a471676ad710eebf3adb8ac1c259eb89d4a131b253bacfca5f319d54f2b0cd69ef142db5a471676ad710eebf3a0101080203020304"
    testpkt3 = bytes.fromhex(testpkt3)
    pkt3 = CoLoR_Ann(testpkt3)
    pkt3.show()

    su = Strategy_unit(tag = 1, length = 1, value = b"\x12")
    su.show2()
    au = Ann_unit(AM = 1, Strategy_unit_list = [su, su])
    au.N_sid = b'\x01'*16
    au.L_sid = b'\x02'*20
    au.nid = b'\x03'*16
    au.show2()
    pkt = CoLoR_Ann(Announce_unit_list = [au])
    pkt.show()
    pkt.show2()
