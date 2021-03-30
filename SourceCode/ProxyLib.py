# coding=utf-8
''' CoLoR代理功能函数库，供交互线程及监听线程调用 '''

from scapy.all import *
import hashlib
import threading
import time

# 公共全局变量


Nid = -0x1  # 当前终端NID，需要初始化
IPv4 = ''  # 当前终端IPv4地址，需要初始化
CacheSidUnits = {}  # 已生成但尚未通告的SID通告单元，key: path; value：class SidUnit
Lock_CacheSidUnits = threading.Lock()  # CacheSidUnits变量锁
# 已通告SID通告单元，key：SID(N_sid+L_sid)的16进制字符串，不存在时为空; value：class SidUnit
AnnSidUnits = {}
Lock_AnnSidUnits = threading.Lock()  # AnnSidUnits变量锁
gets = {}  # 当前请求中的SID，key：SID(N_sid+L_sid)的16进制字符串，value：目标存储路径（含文件名）
Lock_gets = threading.Lock()  # gets变量锁
RegFlag = 0 # 代理注册成功标志，收到RM返回的Control包后置1
PeerProxys = {} # 存储域内Proxy信息，key: NID(int类型)，value：IP地址(字符串类型)
PXs = {} # 存储本域BR信息，key：PX(int类型)，value：IP地址(字符串类型)


# 供线程调用的功能函数


def AnnProxy():
    # 向RM注册当前代理，获取域内信息
    NewPkt = ControlPkt(1)
    Tar = NewPkt.packing()
    SendIpv4(GetRMip(), Tar)


def Sha1Hash(path):
    # 计算特定文件160位hash值(Sha1)
    # path：新文件路径
    block_size = 64 * 1024  # 分块计算hash，减少内存占用
    with open(path, 'rb') as f:
        sha1 = hashlib.sha1()
        while True:
            temp = f.read(block_size)
            if not temp:
                break
            sha1.update(temp)
        # print(sha1.digest())
        return sha1.hexdigest()


def AddCacheSidUnit(path, AM, N, L, I, level=-1):
    # 生成单个SID通告单元
    Strategy_units = {}
    # 增添策略字段
    if(level >= 1 and level <= 10):
        # 信息级别策略。标识为1，value范围为[1, 10]，value长度为1字节
        value = hex(level).replace('0x', '')
        value += '0'*(8-len(value))
        Strategy_units[1] = value
    Hash_sid = int(Sha1Hash(path), 16)
    # TODO: 需通过Hash_sid判断内容是否来自其他生产节点，此处默认了path对应的文件是本终端提供的内容，待完善 #
    N_sid_temp = Nid if N == 1 else -1
    L_sid_temp = Hash_sid if L == 1 else -1
    nid_temp = Nid if I == 1 else -1
    tempSidUnit = SidUnit(path, AM, N_sid_temp,
                          L_sid_temp, nid_temp, Strategy_units)
    Lock_CacheSidUnits.acquire()
    CacheSidUnits[path] = tempSidUnit
    Lock_CacheSidUnits.release()


def DeleteCacheSidUnit(path):
    # 删除已生成但未通告的SID策略单元
    Lock_CacheSidUnits.acquire()
    CacheSidUnits.pop(path)
    Lock_CacheSidUnits.release()


