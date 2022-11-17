""" docstring: CoLoR协议所有类型包格式 """

from cryptography.hazmat.primitives import hashes
from scapy.all import (
    Packet, BitField, ByteField, XShortField, LEShortField,
    FieldLenField, FlagsField, StrFixedLenField, FieldListField,
    PacketListField, XStrFixedLenField, ConditionalField, StrLenField,
    LEIntField, ByteEnumField, bind_layers
)
from scapy.layers.inet import IP


COLOR_PROTOCOL_NUMBER = 150


def CalculateCS(tar):
    """ docstring: 校验和计算 tar: bytes字符串 """
    length = len(tar)
    pointer = 0
    sum = 0
    while (length - pointer > 1):
        # print(tar[pointer], tar[pointer+1])
        # 两字节相加
        temp = tar[pointer] << 8
        temp += tar[pointer+1]
        pointer += 2
        sum += temp
    if (length - pointer > 0):
        sum += tar[pointer] << 8
    sum = (sum >> 16) + (sum & 0xffff)
    sum = (sum >> 16) + (sum & 0xffff)  # 防止上一步相加后结果大于16位
    return (sum ^ 0xffff)  # 按位取反后返回


def CalcHMAC(tar):
    """ docstring: 计算hmac tar: bytes字符串 ret: bytes字符串"""
    digest = hashes.Hash(hashes.MD5())
    digest.update(tar)
    return digest.finalize()


def Int2Bytes(data, length):
    """ docstring: 将int类型转成bytes类型 (大端存储)
    data: 目标数字; length: 目标字节数 """
    return data.to_bytes(length, byteorder='big')


def Int2BytesLE(data, length):
    """ docstring: 将int类型转成bytes类型 (小端存储)
    data: 目标数字; length: 目标字节数 """
    return data.to_bytes(length, byteorder='little')


def Ipv42Int(data):
    """ docstring: 将ipv4转化为数字 """
    parts = data.split('.')
    return (int(parts[0]) << 24) + (int(parts[1]) << 16) + (int(parts[2]) << 8) + int(parts[3])


def Int2Ipv4(data):
    """ docstring: 将数字转化为ipv4"""
    return '.'.join([str(data >> (i << 3) & 0xFF) for i in range(4)[::-1]])


class ColorGet(Packet):
    """ docstring: Get包格式 """
    name = "ColorGet"
    fields_desc = [
        BitField("Version", 7, 4, tot_size=1),
        BitField("Type", 2, 4, end_tot_size=1),
        ByteField("TTL", 64),
        LEShortField("Packet_Length", None),
        XShortField("Checksum", None),
        LEShortField("MTU", None),
        FieldLenField("PID_Num", None, fmt="B", count_of="PID_List"),
        FlagsField("Flags", 8, 8, "rCRASQKF"),
        LEShortField("Minimal_PID_CP", None),
        StrFixedLenField("NSID", "", 16),
        StrFixedLenField("LSID", "", 20),
        StrFixedLenField("NID", "", 16),
        ConditionalField(
            FieldLenField("Public_Key_Length", None, fmt="<H", length_of="Public_Key"),
            lambda pkt:pkt.Flags.K == True
        ),
        ConditionalField(
            StrLenField("Public_Key", "", length_from=lambda pkt:pkt.Public_Key_Length),
            lambda pkt:pkt.Flags.K == True
        ),
        ConditionalField(
            FieldLenField("QoS_Length", None, fmt="B", length_of="QoS_Requirements"),
            lambda pkt:pkt.Flags.Q == True
        ),
        ConditionalField(
            StrLenField("QoS_Requirements", "", length_from=lambda pkt:pkt.QoS_Length),
            lambda pkt:pkt.Flags.Q == True
        ),
        ConditionalField(StrFixedLenField("HMAC", "", 16), lambda pkt:pkt.Flags.C == True),
        ConditionalField(LEIntField("Segment_ID", None), lambda pkt:pkt.Flags.S == True),
        FieldListField("PID_List", None, LEIntField("", None), count_from=lambda pkt:pkt.PID_Num),
        # 旧版本原型系统实现：
        ConditionalField(StrFixedLenField("Random_Num", "", 4), lambda pkt:pkt.Flags.R == True),
        # 新版本计划实现如下：
        # ConditionalField(
        #     FieldLenField("Shared_Secret_Key_Length", None, fmt="B", length_of="Shared_Secret_Key"),
        #     lambda pkt:pkt.Flags.R == True
        # ),
        # ConditionalField(
        #     StrLenField("Shared_Secret_Key", "",
        #                 length_from=lambda pkt:pkt.Shared_Secret_Key_Length),
        #     lambda pkt:pkt.Flags.R == True
        # )
    ]

    def post_build(self, pkt, pay):
        if self.Packet_Length is None:
            self.Packet_Length = len(pkt)
            pkt = pkt[:2] + Int2BytesLE(self.Packet_Length, 2) + pkt[4:]
        if self.Checksum is None:
            self.Checksum = CalculateCS(pkt)
            pkt = pkt[:4] + Int2Bytes(self.Checksum, 2) + pkt[6:]
        return pkt + pay


