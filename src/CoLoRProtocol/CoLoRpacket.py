''' docstring: CoLoR协议所有类型包格式 '''


from scapy.all import (
    Packet, BitField, ByteField, ShortField, XShortField, LEShortField,
    FieldLenField, FlagsField, StrFixedLenField, FieldListField,
    PacketListField, XStrFixedLenField, ConditionalField, StrLenField,
    IntField, LEIntField, ByteEnumField, bind_layers, IP
)


from cryptography.hazmat.primitives import hashes


def CalcHMAC(tar):
    ''' docstring: 计算hmac tar: bytes字符串 ret: bytes字符串'''
    digest = hashes.Hash(hashes.MD5())
    digest.update(tar)
    return digest.finalize()


def CalcChecksum(tar):
    ''' docstring: 校验和计算 tar: bytes字符串 ret: int '''
    length = len(tar)
    pointer = 0
    sum = 0
    while (length - pointer > 1):
        # 两字节相加
        temp = tar[pointer] << 8
        temp += tar[pointer+1]
        pointer += 2
        sum += temp
    if (length - pointer > 0):
        sum += tar[pointer] << 8  # 易出错步骤，注意！
    sum = (sum >> 16) + (sum & 0xffff)
    sum = (sum >> 16) + (sum & 0xffff)  # 防止上一步相加后结果大于16位
    return (sum ^ 0xffff)  # 按位取反后返回


def Int2Bytes(data, length):
    ''' docstring: 将int类型转成bytes类型 (大端存储)
    data: 目标数字; length: 目标字节数 '''
    return data.to_bytes(length, byteorder='big')


def Int2BytesLE(data, length):
    ''' docstring: 将int类型转成bytes类型 (小端存储)
    data: 目标数字; length: 目标字节数 '''
    return data.to_bytes(length, byteorder='little')


def Ipv42Int(data):
    ''' docstring: 将ipv4转化为数字 '''
    parts = data.split('.')
    return (int(parts[0]) << 24) + (int(parts[1]) << 16) + (int(parts[2]) << 8) + int(parts[3])


def Int2Ipv4(data):
    ''' docstring: 将数字转化为ipv4'''
    return '.'.join([str(data >> (i << 3) & 0xFF) for i in range(4)[::-1]])


class ColorGet(Packet):
    ''' docstring: Get包格式 '''
    name = "ColorGet"
    fields_desc = [
        BitField("Version", 7, 4, tot_size=1),
        BitField("Package", 2, 4, end_tot_size=1),
        ByteField("TTL", 64),
        LEShortField("pkg_length", None),
        XShortField("checksum", None),
        ShortField("MTU", None),
        FieldLenField("PID_num", None, fmt="B", count_of="PIDs"),
        FlagsField("Flags", 8, 8, "rrRASQKF"),
        ShortField("Minimal_PID_CP", None),
        StrFixedLenField("N_sid", "", 16),
        StrFixedLenField("L_sid", "", 20),
        StrFixedLenField("nid", "", 16),
        ConditionalField(
            FieldLenField("Public_key_len", None, fmt="H",
                          length_of="Public_key"),
            lambda pkt:pkt.Flags.K == True),
        ConditionalField(
            StrLenField("Public_key", "",
                        length_from=lambda pkt:pkt.Public_key_len),
            lambda pkt:pkt.Flags.K == True),
        ConditionalField(
            FieldLenField("QoS_len", None, fmt="B",
                          length_of="QoS_requirements"),
            lambda pkt:pkt.Flags.Q == True),
        ConditionalField(
            StrLenField("QoS_requirements", "",
                        length_from=lambda pkt:pkt.QoS_len),
            lambda pkt:pkt.Flags.Q == True),
        ConditionalField(
            IntField("Seg_ID", None),
            lambda pkt:pkt.Flags.S == True),
        FieldListField(
            "PIDs", None, StrFixedLenField("", "", 4),
            count_from=lambda pkt:pkt.PID_num),
        ConditionalField(
            StrFixedLenField("Random_num", "", 4),
            lambda pkt:pkt.Flags.R == True
        )
    ]

    def post_build(self, pkt, pay):
        if self.pkg_length is None:
            self.pkg_length = len(pkt)
            pkt = pkt[:2] + Int2BytesLE(self.pkg_length, 2) + pkt[4:]
        if self.checksum is None:
            self.checksum = CalcChecksum(pkt)
            pkt = pkt[:4] + Int2Bytes(self.checksum, 2) + pkt[6:]
        return pkt + pay