def SidAnn(ttl=64, PublicKey='', P=1):
    # 整合已生成的SID策略单元，发送ANN报文
    # PublicKey格式为16进制字符串(不含0x前缀)
    if(RegFlag == 1):
        # 变量整理
        V = 7
        Package = 1
        pkt_length = 0
        checksum = 0
        F = 0
        PublicKeyLen = len(PublicKey)/2  # 字节长度
        K = 1 if PublicKeyLen != 0 else 0
        Lock_CacheSidUnits.acquire()
        # 需判断MTU，判断是否拆分出多个ANN包，当前默认1个ANN，待完善 #
        SidUnits = CacheSidUnits.copy()  # 提取缓存区的SID块
        CacheSidUnits.clear()  # 清空原缓存区
        Lock_CacheSidUnits.release()
        UnitNum = len(SidUnits)
        PXNum = 0
        ASPathLen = 0
        # 长度计算
        pkt_length += 8  # 固定长度
        for value in SidUnits.values():
            pkt_length += value.Unit_length
        if (K == 1):
            pkt_length += (2 + PublicKeyLen)
        if (P == 1):
            pkt_length += 1
        # 封装到bytes类型及校验和计算
        TarPre = bytes()  # 存储CheckSum前的报文
        TarCS = ConvertInt2Bytes(checksum, 2)  # 计算校验和时默认CS字段为0
        TarRest = bytes()  # CheckSum后的报文
        TarPre += ConvertInt2Bytes((V << 4) + Package, 1)
        TarPre += ConvertInt2Bytes(ttl, 1)
        TarPre += ConvertInt2Bytes_LE(pkt_length, 2)
        TarRest += ConvertInt2Bytes(((F << 7)+(K << 6)+(P << 5)), 1)
        TarRest += ConvertInt2Bytes(((UnitNum << 4)+PXNum), 1)
        for value in SidUnits.values():
            TarRest += value.packing()
        if (K == 1):
            TarRest += ConvertInt2Bytes_LE(PublicKeyLen, 2)
            TarRest += ConvertInt2Bytes(int(PublicKey, 16), PublicKeyLen)
        if (P == 1):
            TarRest += ConvertInt2Bytes(ASPathLen, 1)
        Tar = TarPre + TarCS + TarRest  # 校验和为0的字节串
        TarCS = ConvertInt2Bytes(CalculateCS(Tar), 2)
        Tar = TarPre + TarCS + TarRest  # 计算出校验和的字节串
        # SID块存入AnnSidUnits，发送报文
        for key in SidUnits.keys():
            NewKey = ''
            if(SidUnits[key].N_sid != -1):
                NewKey += hex(SidUnits[key].N_sid).replace('0x', '').zfill(32)
            if(SidUnits[key].L_sid != -1):
                NewKey += hex(SidUnits[key].L_sid).replace('0x', '').zfill(40)
            Lock_AnnSidUnits.acquire()
            # 可能是修改或删除情况的ANN，待完善#
            AnnSidUnits[NewKey] = SidUnits[key]
            Lock_AnnSidUnits.release()
        SendIpv4(GetRMip(), Tar)
    else:
        print("错误！代理注册未完成！")


def Get(SID, path, ttl=64, PublicKey='', QoS='', SegID=-1, A=1):
    # 生成完整的Get报文，获取对应内容
    # SID：目标SID(N_sid+L_sid)的16进制字符串，path：本地存储路径（含文件名）
    if(RegFlag == 1):
        NewPkt = GetPkt(1, SID, ttl, PublicKey, QoS, SegID, A)
        Tar = NewPkt.packing()
        Lock_gets.acquire()
        gets[SID] = path
        Lock_gets.release()
        SendIpv4(GetRMip(), Tar)
    else:
        print("错误！代理注册未完成！")


def ConvertFile(path, lpointer=0, rpointer=-1):
    # 将任意文件编码为二进制
    # path：文件路径，lpointer：左截取指针，rpointer
    f = open(path, 'rb')
    tar = f.read()
    if(rpointer == -1):
        rpointer = len(tar)
    return tar[lpointer: rpointer]


def ConvertByte(tar, path):
    # 将二进制编码写入到文件
    # src：二进制编码，path：新文件路径
    f = open(path, 'ab')  # 追加写入，覆盖写入为'wb'
    f.write(tar)
    f.close()


# 各对象定义


