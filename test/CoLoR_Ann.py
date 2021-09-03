# coding = utf-8
''' docstring: 注册包格式 '''

from scapy.all import *
from useful_func import (CalcChecksum, int2BytesLE, int2Bytes)


class CoLoR_Ann(Packet):
    name = "CoLoR_Ann"
    fields_desc = [

    ]
    def post_build(self, pkt, pay):
        pass


class TestSLF(Packet):
    fields_desc=[ FieldLenField("len", None, length_of="data"),
                  StrLenField("data", "", length_from=lambda pkt:pkt.len) ]

class TestPLF(Packet):
    fields_desc=[ FieldLenField("len", None, count_of="plist"),
                  PacketListField("plist", None, IP, count_from=lambda pkt:pkt.len) ]

class TestFLF(Packet):
    fields_desc=[
       FieldLenField("the_lenfield", None, count_of="the_varfield"),
       FieldListField("the_varfield", ["1.2.3.4"], IPField("", "0.0.0.0"),
                       count_from = lambda pkt: pkt.the_lenfield) ]

class TestPkt(Packet):
    fields_desc = [ ByteField("f1",65),
                    ShortField("f2",0x4244) ]
    def extract_padding(self, p):
        return "", p

class TestPLF2(Packet):
    fields_desc = [ FieldLenField("len1", None, count_of="plist",fmt="H", adjust=lambda pkt,x:x),
                    FieldLenField("len2", None, length_of="plist",fmt="I", adjust=lambda pkt,x:x),
                    PacketListField("plist", None, TestPkt, length_from=lambda x:x.len2) ]

test = TestPLF2()
test.show()