class ColorData(Packet):
    ''' docstring: Data包格式 '''
    name = 'ColorData'
    fields_desc = [
        BitField("Version", 7, 4, tot_size=1),
        BitField("Package", 3, 4, end_tot_size=1),
        ByteField("TTL", 64),
        LEShortField("pkg_length", None),
        XShortField("checksum", None),
        ByteField("header_length", None),
        ByteField("PID_pt", None),
        FieldLenField("PID_num", None, fmt="B", count_of="PIDs",
                      adjust=lambda pkt, x:x-(pkt.Flags.R == True)),
        FlagsField("Flags", 0, 8, "rSCQMRBF"),
        ConditionalField(ShortField("Minimal_PID_CP", None),
                         lambda pkt:pkt.Flags.M),
        StrFixedLenField("N_sid", "", 16),
        StrFixedLenField("L_sid", "", 20),
        StrFixedLenField("nid_cus", "", 16),
        ConditionalField(StrFixedLenField("nid_pro", "", 16),
                         lambda pkt:pkt.Flags.B == False and pkt.Flags.R == True),
        ConditionalField(
            FieldLenField("QoS_len", None, fmt="B",
                          length_of="QoS_requirements"),
            lambda pkt:pkt.Flags.Q == True),
        ConditionalField(
            StrLenField("QoS_requirements", "",
                        length_from=lambda pkt:pkt.QoS_len),
            lambda pkt:pkt.Flags.Q == True),
        ConditionalField(StrFixedLenField("HMAC", "", 4),
                         lambda pkt:pkt.Flags.C == True),
        ConditionalField(LEIntField("Seg_ID", None),
                         lambda pkt:pkt.Flags.S == True),
        FieldListField("PIDs", [""], StrFixedLenField("", "", 4),
                       count_from=lambda pkt:pkt.PID_num+(pkt.Flags.R == True))
    ]

    def post_build(self, pkt, pay):
        if self.header_length is None:
            self.header_length = len(pkt)
            pkt = pkt[:6] + Int2Bytes(self.header_length, 1) + pkt[7:]
        if self.pkg_length is None:
            self.pkg_length = len(pkt) + len(pay)
            pkt = pkt[:2] + Int2BytesLE(self.pkg_length, 2) + pkt[4:]
        # print(self.pkg_length, self.header_length)
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
        if self.checksum is None:
            self.checksum = CalcChecksum(pkt)
            pkt = pkt[:4] + Int2Bytes(self.checksum, 2) + pkt[6:]
        # print(self.checksum)
        return pkt + pay


class Strategy_unit(Packet):
    ''' docstring: 通告策略单元 '''
    name = "ColorAnn_Strategy_unit"
    fields_desc = [
        ByteField("tag", 0),
        FieldLenField("length", None, fmt="B", length_of="value"),
        StrLenField("value", "", length_from=lambda pkt:pkt.length)
    ]

    def extract_padding(self, s):
        return "", s


class Ann_unit(Packet):
    ''' docstring: 通告单元 '''
    name = "ColorAnn_unit"
    fields_desc = [
        BitField("N", 1, 1, tot_size=1),
        BitField("L", 1, 1),
        BitField("I", 1, 1),
        BitField("AM", 1, 2),  # 1注册，2更新，3取消
        BitField("r", 0, 3, end_tot_size=1),
        ByteField("Unit_length", None),
        FieldLenField("Strategy_N", None, fmt="B",
                      count_of="Strategy_unit_list"),
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
        PacketListField("Strategy_unit_list", None, Strategy_unit,
                        count_from=lambda pkt:pkt.Strategy_N)
    ]

    def post_build(self, pkt, pay):
        if self.Unit_length is None:
            self.Unit_length = len(pkt)
            pkt = pkt[:1] + Int2Bytes(self.Unit_length, 1) + pkt[2:]
        return pkt + pay

    def extract_padding(self, s):
        return "", s