class ColorData(Packet):
    """ docstring: Data包格式 """
    name = 'ColorData'
    fields_desc = [
        BitField("Version", 7, 4, tot_size=1),
        BitField("Type", 3, 4, end_tot_size=1),
        ByteField("TTL", 64),
        LEShortField("Packet_Length", None),
        XShortField("Checksum", None),
        ByteField("Header_Length", None),
        ByteField("PID_Pointer", None),
        FieldLenField("PID_Num", None, fmt="B", count_of="PID_List", adjust=lambda pkt, x:x-(pkt.Flags.R == True)),
        FlagsField("Flags", 0, 8, "rSCQMRBF"),
        ConditionalField(LEShortField("Minimal_PID_CP", None), lambda pkt:pkt.Flags.M),
        StrFixedLenField("NSID", "", 16),
        StrFixedLenField("LSID", "", 20),
        StrFixedLenField("Destination_NID", "", 16),
        ConditionalField(StrFixedLenField("Source_NID", "", 16),
                         lambda pkt:pkt.Flags.B == False and pkt.Flags.R == True),
        ConditionalField(
            FieldLenField("QoS_Length", None, fmt="B", length_of="QoS_Requirements"),
            lambda pkt:pkt.Flags.Q == True
        ),
        ConditionalField(
            StrLenField("QoS_Requirements", "", length_from=lambda pkt:pkt.QoS_Length),
            lambda pkt:pkt.Flags.Q == True
        ),
        ConditionalField(StrFixedLenField("HMAC", "", 4), lambda pkt:pkt.Flags.C == True),
        ConditionalField(LEIntField("Segment_ID", None), lambda pkt:pkt.Flags.S == True),
        FieldListField("PID_List", [0], LEIntField("", None), count_from=lambda pkt:pkt.PID_Num+(pkt.Flags.R == True))
    ]

    def post_build(self, pkt, pay):
        if self.Header_Length is None:
            self.Header_Length = len(pkt)
            pkt = pkt[:6] + Int2Bytes(self.Header_Length, 1) + pkt[7:]
        if self.Packet_Length is None:
            self.Packet_Length = len(pkt) + len(pay)
            pkt = pkt[:2] + Int2BytesLE(self.Packet_Length, 2) + pkt[4:]
        # print(self.Packet_Length, self.Header_Length)
        # warning: 此处将RN先放置于该包HMAC处，提取出后计算结果再放回
        if self.Flags.C:
            hmac_offset = 62 + 2*self.Flags.M + \
                16*(self.Flags.R & ~self.Flags.B)
            hmac_offset += self.Qos_len+1 if self.Flags.Q else 0
            hmac_start = 10 + 2*self.Flags.M
            hmac_bytes = CalcHMAC(pkt[hmac_start:hmac_offset] + Int2Bytes(0, 4) +
                                  pkt[hmac_offset+4:] + pay + pkt[hmac_offset:hmac_offset+4])
            # print((pkt[hmac_start:hmac_offset] + Int2Bytes(0, 4) + pkt[hmac_offset+4:] + pay + pkt[hmac_offset:hmac_offset+4]).hex())
            # print(hmac_bytes.hex())
            self.HMAC = hmac_bytes[-4:]
            pkt = pkt[:hmac_offset] + self.HMAC + pkt[hmac_offset+4:]
        if self.Checksum is None:
            self.Checksum = CalculateCS(pkt)
            pkt = pkt[:4] + Int2Bytes(self.Checksum, 2) + pkt[6:]
        # print(self.Checksum)
        return pkt + pay