class ControlPkt():
    # 控制包
    V = 7
    Package = 4
    ttl = 64
    checksum = 0
    HeaderLength = 0
    tag = 0
    DataLength = 0
    ProxyIP = ''
    ProxyNid = -1
    Proxys = []  # 元组（NID, IP）列表
    BRs = []  # 元组（PX, IP）列表
    data = b''
    Pkt = b''

    def __init__(self, flag, ttl=64, Pkt=b''):
        if(flag == 0):
            # 解析控制包
            pointer = 1  # 当前解析字节指针，第0字节已在调用时验证
            self.Pkt = Pkt
            self.ttl = Pkt[pointer]
            pointer += 1
            self.checksum = (Pkt[pointer] << 8)+Pkt[pointer+1]
            pointer += 2
            self.HeaderLength = Pkt[pointer]
            pointer += 1
            self.tag = Pkt[pointer]
            pointer += 1
            self.DataLength = Pkt[pointer]+(Pkt[pointer+1] << 8)
            pointer += 2
            if(self.tag == 6):
                # RM同步域内信息
                NumProxys = Pkt[pointer]
                pointer += 1
                self.Proxys.clear()
                for i in range(NumProxys):
                    tempNid = 0
                    for j in range(16):
                        tempNid = (tempNid << 8) + Pkt[pointer]
                        pointer += 1
                    tempIP = ''
                    for j in range(4):
                        tempIP += str(Pkt[pointer]) + '.'
                        pointer += 1
                    tempIP = tempIP[:-1]
                    self.Proxys.append((tempNid, tempIP))
                NumBRs = Pkt[pointer]
                pointer += 1
                self.BRs.clear()
                for i in range(NumBRs):
                    tempPX = 0
                    for j in range(2):
                        tempPX = (tempPX << 8) + Pkt[pointer]
                        pointer += 1
                    tempIP = ''
                    for j in range(4):
                        tempIP += str(Pkt[pointer]) + '.'
                        pointer += 1
                    tempIP = tempIP[:-1]
                    self.BRs.append((tempPX, tempIP))
            elif(self.tag == 8) and (self.DataLength == 20):
                # RM分发新注册的proxy信息
                self.ProxyIP = ''
                for i in range(4):
                    self.ProxyIP += str(Pkt[pointer]) + '.'
                    pointer += 1
                self.ProxyIP = self.ProxyIP[:-1]
                self.ProxyNid = 0
                for i in range(16):
                    self.ProxyNid = (self.ProxyNid << 8) + Pkt[pointer]
                    pointer += 1
        elif(flag == 1):
            # 新建控制包
            self.ttl = ttl
            self.HeaderLength = 8
            self.tag = 5  # 仅存在一种情况
            self.DataLength = 20
            self.ProxyIP = IPv4
            self.ProxyNid = Nid
            IPList = self.ProxyIP.split('.')
            self.data = b''
            for i in IPList:
                self.data += ConvertInt2Bytes(int(i), 1)
            self.data += ConvertInt2Bytes(self.ProxyNid, 16)

    def packing(self):
        # 计算校验和
        TarPre = bytes()  # 存储CheckSum前的报文
        TarCS = ConvertInt2Bytes(self.checksum, 2)  # 计算校验和时默认CS字段为0
        TarRest = bytes()  # CheckSum后的报文
        TarPre += ConvertInt2Bytes((self.V << 4) + self.Package, 1)
        TarPre += ConvertInt2Bytes(self.ttl, 1)
        TarRest += ConvertInt2Bytes(self.HeaderLength, 1)
        TarRest += ConvertInt2Bytes(self.tag, 1)
        TarRest += ConvertInt2Bytes_LE(self.DataLength, 2)
        # TarRest += self.data
        Tar = TarPre + TarCS + TarRest  # 校验和为0的字节串
        TarCS = ConvertInt2Bytes(CalculateCS(Tar), 2)
        Tar = TarPre + TarCS + TarRest + self.data # 计算出校验和的字节串
        # 封装并返回
        self.Pkt = Tar
        return self.Pkt


