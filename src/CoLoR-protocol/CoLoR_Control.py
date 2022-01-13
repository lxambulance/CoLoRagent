# coding=utf-8


from scapy.all import *
from useful_func import (int2BytesLE, CalcChecksum, int2Bytes)


class CoLoR_Control(Packet):
    name = 'CoLoR_Control'
    tags = {
        1: "CONFIG_RM", 2: "CONFIG_RM_ACK", 3: "CONFIG_BR", 4: "CONFIG_BR_ACK",
        5: "PROXY_REGISTER", 6: "PROXY_REGISTER_REPLY", 7: "PROXY_REGISTER_REPLY_ACK",
        8: "CONFIG_PROXY", 9: "CONFIG_PROXY_ACK",
        10: "CONFIG_RM_STRATEGY", 11: "CONFIG_RM_STRATEGY_ACK",
        16: "ODC_ADD_ENTRY", 17: "ODC_WARNING", 18: "ATTACK_WARNING"
    }
    fields_desc = [
        BitField("Version", 7, 4, tot_size=1),
        BitField("Package", 4, 4, end_tot_size=1),
        ByteField("TTL", 64),
        XShortField("checksum", None),
        ByteField("header_length", 8),
        ByteEnumField("tag", None, tags),
        LEShortField("pkg_length", None)
    ]
    def post_build(self, pkt, pay):
        if self.pkg_length is None:
            self.pkg_length = len(pay)
            pkt = pkt[:6] + int2BytesLE(self.pkg_length,2) + pkt[8:]
        if self.checksum is None:
            self.checksum = CalcChecksum(pkt)
            pkt = pkt[:2] + int2Bytes(self.checksum, 2) + pkt[4:]
        return pkt + pay


class IP_nid(Packet):
    name = 'IP_nid'
    fields_desc = [
        LEIntField("IP", None),
        StrFixedLenField("nid", "", 16)
    ]


class nid_IP(Packet):
    name = 'nid_IP'
    fields_desc = [
        StrFixedLenField("nid", "", 16),
        LEIntField("IP", None)
    ]


class PX_IP(Packet):
    name = 'PX_IP'
    fields_desc = [
        LEShortField("PX", None),
        LEIntField("IP", None)
    ]


class ASinfo(Packet):
    name = 'ASinfo'
    fields_desc = [
        FieldLenField("nid_ip_num", None, count_of="nid_ip_list"),
        PacketListField("nid_ip_list", None, nid_IP, count_from=lambda pkt:pkt.nid_ip_num),
        FieldLenField("px_ip_num", None, count_of="px_ip_list"),
        PacketListField("px_ip_list", None, PX_IP, count_from=lambda pkt:pkt.px_ip_num),
    ]


class attackSummary(Packet):
    name = 'attackSummary'
    fields_desc = [
        ByteField('ASid', None),
        LEIntField('attack_num', None)
    ]


class attackInfo(Packet):
    name = 'attackInfo'
    fields_desc = [
        StrFixedLenField("BR_nid", "", 16),
        PacketListField('attack_list', None, attackSummary,
            count_from=lambda pkt:(pkt.pkg_length-16)//5)
    ]


# 用于解析时推导负载字段
bind_layers(CoLoR_Control, IP_nid, tag="PROXY_REGISTER")
bind_layers(CoLoR_Control, IP_nid, tag="CONFIG_PROXY")
bind_layers(CoLoR_Control, ASinfo, tag="PROXY_REGISTER_REPLY")
bind_layers(CoLoR_Control, IP, tag="ODC_WARNING")
bind_layers(CoLoR_Control, attackInfo, tag="ATTACK_WARNING")


# 用于构建时自动填写tag字段
bind_layers(CoLoR_Control, IP_nid, {'tag':5})
bind_layers(CoLoR_Control, ASinfo, {'tag':6})
bind_layers(CoLoR_Control, IP, {'tag':17})
bind_layers(CoLoR_Control, attackInfo, {'tag':18})


if __name__ == '__main__':
    # bind_layers(IP, CoLoR_Control, proto=150)
    # bind_layers(IP, CoLoR_Control, {'proto':150})
    pass