class Strategy_Unit(Packet):
    """ docstring: 通告策略单元 """
    name = "Strategy_Unit"
    fields_desc = [
        ByteField("Type", 0),
        FieldLenField("Length", None, fmt="B", length_of="Value"),
        StrLenField("Value", "", length_from=lambda pkt:pkt.Length)
    ]

    def extract_padding(self, s):
        return "", s


class Announce_Unit(Packet):
    """ docstring: 通告单元 """
    name = "Announce_Unit"
    fields_desc = [
        BitField("N", 1, 1, tot_size=1),
        BitField("L", 1, 1),
        BitField("I", 1, 1),
        BitField("AM", 1, 2),  # 1注册，2更新，3取消
        BitField("r", 0, 3, end_tot_size=1),
        ByteField("Unit_Length", None),
        FieldLenField("Strategy_Num", None, fmt="B",
                      count_of="Strategy_Unit_List"),
        ConditionalField(
            XStrFixedLenField("NSID", "", 16),
            lambda pkt: pkt.N == 1
        ),
        ConditionalField(
            XStrFixedLenField("LSID", "", 20),
            lambda pkt: pkt.L == 1
        ),
        ConditionalField(
            XStrFixedLenField("NID", "", 16),
            lambda pkt: pkt.I == 1
        ),
        PacketListField("Strategy_Unit_List", None, Strategy_Unit,
                        count_from=lambda pkt:pkt.Strategy_Num)
    ]

    def post_build(self, pkt, pay):
        if self.Unit_Length is None:
            self.Unit_Length = len(pkt)
            pkt = pkt[:1] + Int2Bytes(self.Unit_Length, 1) + pkt[2:]
        return pkt + pay

    def extract_padding(self, s):
        return "", s


class ColorAnnounce(Packet):
    """ docstring: 注册包格式 """
    name = "ColorAnnounce"
    fields_desc = [
        BitField("Version", 7, 4, tot_size=1),
        BitField("Type", 1, 4, end_tot_size=1),
        ByteField("TTL", 64),
        LEShortField("Packet_Length", None),
        XShortField("Checksum", None),
        FlagsField("Flags", 0, 8, "rrrrCPKF"),
        BitField("Unit_Num", None, 4, tot_size=1),
        BitField("PX_Num", None, 4, end_tot_size=1),
        PacketListField("Announce_Unit_List", None, Announce_Unit, count_from=lambda pkt:pkt.Unit_Num),
        ConditionalField(
            FieldLenField("Public_Key_Length", None, fmt="<H", length_of="Public_Key"),
            lambda pkt:pkt.Flags.K == True
        ),
        ConditionalField(
            StrLenField("Public_Key", "", length_from=lambda pkt:pkt.Public_Key_Length),
            lambda pkt:pkt.Flags.K == True
        ),
        ConditionalField(
            FieldLenField("AS_Path_Num", None, fmt="B", count_of="AID_List"),
            lambda pkt:pkt.Flags.P == True
        ),
        ConditionalField(
            FieldListField("AID_List", None, StrFixedLenField("", "", 1), count_from=lambda pkt:pkt.AS_Path_Num),
            lambda pkt:pkt.Flags.P == True
        ),
        ConditionalField(StrFixedLenField("HMAC", "", 16), lambda pkt:pkt.Flags.C == True),
        FieldListField("PX_List", None, StrFixedLenField("", "", 2), count_from=lambda pkt:pkt.PX_Num)
    ]

    def post_build(self, pkt, pay):
        if self.Packet_Length is None:
            self.Packet_Length = len(pkt)
            pkt = pkt[:2] + Int2BytesLE(self.Packet_Length, 2) + pkt[4:]
        if self.Unit_Num is None and self.PX_Num is None:
            self.Unit_Num = len(self.Announce_Unit_List)
            self.PX_Num = len(self.PX_List)
            pkt = pkt[:7] + Int2Bytes(self.Unit_Num <<
                                      4 | self.PX_Num, 1) + pkt[8:]
        if self.Checksum is None:
            self.Checksum = CalculateCS(pkt)
            pkt = pkt[:4] + Int2Bytes(self.Checksum, 2) + pkt[6:]
        return pkt + pay