class ColorAnn(Packet):
    ''' docstring: 注册包格式 '''
    name = "ColorAnn"
    fields_desc = [
        BitField("Version", 7, 4, tot_size=1),
        BitField("Package", 1, 4, end_tot_size=1),
        ByteField("TTL", 64),
        LEShortField("pkg_length", None),
        XShortField("checksum", None),
        FlagsField("Flags", 0, 8, "rrrrrPKF"),
        BitField("unit_num", None, 4, tot_size=1),
        BitField("PX_num", None, 4, end_tot_size=1),
        PacketListField("Announce_unit_list", None, Ann_unit,
                        count_from=lambda pkt:pkt.unit_num),
        ConditionalField(
            FieldLenField("Public_key_len", None, fmt="H",
                          length_of="Public_key"),
            lambda pkt:pkt.Flags.K == True
        ),
        ConditionalField(
            StrLenField("Public_key", "",
                        length_from=lambda pkt:pkt.Public_key_len),
            lambda pkt:pkt.Flags.K == True
        ),
        ConditionalField(
            FieldLenField("AS_PATH_len", None, fmt="B", count_of="AID_list"),
            lambda pkt:pkt.Flags.P == True
        ),
        ConditionalField(
            FieldListField("AID_list", None, StrFixedLenField(
                "", "", 1), count_from=lambda pkt:pkt.AS_PATH_len),
            lambda pkt:pkt.Flags.P == True
        ),
        FieldListField("PX_list", None, StrFixedLenField(
            "", "", 2), count_from=lambda pkt:pkt.PX_num)
    ]

    def post_build(self, pkt, pay):
        if self.pkg_length is None:
            self.pkg_length = len(pkt)
            pkt = pkt[:2] + Int2BytesLE(self.pkg_length, 2) + pkt[4:]
        if self.unit_num is None and self.PX_num is None:
            self.unit_num = len(self.Announce_unit_list)
            self.PX_num = len(self.PX_list)
            pkt = pkt[:7] + Int2Bytes(self.unit_num <<
                                      4 | self.PX_num, 1) + pkt[8:]
        if self.checksum is None:
            self.checksum = CalcChecksum(pkt)
            pkt = pkt[:4] + Int2Bytes(self.checksum, 2) + pkt[6:]
        return pkt + pay


class IP_NID(Packet):
    ''' docstring: IP-nid映射条目 '''
    name = 'IP_NID'
    fields_desc = [
        LEIntField("IP", None),
        StrFixedLenField("nid", "", 16)
    ]

    def extract_padding(self, s):
        return "", s


class PX_IP(Packet):
    ''' docstring: PX-IP映射条目 '''
    name = 'PX_IP'
    fields_desc = [
        LEShortField("PX", None),
        LEIntField("IP", None)
    ]

    def extract_padding(self, s):
        return "", s


class ASinfo(Packet):
    ''' docstring: 域内信息同步表 '''
    name = 'ASinfo'
    fields_desc = [
        FieldLenField("ip_nid_num", None, count_of="ip_nid_list", fmt='B'),
        PacketListField("ip_nid_list", None, IP_NID,
                        count_from=lambda pkt:pkt.ip_nid_num),
        FieldLenField("px_ip_num", None, count_of="px_ip_list", fmt='B'),
        PacketListField("px_ip_list", None, PX_IP,
                        count_from=lambda pkt:pkt.px_ip_num),
    ]


class AttackSummaryUnit(Packet):
    ''' docstring: 攻击信息概要单元 '''
    name = 'AttackSummaryUnit'
    fields_desc = [
        ByteField('ASid', None),
        LEIntField('attack_num', None)
    ]

    def extract_padding(self, s):
        return "", s


class AttackInfo(Packet):
    ''' docstring: 攻击信息表 '''
    name = 'AttackInfo'
    fields_desc = [
        StrFixedLenField("BR_nid", "", 16),
        PacketListField('attack_list', None, AttackSummaryUnit,
                        next_cls_cb=lambda a, b, c, d:AttackSummaryUnit)
    ]


class ColorControl(Packet):
    ''' docstring: 控制包格式 '''
    name = 'ColorControl'
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
            pkt = pkt[:6] + Int2BytesLE(self.pkg_length, 2) + pkt[8:]
        if self.checksum is None:
            self.checksum = CalcChecksum(pkt + pay)
            pkt = pkt[:2] + Int2Bytes(self.checksum, 2) + pkt[4:]
        return pkt + pay

    def guess_payload_class(self, payload):
        if self.tag == "PROXY_REGISTER" or self.tag == "CONFIG_PROXY":
            return IP_NID
        elif self.tag == "PROXY_REGISTER_REPLY":
            return ASinfo
        elif self.tag == "ODC_WARNING":
            return IP
        elif self.tag == "ATTACK_WARNING":
            return AttackInfo
        return super().guess_payload_class(payload)