class SidUnit():
    # 通告单元
    path = ''
    AM = 0  # 通告单元的动作类型，可能取值为新增（1）、更新（2）、注销（3）
    Unit_length = 0  # 通告单元的总长度，长度为字节
    N_sid = -0x1  # 所注册SID的前部, 128bits，用16进制数表示，可为-1（此时标志位N=1）
    L_sid = -0x1  # 所注册SID的前部, 160bits，用16进制数表示，可为-1（此时标志位L=1）
    nid = -0x1  # 注册该服务的节点的NID，128bits，用16进制数表示，可为-1（此时标志位I=1）
    # 策略单元，key为策略编号tag，格式int;value为策略具体内容，格式为16进制字符串(不含0x前缀)
    Strategy_units = {}
    Strategy_units_length = {}  # 存储策略字段长度信息

    def __init__(self, path, AM, N_sid, L_sid, nid, Strategy_units):
        self.path = path
        self.AM = AM
        self.N_sid = N_sid
        self.L_sid = L_sid
        self.nid = nid
        self.Strategy_units = Strategy_units.copy()
        self.Unit_length = 3  # 固定长度
        if(N_sid != -1):
            self.Unit_length += 16
        if(L_sid != -1):
            self.Unit_length += 20
        if(nid != -1):
            self.Unit_length += 16
        self.Strategy_units_length.clear()
        for key in self.Strategy_units:
            value_length = len(self.Strategy_units[key])/2 + 2
            self.Unit_length += value_length
            self.Strategy_units_length[key] = value_length

    def packing(self):
        # 按通告单元格式进行封装，返回bytes类型字符串
        tar = bytes()
        # 首字节
        temp = 0
        if(self.N_sid != -1):
            temp |= 0x80
        if(self.L_sid != -1):
            temp |= 0x40
        if(self.nid != -1):
            temp |= 0x20
        if(self.AM == 1):
            temp |= 0X08
        elif(self.AM == 2):
            temp |= 0X10
        elif(self.AM == 3):
            temp |= 0X18
        tar += ConvertInt2Bytes(temp, 1)
        # Unit_length字节
        tar += ConvertInt2Bytes(self.Unit_length, 1)
        # Strategy_N字节
        tar += ConvertInt2Bytes(len(self.Strategy_units), 1)
        # sid字段
        if(self.N_sid != -1):
            tar += ConvertInt2Bytes(self.N_sid, 16)
        if(self.L_sid != -1):
            tar += ConvertInt2Bytes(self.L_sid, 20)
        if(self.nid != -1):
            tar += ConvertInt2Bytes(self.nid, 16)
        # 策略字段
        for key in self.Strategy_units:
            tag = key
            tar += ConvertInt2Bytes(tag, 1)
            length = self.Strategy_units_length[key]
            tar += ConvertInt2Bytes(length, 1)
            tar += ConvertInt2Bytes(
                int(self.Strategy_units[key], 16), length-2)
        return tar