class IP_NID(Packet):
    """ docstring: IP-NID映射条目 """
    name = 'IP_NID'
    fields_desc = [
        LEIntField("IP", None),
        StrFixedLenField("NID", "", 16)
    ]

    def extract_padding(self, s):
        return "", s


class PX_IP(Packet):
    """ docstring: PX-IP映射条目 """
    name = 'PX_IP'
    fields_desc = [
        LEShortField("PX", None),
        LEIntField("IP", None)
    ]

    def extract_padding(self, s):
        return "", s


class ASInfo(Packet):
    """ docstring: 域内信息同步表 """
    name = 'ASInfo'
    fields_desc = [
        FieldLenField("IP_NID_Num", None, count_of="IP_NID_List", fmt='B'),
        PacketListField("IP_NID_List", None, IP_NID, count_from=lambda pkt:pkt.IP_NID_Num),
        FieldLenField("PX_IP_Num", None, count_of="PX_IP_List", fmt='B'),
        PacketListField("PX_IP_List", None, PX_IP, count_from=lambda pkt:pkt.PX_IP_Num),
    ]


class AttackSummaryUnit(Packet):
    """ docstring: 攻击信息概要单元 """
    name = 'AttackSummaryUnit'
    fields_desc = [
        ByteField("ASID", None),
        LEIntField("Attack_Num", None)
    ]

    def extract_padding(self, s):
        return "", s


class AttackInfo(Packet):
    """ docstring: 攻击信息表 """
    name = 'AttackInfo'
    fields_desc = [
        StrFixedLenField("BR_NID", "", 16),
        PacketListField("Attack_List", None, AttackSummaryUnit,
                        next_cls_cb=lambda a, b, c, d:AttackSummaryUnit)
    ]


class ColorControl(Packet):
    """ docstring: 控制包格式 """
    name = 'ColorControl'
    Subtypes = {
        1: "CONFIG_RM", 2: "CONFIG_RM_ACK", 3: "CONFIG_BR", 4: "CONFIG_BR_ACK",
        5: "PROXY_REGISTER", 6: "PROXY_REGISTER_REPLY", 7: "PROXY_REGISTER_REPLY_ACK",
        8: "CONFIG_PROXY", 9: "CONFIG_PROXY_ACK",
        10: "CONFIG_RM_STRATEGY", 11: "CONFIG_RM_STRATEGY_ACK",
        16: "ODC_ADD_ENTRY", 17: "ODC_WARNING", 18: "ATTACK_WARNING"
    }
    fields_desc = [
        BitField("Version", 7, 4, tot_size=1),
        BitField("Type", 4, 4, end_tot_size=1),
        ByteField("TTL", 64),
        XShortField("Checksum", None),
        ByteField("Header_Length", 8),
        ByteEnumField("Subtype", None, Subtypes),
        LEShortField("Packet_Length", None)
    ]

    def post_build(self, pkt, pay):
        if self.Packet_Length is None:
            self.Packet_Length = len(pay)
            pkt = pkt[:6] + Int2BytesLE(self.Packet_Length, 2) + pkt[8:]
        if self.Checksum is None:
            self.Checksum = CalculateCS(pkt + pay)
            pkt = pkt[:2] + Int2Bytes(self.Checksum, 2) + pkt[4:]
        return pkt + pay

    def guess_payload_class(self, payload):
        if self.Subtype == "PROXY_REGISTER" or self.Subtype == "CONFIG_PROXY":
            return IP_NID
        elif self.Subtype == "PROXY_REGISTER_REPLY":
            return ASInfo
        elif self.Subtype == "ODC_WARNING":
            return IP
        elif self.Subtype == "ATTACK_WARNING":
            return AttackInfo
        return super().guess_payload_class(payload)


# 用于构建时自动填写Tag字段
bind_layers(ColorControl, IP_NID, {'Subtype': 5})
bind_layers(ColorControl, ASInfo, {'Subtype': 6})
bind_layers(ColorControl, IP, {'Subtype': 17})
bind_layers(ColorControl, AttackInfo, {'Subtype': 18})


def newIP_guess_payload_class(self, payload):
    """ docstring: 重载IP层负载猜测函数, 添加color协议 """
    if self.proto == COLOR_PROTOCOL_NUMBER:
        if payload[0] == 113:
            return ColorAnnounce
        elif payload[0] == 114:
            return ColorGet
        elif payload[0] == 115:
            return ColorData
        elif payload[0] == 116:
            return ColorControl
    return super(IP, self).guess_payload_class(payload)