# 用于构建时自动填写tag字段
bind_layers(ColorControl, IP_NID, {'tag': 5})
bind_layers(ColorControl, ASinfo, {'tag': 6})
bind_layers(ColorControl, IP, {'tag': 17})
bind_layers(ColorControl, AttackInfo, {'tag': 18})


def newIP_guess_payload_class(self, payload):
    ''' docstring: 重载IP层负载猜测函数, 添加color协议 '''
    if self.proto == 150:
        if payload[0] == 113:
            return ColorAnn
        elif payload[0] == 114:
            return ColorGet
        elif payload[0] == 115:
            return ColorData
        elif payload[0] == 116:
            return ColorControl
    return super(IP, self).guess_payload_class(payload)


# 用于IP报文负载推测和自动填写proto字段
IP.guess_payload_class = newIP_guess_payload_class
bind_layers(IP, ColorAnn, {'proto': 150})
bind_layers(IP, ColorGet, {'proto': 150})
bind_layers(IP, ColorData, {'proto': 150})
bind_layers(IP, ColorControl, {'proto': 150})


if __name__ == '__main__':
    # 使用样例 构造测试
    from scapy.all import send
    pkt = IP(dst="192.168.50.1")

    cg = ColorGet()
    cg.N_sid = b'\xff'*16
    cg.L_sid = b'\x01'*20
    cg.nid = b'\xa5'*16
    cg.PIDs = [b'\x01\x23\x45\x67', b'\x98\x76\x54\x32']
    send(pkt/cg, verbose=0)

    cg = ColorGet()
    cg.N_sid = bytes.fromhex("d23454d19f307d8b98ff2da277c0b546")
    cg.L_sid = bytes.fromhex("a9dd379c69638ad6656b2df1dec4804ce760106a")
    cg.nid = bytes.fromhex("b0cd69ef142db5a471676ad710eebf3a")
    cg.PIDs = [b'\x01\x23\x45\x67', b'\x98\x76\x54\x32']
    cg.Flags.R = True
    cg.Random_num = bytes.fromhex("12345678")
    send(pkt/cg, verbose = 0)

    cd = ColorData()
    cd.N_sid = b'\xff'*16
    cd.L_sid = b'\x01'*20
    cd.nid_cus = b'\xa5'*16
    cd.nid_pro = b'\x5a'*16
    cd.PIDs = [b'\x00\x00\x00\x00', b'\x98\x76\x54\x32', b'\x01\x23\x45\x67']
    send(pkt/cd, verbose=0)

    # 测试hmac计算
    cd = ColorData()
    cd.N_sid = b'\xff'*16
    cd.L_sid = b'\x01'*20
    cd.nid_cus = b'\xa5'*16
    cd.nid_pro = b'\x5a'*16
    cd.Flags.R = True
    cd.Flags.C = True
    cd.HMAC = b'\x12\x34\x56\x78'
    cd.PIDs = [b'\x00\x00\x00\x00', b'\x98\x76\x54\x32', b'\x01\x23\x45\x67']
    send(pkt/cd, verbose=0)

    su = Strategy_unit(tag=1, length=1, value=b"\x12")
    au = Ann_unit(AM=1, Strategy_unit_list=[su, su])
    au.N_sid = b'\x01'*16
    au.L_sid = b'\x02'*20
    au.nid = b'\x03'*16
    ca = ColorAnn(Announce_unit_list=[au, au])
    # ca.show2()
    send(pkt/ca, verbose=0)

    ipniditem = IP_NID(IP=Ipv42Int("192.168.50.62"), nid=b"\xf0"*16)
    # ipniditem.show2()
    cc = ColorControl()/ipniditem
    # cc.show2()
    send(pkt/cc, verbose=0)
    pxipitem = PX_IP(PX=0x1122, IP=Ipv42Int("192.168.50.38"))
    # pxipitem.show2()
    asi = ASinfo(ip_nid_list=[ipniditem]*3, px_ip_list=[pxipitem]*5)
    # asi.show2()
    cc = ColorControl()/asi
    # cc.show2()
    send(pkt/cc, verbose=0)
    asu = AttackSummaryUnit(ASid=5, attack_num=6666)
    ai = AttackInfo(attack_list=[asu]*3)
    cc = ColorControl()/ai
    # cc.show2()
    send(pkt/cc, verbose=0)
    ipu = IP(src="1.1.1.1", dst="2.2.2.2")
    cc = ColorControl()/ipu
    # cc.show2()
    send(pkt/cc, verbose=0)