class DataPkt():
    # data包
    V = 7
    Package = 3
    ttl = 64
    PktLength = 0
    checksum = 0
    HeaderLength = 0
    PidPt = 0  # PID指针，指向入域时需要BR校验的PID
    PID_num = 0
    F = 0
    B = 0
    R = 0
    M = 0
    Q = 0
    C = 0
    S = 0
    MinimalPidCp = -1  # 暂不使用，待完善 #
    N_sid = -1
    L_sid = -1
    nid_cus = -1
    nid_pro = -1
    QoS = ''  # 格式为16进制字符串(不含0x前缀)
    HMAC = 0  # 暂不使用，待完善 #
    SegID = -1
    PIDs = []  # RES_PID包含其中
    load = b''
    Pkt = b''

    def __init__(self, flag, B=0, R=0, C=0, SID='', ttl=64, MinimalPidCp=-1, nid_cus=-1, nid_pro=-1, QoS='', SegID=-1, PIDs=[], load=b'', Pkt=b''):
        if(flag == 0):
            # 解析Data包
            pointer = 1  # 当前解析字节指针，第0字节已在调用时验证
            self.Pkt = Pkt
            self.ttl = Pkt[pointer]
            pointer += 1
            self.PktLength = Pkt[pointer]+(Pkt[pointer+1] << 8)
            pointer += 2
            self.checksum = (Pkt[pointer] << 8)+Pkt[pointer+1]
            pointer += 2
            self.HeaderLength = Pkt[pointer]
            pointer += 1
            self.PidPt = Pkt[pointer]
            pointer += 1
            self.PID_num = Pkt[pointer]
            pointer += 1
            self.F = 1 if Pkt[pointer] & (1 << 7) > 0 else 0
            self.B = 1 if Pkt[pointer] & (1 << 6) > 0 else 0
            self.R = 1 if Pkt[pointer] & (1 << 5) > 0 else 0
            self.M = 1 if Pkt[pointer] & (1 << 4) > 0 else 0
            self.Q = 1 if Pkt[pointer] & (1 << 3) > 0 else 0
            self.C = 1 if Pkt[pointer] & (1 << 2) > 0 else 0
            self.S = 1 if Pkt[pointer] & (1 << 1) > 0 else 0
            pointer += 1
            if(self.M == 1):
                self.MinimalPidCp = Pkt[pointer]+(Pkt[pointer+1] << 8)
                pointer += 2
            self.N_sid = 0
            for i in range(16):
                self.N_sid = (self.N_sid << 8) + Pkt[pointer]
                pointer += 1
            self.L_sid = 0
            for i in range(20):
                self.L_sid = (self.L_sid << 8) + Pkt[pointer]
                pointer += 1
            if(self.B == 0):
                self.nid_cus = 0
                for i in range(16):
                    self.nid_cus = (self.nid_cus << 8) + Pkt[pointer]
                    pointer += 1
            self.nid_pro = 0
            for i in range(16):
                self.nid_pro = (self.nid_pro << 8) + Pkt[pointer]
                pointer += 1
            if(self.Q == 1):
                QosLen = Pkt[pointer]
                pointer += 1
                for i in range(QosLen):
                    self.QoS += hex(Pkt[pointer]).replace('0x', '')
                    pointer += 1
            if(self.C == 1):
                self.HMAC = 0
                for i in range(4):
                    self.HMAC += Pkt[pointer] << (8*i)
                    pointer += 1
            if(self.S == 1):
                self.SegID = 0
                for i in range(4):
                    self.SegID += Pkt[pointer] << (8*i)
                    pointer += 1
            self.PIDs.clear()
            for i in range(self.PID_num + self.R):
                tempPID = 0
                for j in range(4):
                    tempPID += tempPID << 8 + Pkt[pointer]
                    pointer += 1
                self.PIDs.append(tempPID)
            while(pointer < len(Pkt)):
                self.load += ConvertInt2Bytes(Pkt[pointer], 1)
                pointer += 1
        elif(flag == 1):
            # 新建Data包
            self.ttl = ttl
            self.PidPt = len(PIDs)
            self.PID_num = len(PIDs)
            self.B = B
            self.R = R
            self.MinimalPidCp = MinimalPidCp
            if(MinimalPidCp == -1):
                self.M = 0
            else:
                self.MinimalPidCp = MinimalPidCp
                self.M = 1
            if(len(QoS) == 0):
                self.Q = 0
            else:
                self.Q = 1
                self.QoS = QoS
            self.C = 0  # 暂不考虑MAC字段 #
            if(SegID == -1):
                self.S = 0
            else:
                self.S = 1
                self.SegID = SegID
            if(len(SID) == 72):
                self.N_sid = int(SID[0:32], 16)
                self.L_sid = int(SID[32:], 16)
            elif(len(SID) == 32):
                self.N_sid = int(SID, 16)
            elif(len(SID) == 40):
                self.L_sid = int(SID, 16)
            if(self.B == 0):
                # 普通数据报文
                self.nid_pro = Nid
                self.nid_cus = nid_cus
            elif(self.B == 1):
                # ACK报文
                self.nid_pro = nid_pro
            self.PIDs = PIDs.copy()
            if(self.B == 0 and self.R == 1):
                self.PIDs.append(0)  # 预留字段
            self.load = load
            # 计算HeaderLength和PktLength
            self.HeaderLength = 10  # 固定长度（截止到Minimal_PID_CP前）
            if(self.M == 1):
                self.HeaderLength += 2
            self.HeaderLength += 52
            if(self.B == 0):
                self.HeaderLength += 16  # nid_customer的长度
            if(self.Q == 1):
                self.HeaderLength += 1 + len(self.QoS)/2
            if(self.C == 1):
                self.HeaderLength += 4
            if(self.S == 1):
                self.HeaderLength += 4
            self.HeaderLength += len(self.PIDs)*4
            self.PktLength = self.HeaderLength + len(self.load)

    def packing(self):
        # 计算校验和
        TarPre = bytes()  # 存储CheckSum前的报文
        TarCS = ConvertInt2Bytes(self.checksum, 2)  # 计算校验和时默认CS字段为0
        TarRest = bytes()  # CheckSum后的报文
        TarPre += ConvertInt2Bytes((self.V << 4) + self.Package, 1)
        TarPre += ConvertInt2Bytes(self.ttl, 1)
        TarPre += ConvertInt2Bytes_LE(self.PktLength, 2)
        TarRest += ConvertInt2Bytes(self.HeaderLength, 1)
        TarRest += ConvertInt2Bytes(self.PidPt, 1)
        TarRest += ConvertInt2Bytes(self.PID_num, 1)
        TarRest += ConvertInt2Bytes((self.F << 7)+(self.B << 6) + (self.R << 5)+(
            self.M << 4)+(self.Q << 3)+(self.C << 2)+(self.S << 1), 1)
        if(self.M == 1):
            TarRest += ConvertInt2Bytes_LE(self.MinimalPidCp, 2)
        if(self.N_sid != -1):
            TarRest += ConvertInt2Bytes(self.N_sid, 16)
        else:
            TarRest += ConvertInt2Bytes(0, 16)
        if(self.L_sid != -1):
            TarRest += ConvertInt2Bytes(self.L_sid, 20)
        else:
            TarRest += ConvertInt2Bytes(0, 20)
        if(self.B == 0):
            TarRest += ConvertInt2Bytes(self.nid_cus, 16)
        TarRest += ConvertInt2Bytes(self.nid_pro, 16)
        if(self.Q == 1):
            QosLen = len(self.QoS)/2
            TarRest += ConvertInt2Bytes(QosLen, 1)
            TarRest += ConvertInt2Bytes(int(self.QoS, 16), QosLen)
        if(self.C == 1):
            TarRest += ConvertInt2Bytes(self.HMAC, 4)
        if(self.S == 1):
            TarRest += ConvertInt2Bytes_LE(self.SegID, 4)
        for pid in self.PIDs:
            TarRest += ConvertInt2Bytes(pid, 4)
        TarRest += self.load
        Tar = TarPre + TarCS + TarRest  # 校验和为0的字节串
        TarCS = ConvertInt2Bytes(CalculateCS(Tar), 2)
        Tar = TarPre + TarCS + TarRest  # 计算出校验和的字节串
        # 封装并返回
        self.Pkt = Tar
        return self.Pkt