# 用于IP报文负载推测和自动填写proto字段
IP.guess_payload_class = newIP_guess_payload_class
bind_layers(IP, ColorAnnounce, {'proto': COLOR_PROTOCOL_NUMBER})
bind_layers(IP, ColorGet, {'proto': COLOR_PROTOCOL_NUMBER})
bind_layers(IP, ColorData, {'proto': COLOR_PROTOCOL_NUMBER})
bind_layers(IP, ColorControl, {'proto': COLOR_PROTOCOL_NUMBER})


if __name__ == '__main__':
    # 使用样例 构造测试
    from scapy.all import send, hexdump
    pkt = IP(dst="192.168.50.1")

    # 生成get包
    cg = ColorGet()
    cg.NSID = b'\xff'*16
    cg.LSID = b'\x01'*20
    cg.NID = b'\xa5'*16
    cg.PID_List = [int('01234567', 16), int('98765432', 16)]
    # (pkt/cg).show2()
    send(pkt/cg, verbose=0)

    # 生成get包，带Random_number
    cg = ColorGet()
    cg.NSID = bytes.fromhex("d23454d19f307d8b98ff2da277c0b546")
    cg.LSID = bytes.fromhex("a9dd379c69638ad6656b2df1dec4804ce760106a")
    cg.NID = bytes.fromhex("b0cd69ef142db5a471676ad710eebf3a")
    cg.PID_List = [int('01234567', 16), int('98765432', 16)]
    cg.Flags.R = True
    cg.Random_Num = bytes.fromhex("12345678")
    # (pkt/cg).show2()
    send(pkt/cg, verbose=0)

    # 生成data包
    cd = ColorData()
    cd.NSID = b'\xff'*16
    cd.LSID = b'\x01'*20
    cd.Destination_NID = b'\xa5'*16
    cd.Source_NID = b'\x5a'*16
    cd.PID_List = [int('98765432', 16), int('01234567', 16), 0]
    # (pkt/cd).show2()
    send(pkt/cd, verbose=0)

    # 生成get包，并测试hmac计算
    cd = ColorData()
    cd.NSID = b'\xff'*16
    cd.LSID = b'\x01'*20
    cd.Destination_NID = b'\xa5'*16
    cd.Source_NID = b'\x5a'*16
    cd.Flags.R = True
    cd.Flags.C = True
    cd.HMAC = b'\x12\x34\x56\x78'
    cd.PID_List = [int('98765432', 16), int('01234567', 16), 0]
    # (pkt/cd).show2()
    send(pkt/cd, verbose=0)

    # 生成announce包
    su = Strategy_Unit(Type=1, Length=1, Value=b"\x12")
    # su.show2()
    au = Announce_Unit(AM=1, Strategy_Unit_List=[su, su])
    # au.show2()
    au.NSID = b'\x01'*16
    au.LSID = b'\x02'*20
    au.NID = b'\x03'*16
    ca = ColorAnnounce(Announce_Unit_List=[au, au])
    # (pkt/ca).show2()
    send(pkt/ca, verbose=0)

    # 生成control包，带IP_NID
    ipNIDitem = IP_NID(IP=Ipv42Int("192.168.50.62"), NID=b"\xf0"*16)
    cc = ColorControl()/ipNIDitem
    # (pkt/cc).show2()
    send(pkt/cc, verbose=0)

    # 生成control包，带ASinfo
    pxipitem = PX_IP(PX=0x1122, IP=Ipv42Int("192.168.50.38"))
    asi = ASInfo(IP_NID_List=[ipNIDitem]*3, PX_IP_List=[pxipitem]*5)
    cc = ColorControl()/asi
    # (pkt/cc).show2()
    send(pkt/cc, verbose=0)

    # 生成control包，带AttackInfo
    asu = AttackSummaryUnit(ASID=5, Attack_Num=6666)
    ai = AttackInfo(Attack_List=[asu]*3)
    cc = ColorControl()/ai
    # (pkt/cc).show2()
    send(pkt/cc, verbose=0)

    # 生成control包，带IP头
    ipu = IP(src="1.1.1.1", dst="2.2.2.2")
    cc = ColorControl()/ipu
    # (pkt/cc).show2()
    send(pkt/cc, verbose=0)