class GetPkt():
    # get包
    V = 7
    Package = 2
    ttl = 64
    PktLength = 0
    checksum = 0
    MTU = 0
    PID_num = 0
    F = 0
    K = 0
    Q = 0
    S = 0
    A = 1
    MinimalPidCp = 0  # 暂不使用，待完善 #
    N_sid = -1
    L_sid = -1
    nid = -1
    PublicKey = ''  # PublicKey格式为16进制字符串(不含0x前缀)
    QoS = ''  # 同上
    SegID = -1
    PIDs = []
    Pkt = b''

    def __init__(self, flag, SID='', ttl=64, PublicKey='', QoS='', SegID=-1, A=1, Pkt=b''):
        if (flag == 0):
            # 解析Get包
            pointer = 1  # 当前解析字节指针，第0字节已在调用时验证
            self.Pkt = Pkt
            self.ttl = Pkt[pointer]
            pointer += 1
            self.PktLength = Pkt[pointer]+(Pkt[pointer+1] << 8)
            pointer += 2
            self.checksum = (Pkt[pointer] << 8)+Pkt[pointer+1]
            pointer += 2
            self.MTU = Pkt[pointer]+(Pkt[pointer+1] << 8)
            pointer += 2
            self.PID_num = Pkt[pointer]
            pointer += 1
            self.F = 1 if Pkt[pointer] & (1 << 7) > 0 else 0
            self.K = 1 if Pkt[pointer] & (1 << 6) > 0 else 0
            self.Q = 1 if Pkt[pointer] & (1 << 5) > 0 else 0
            self.S = 1 if Pkt[pointer] & (1 << 4) > 0 else 0
            self.A = 1 if Pkt[pointer] & (1 << 3) > 0 else 0
            pointer += 1
            self.MinimalPidCp = Pkt[pointer]+(Pkt[pointer+1] << 8)
            pointer += 2
            self.N_sid = 0
            for i in range(16):
                self.N_sid = (self.N_sid << 8) + Pkt[pointer]
                pointer += 1
            self.L_sid = 0
            for i in range(20):
                self.L_sid = (self.L_sid << 8) + Pkt[pointer]
                pointer += 1
            self.nid = 0
            for i in range(16):
                self.nid = (self.nid << 8) + Pkt[pointer]
                pointer += 1
            if(self.K == 1):
                PublicKeyLen = Pkt[pointer]+(Pkt[pointer+1] << 8)
                pointer += 2
                for i in range(PublicKeyLen):
                    self.PublicKey += hex(Pkt[pointer]).replace('0x', '')
                    pointer += 1
            if(self.Q == 1):
                QosLen = Pkt[pointer]
                pointer += 1
                for i in range(QosLen):
                    self.QoS += hex(Pkt[pointer]).replace('0x', '')
                    pointer += 1
            if(self.S == 1):
                self.SegID = 0
                for i in range(4):
                    self.SegID += Pkt[pointer] << (8*i)
                    pointer += 1
            self.PIDs.clear()
            for i in range(self.PID_num):
                tempPID = 0
                for j in range(4):
                    tempPID += tempPID << 8 + Pkt[pointer]
                    pointer += 1
                self.PIDs.append(tempPID)
        elif (flag == 1):
            # 新建Get包
            # 特定字段填充(校验和除外)
            if(len(SID) == 72):
                self.N_sid = int(SID[0:32], 16)
                self.L_sid = int(SID[32:], 16)
            elif(len(SID) == 32):
                self.N_sid = int(SID, 16)
            elif(len(SID) == 40):
                self.L_sid = int(SID, 16)
            self.ttl = ttl
            if(len(PublicKey) == 0):
                self.K = 0
            else:
                self.K = 1
                self.PublicKey = PublicKey
            if(len(QoS) == 0):
                self.Q = 0
            else:
                self.Q = 1
                self.QoS = QoS
            self.SegID = SegID
            self.A = A
            self.nid = Nid
            # 计算PktLength
            self.PktLength = 64  # 固定长度(截止到SID)
            if(self.K == 1):
                self.PktLength += 2 + len(self.PublicKey)/2
            if(self.Q == 1):
                self.PktLength += 1 + len(self.QoS)/2
            if(self.S == 1):
                self.PktLength += 4

    def packing(self):
        # 计算校验和
        TarPre = bytes()  # 存储CheckSum前的报文
        TarCS = ConvertInt2Bytes(self.checksum, 2)  # 计算校验和时默认CS字段为0
        TarRest = bytes()  # CheckSum后的报文
        TarPre += ConvertInt2Bytes((self.V << 4) + self.Package, 1)
        TarPre += ConvertInt2Bytes(self.ttl, 1)
        TarPre += ConvertInt2Bytes_LE(self.PktLength, 2)
        TarRest += ConvertInt2Bytes_LE(self.MTU, 2)
        TarRest += ConvertInt2Bytes(self.PID_num, 1)
        TarRest += ConvertInt2Bytes((self.F << 7)+(self.K << 6) +
                                    (self.Q << 5)+(self.S << 4)+(self.A << 3), 1)
        TarRest += ConvertInt2Bytes_LE(self.MinimalPidCp, 2)
        if(self.N_sid != -1):
            TarRest += ConvertInt2Bytes(self.N_sid, 16)
        else:
            TarRest += ConvertInt2Bytes(0, 16)
        if(self.L_sid != -1):
            TarRest += ConvertInt2Bytes(self.L_sid, 20)
        else:
            TarRest += ConvertInt2Bytes(0, 20)
        TarRest += ConvertInt2Bytes(self.nid, 16)
        if(self.K == 1):
            PublicKeyLen = len(self.PublicKey)/2
            TarRest += ConvertInt2Bytes_LE(PublicKeyLen, 2)
            TarRest += ConvertInt2Bytes(int(self.PublicKey, 16), PublicKeyLen)
        if(self.Q == 1):
            QosLen = len(self.QoS)/2
            TarRest += ConvertInt2Bytes(QosLen, 1)
            TarRest += ConvertInt2Bytes(int(self.QoS, 16), QosLen)
        if(self.S == 1):
            TarRest += ConvertInt2Bytes_LE(self.SegID, 4)
        Tar = TarPre + TarCS + TarRest  # 校验和为0的字节串
        TarCS = ConvertInt2Bytes(CalculateCS(Tar), 2)
        Tar = TarPre + TarCS + TarRest  # 计算出校验和的字节串
        # 封装并返回
        self.Pkt = Tar
        return self.Pkt


# 函数库使用的功能函数


def ConvertInt2Bytes(data, length):
    # 将int类型转成bytes类型（大端存储）
    # data：目标数字，length：目标字节数
    data = hex(data).replace('0x', '')
    data = '0'*(length*2 - len(data)) + data
    data_bytes = bytes.fromhex(data)
    return data_bytes


def ConvertInt2Bytes_LE(data, length):
    # 将int类型转成bytes类型（小端存储）
    # data：目标数字，length：目标字节数
    data = hex(data).replace('0x', '')
    data = '0'*(length*2 - len(data)) + data
    data_LE = ''
    temp = ''
    pointer = 0
    while(pointer < len(data)):
        temp += data[pointer]
        pointer += 1
        if(pointer % 2 == 0):
            data_LE = temp + data_LE
            temp = ''
    data_bytes = bytes.fromhex(data_LE)
    return data_bytes


def CalculateCS(tar):
    ''' docstring: 校验和计算 '''
    # tar：bytes字符串
    length = len(tar)
    pointer = 0
    sum = 0
    while (length - pointer > 1):
        temp = tar[pointer] << 8
        temp += tar[pointer+1]
        pointer += 2
        sum += temp
    if (length - pointer > 0):
        sum += tar[pointer]
    sum = (sum >> 16) + (sum & 0xffff)
    sum = (sum >> 16) + (sum & 0xffff)  # 防止上一步相加后结果大于16位
    return (sum ^ 0xffff)  # 按位取反后返回


def SendIpv4(ipdst, data):
    # 封装IPv4网络包并发送
    # ipdst: 目标IP地址，data：IP包正文内容
    pkt = IP(dst=ipdst, proto=150) / data
    # pkt.show()
    send(pkt, verbose=0)


def GetRMip():
    ''' docstring: 读配置文件获取RM所在IP地址(适用IPv4) '''
    # TODO: 修改为与RM交互获取数据
    return '10.0.0.1'


# def GetBRip():
#     ''' docstring: 读配置文件获取BR所在IP地址(适用IPv4)'''
#     return '192.168.50.129'
