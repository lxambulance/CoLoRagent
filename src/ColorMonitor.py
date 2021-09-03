# coding=utf-8
''' docstring: CoLoR监听线程，负责与网络组件的报文交互 '''

from scapy.all import *
import threading
import ProxyLib as PL
import math
import time
import cv2
import numpy as np
import zlib
import queue
import pickle
import pymysql

from PyQt5.QtCore import QObject, pyqtSignal
import establishSecureSession as ESS

# 文件传输相关全局变量
SendingSid = {}  # 记录内容发送情况，key:SID，value:[片数，单片大小，下一片指针，customer的nid，pid序列]
RecvingSid = {}  # 记录内容接收情况，key:SID，value:下一片指针
WaitingACK = {}  # 流视频提供者记录ACK回复情况，key:NID（customer），value:连续未收到ACK个数
RTO = 1  # 超时重传时间
ESS.RTO = RTO
# 视频传输相关全局变量
Lock_WaitingACK = threading.Lock()
VideoCache = {}  # 流视频接收者缓存数据片，{帧序号：{片序号：片内容}}，最多存储最新的三个帧的信息
MergeFlag = {}  # 流视频接收者记录单个数据片的可拼装情况{帧序号：flag}；flag=0，未收到最后一片；收到最后一片：flag=片数
Lock_VideoCache = threading.Lock()
FrameCache = queue.Queue(10)  # 视频接收者完整帧的缓存区
FrameSid = queue.Queue(10)  # 记录视频帧对应的SID
# 数据库查询相关全局变量
# client已经指定但尚未传输的数据库查询指令，key:ServerNid(int)，value:完整的单一查询指令字符串
QueryCache = {}
Lock_QueryCache = threading.Lock()
SqlResultCache = {}  # client接收数据库查询结果的缓冲区，key：ServerNid(int)，value:bytes字符串
Lock_SqlResultCache = threading.Lock()
ServerQueryCache = {} # server接收数据库查询请求的缓冲区，key：clientNid(int)，value:bytes字符串
Lock_ServerQueryCache = threading.Lock()
# server接收到查询命令后存储查询结果的缓冲区，key：clientNid(int)，value:bytes字符串
ServerResultCache = {}
Lock_ServerResultCache = threading.Lock()


def GetSql(ServerNid, command):
    # client获取数据库内容的初始化函数，参数为数据库NID(16进制字符串)及完整的单一查询指令字符串
    PL.AddCacheSidUnit(4, 1, 1, 1, 1)
    PL.SidAnn()
    Lock_QueryCache.acquire()
    QueryCache[int(ServerNid, 16)] = pickle.dumps(command)
    Lock_QueryCache.release()
    SID = ServerNid.zfill(32) + '3'.zfill(40)
    PL.Get(SID, 3)


class pktSignals(QObject):
    ''' docstring: 包处理的信号 '''
    # finished用于任务结束信号
    finished = pyqtSignal()
    # output用于输出信号
    output = pyqtSignal(int, object)
    # pathdata用于输出路径相关信息
    pathdata = pyqtSignal(int, str, list, int, int)


class PktHandler(threading.Thread):
    ''' docstring: 收包处理程序 '''
    packet = ''

    def __init__(self, packet):
        threading.Thread.__init__(self)
        self.packet = packet
        # 请将所有需要输出print()的内容改写为信号的发射(self.signals.output.emit())
        # TODO：异常情况调用traceback模块输出信息
        self.signals = pktSignals()

    def video_provider(self, Sid, NidCus, PIDs, LoadLength, ReturnIP):
        FrameCount = 0  # 帧序号，每15帧设定第一片的标志位R为1（需要重传ACK）
        # 校验视频传输GET包后，调用流视频传输进程
        capture = cv2.VideoCapture(0)
        ret, frame = capture.read()
        # 压缩参数，15代表图像质量，越高代表图像质量越好为 0-100，默认95
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 20]
        while ret:
            # 避免发送过快
            # time.sleep(0.01)
            # 单帧编码
            result, imgencode = cv2.imencode('.jpg', frame, encode_param)
            data = np.array(imgencode)
            stringData = data.tostring()
            stringData = zlib.compress(stringData)
            # 单帧数据发送
            ChipNum = math.ceil(len(stringData) / LoadLength)
            ChipCount = 0  # 单帧片序号
            while ChipCount < ChipNum:
                if(ChipCount + 1 == ChipNum):
                    # 最后一片
                    load = PL.ConvertInt2Bytes(1, 1)
                    load += stringData[ChipCount * LoadLength:]
                else:
                    load = PL.ConvertInt2Bytes(0, 1)
                    load += stringData[ChipCount *
                                       LoadLength:(ChipCount + 1) * LoadLength]
                R = 1 if (FrameCount % 15 == 0 and ChipCount == 0) else 0
                SegID = ((FrameCount << 16) % (1 << 32)) + ChipCount
                NewDataPkt = PL.DataPkt(
                    1, 0, R, 0, Sid, nid_cus=NidCus, SegID=SegID, PIDs=PIDs, load=load)
                if (R == 1):
                    Lock_WaitingACK.acquire()
                    if NidCus not in WaitingACK.keys():
                        WaitingACK[NidCus] = 1
                    else:
                        WaitingACK[NidCus] += 1
                    Lock_WaitingACK.release()
                Tar = NewDataPkt.packing()
                PL.SendIpv4(ReturnIP, Tar)
                ChipCount += 1
            # 读取下一帧
            ret, frame = capture.read()
            FrameCount += 1
            cv2.imshow("img", frame)
            if cv2.waitKey(10) == 27:
                # 视频提供者主动退出
                Lock_WaitingACK.acquire()
                if (NidCus in WaitingACK.keys()):
                    WaitingACK.pop(NidCus)
                Lock_WaitingACK.release()
                cv2.destroyAllWindows()
                capture.release()
                break
            Lock_WaitingACK.acquire()
            if (NidCus in WaitingACK.keys()) and (WaitingACK[NidCus] > 5):
                # 视频接收者退出后，视频提供者退出
                WaitingACK.pop(NidCus)
                Lock_WaitingACK.release()
                self.signals.output.emit(0, '连续多个ACK未收到，判断链路中断，结束视频流传输')
                cv2.destroyAllWindows()
                capture.release()
                break
            Lock_WaitingACK.release()

    def SqlQuery(self, command):
        # 打开数据库连接
        db = pymysql.connect(host="localhost", user="root", password="Mysql233.", database="testdb")
        # 使用 cursor() 方法创建一个游标对象 cursor
        cursor = db.cursor()
        result = -1
        try:
            cursor.execute(command)
            result = cursor.fetchall()
        except:
            print("Error: unable to fecth data")
        db.close()
        return result
    
    def run(self):
        if ('Raw' in self.packet) and (self.packet[IP].dst == PL.IPv4) and (self.packet[IP].proto == 150):
            # self.packet.show()
            data = bytes(self.packet['Raw'])  # 存入二进制字符串
            PktLength = len(data)
            if(PL.RegFlag == 0):
                # 注册中状态
                # 过滤掉其他格式的包。
                if PktLength < 8 or data[0] != 0x74 or data[5] != 6 or PktLength != (data[4] + data[6] + ((data[7]) << 8)):
                    return
                # 校验和检验
                CS = PL.CalculateCS(data[0:8])
                if(CS != 0):
                    return
                # 解析报文内容
                NewCtrlPkt = PL.ControlPkt(0, Pkt=data)
                for proxy in NewCtrlPkt.Proxys:
                    if proxy[0] != PL.Nid:
                        # 过滤本代理信息
                        PL.PeerProxys[proxy[0]] = proxy[1]
                for BR in NewCtrlPkt.BRs:
                    PL.PXs[BR[0]] = BR[1]
                self.signals.output.emit(0, "代理注册完成，开启网络功能")
                PL.RegFlag = 1
            elif(PL.RegFlag == 1):
                # 正常运行状态
                # 过滤掉其他格式的包。
                if PktLength < 4:
                    return
                if (data[0] == 0x72):
                    # 收到网络中的get报文
                    # 校验和检验
                    CS = PL.CalculateCS(data)
                    if(CS != 0):
                        return
                    # 解析报文内容
                    NewGetPkt = PL.GetPkt(0, Pkt=data)
                    # 判断是否为代理当前提供内容
                    NewSid = ''
                    if NewGetPkt.N_sid != 0:
                        NewSid += hex(NewGetPkt.N_sid).replace('0x',
                                                               '').zfill(32)
                    if NewGetPkt.L_sid != 0:
                        NewSid += hex(NewGetPkt.L_sid).replace('0x',
                                                               '').zfill(40)
                    self.signals.pathdata.emit(
                        0x72, NewSid, NewGetPkt.PIDs, NewGetPkt.PktLength, NewGetPkt.nid)
                    PL.Lock_AnnSidUnits.acquire()
                    if NewSid not in PL.AnnSidUnits.keys():
                        PL.Lock_AnnSidUnits.release()
                        return
                    # 返回数据
                    SidUnitLevel = PL.AnnSidUnits[NewSid].Strategy_units.get(
                        1, 0)  # 获取密级以备后续使用，没有默认为0
                    SidPath = PL.AnnSidUnits[NewSid].path
                    PL.Lock_AnnSidUnits.release()
                    NidCus = NewGetPkt.nid
                    PIDs = NewGetPkt.PIDs.copy()
                    # 按最大长度减去IP报文和DATA报文头长度(QoS暂默认最长为1字节)，预留位占4字节，数据传输结束标志位位于负载内占1字节
                    # SidLoadLength = NewGetPkt.MTU-60-86-(4*len(PIDs)) - 4 - 1
                    SidLoadLength = 1200  # 仅在报文不经过RM的点对点调试用
                    ReturnIP = ''
                    if (len(PIDs) == 0):
                        # 域内请求
                        if (NidCus in PL.PeerProxys.keys()):
                            ReturnIP = PL.PeerProxys[NidCus]
                        else:
                            self.signals.output.emit(1, "未知的NID：" +
                                                     hex(NidCus).replace('0x', '').zfill(32))
                            return
                    else:
                        PX = PIDs[-1] >> 16
                        if (PX in PL.PXs.keys()):
                            ReturnIP = PL.PXs[PX]
                        else:
                            self.signals.output.emit(
                                1, "未知的PX："+hex(PX).replace('0x', '').zfill(4))
                            return
                    # 判断是否传递特殊内容
                    if isinstance(SidPath, int):
                        if SidPath == 1:
                            # 视频服务
                            self.video_provider(
                                NewSid, NidCus, PIDs, SidLoadLength, ReturnIP)
                            return
                        elif (SidPath & 0xff) == 2:
                            # 安全链接服务
                            ESS.gotoNextStatus(
                                NidCus, NewSid, pids=PIDs, ip=ReturnIP)
                            return
                        elif SidPath == 3:
                            # 数据库查询服务
                            if (NidCus not in ServerResultCache.keys()):
                                # 首次接收
                                Lock_ServerResultCache.acquire()
                                ServerResultCache[NidCus] = b''
                                Lock_ServerResultCache.release()
                                SID = hex(NidCus).replace(
                                    '0x', '').zfill(32) + '4'.zfill(40)
                                PL.Get(SID, 4)
                                return
                            else:
                                # 第二次接收（已经接收到查询指令）
                                Data = b''
                                errorflag = 1
                                for i in range(3):
                                    Lock_ServerResultCache.acquire()
                                    if (len(ServerResultCache[NidCus]) != 0):
                                        Data = ServerResultCache[NidCus]
                                        Lock_ServerResultCache.release()
                                        errorflag = 0
                                        break
                                    Lock_ServerResultCache.release()
                                    time.sleep(1)
                                if (errorflag == 1):
                                    self.signals.output.emit(1, "未获得正确查询指令！查询失败！")
                                    return
                        elif SidPath == 4:
                            Data = QueryCache[NidCus]
                    else:
                        Data = PL.ConvertFile(SidPath)
                    DataLength = len(Data)
                    # 特定密集文件，开启加密传输
                    ESSflag = ESS.checkSession(NidCus, NewSid)
                    if int(SidUnitLevel) > 5:
                        if not ESSflag:
                            ESS.newSession(NidCus, NewSid, PIDs,
                                           ReturnIP, pkt=self.packet)
                            return
                        elif not ESS.sessionReady(NidCus, NewSid):
                            self.signals.output.emit(1, "收到重复Get，但安全连接未建立")
                            return
                    # 获取数据，分片或直接传输
                    if ESSflag:
                        SidLoadLength -= 32
                    if (DataLength <= SidLoadLength):
                        ChipNum = 1
                        ChipLength = DataLength
                        load = PL.ConvertInt2Bytes(
                            5 if ESSflag else 1, 1) + (ESS.Encrypt(NidCus, NewSid, Data) if ESSflag else Data)
                        endflag = 1
                    else:
                        ChipNum = math.ceil(DataLength/SidLoadLength)
                        ChipLength = SidLoadLength
                        text = Data[:SidLoadLength]
                        load = PL.ConvertInt2Bytes(
                            4 if ESSflag else 0, 1) + (ESS.Encrypt(NidCus, NewSid, text) if ESSflag else text)
                        endflag = 0
                    SendingSid[NewSid] = [
                        ChipNum, ChipLength, 1, NidCus, PIDs, ESSflag]
                    NewDataPkt = PL.DataPkt(
                        1, 0, 1, 0, NewSid, nid_cus=NidCus, SegID=0, PIDs=PIDs, load=load)
                    Tar = NewDataPkt.packing()
                    PL.SendIpv4(ReturnIP, Tar)
                    # 内容发送完成的特殊操作
                    if isinstance(SidPath, int) and (endflag == 1):
                        if (SidPath == 3):
                            Lock_ServerResultCache.acquire()
                            ServerResultCache.pop(NidCus)
                            Lock_ServerResultCache.release()
                        elif (SidPath == 4):
                            # 数据库查询指令发送完成，获取查询内容
                            Lock_QueryCache.acquire()
                            QueryCache.pop(NidCus)
                            Lock_QueryCache.release()
                            SID = hex(NidCus).replace(
                                '0x', '').zfill(32) + '3'.zfill(40)
                            PL.Get(SID, 3)
                    # 重传判断，待完善锁机制 #
                    for i in range(3):
                        time.sleep(RTO)
                        if ((NewSid in SendingSid) and (SendingSid[NewSid][2] == 1)):
                            self.signals.output.emit(0, '第'+str(SendingSid[NewSid]
                                                                [2]-1)+'片，第'+str(i+1)+'次重传')
                            PL.SendIpv4(ReturnIP, Tar)
                            if isinstance(SidPath, int) and (SidPath == 4) and (endflag == 1):
                                SID = hex(NidCus).replace(
                                    '0x', '').zfill(32) + '3'.zfill(40)
                                PL.Get(SID, 3)
                        else:
                            break
                elif (data[0] == 0x73):
                    # 收到网络中的data报文(或ACK)
                    # 校验和检验
                    HeaderLength = data[6]
                    CS = PL.CalculateCS(data[0:HeaderLength])
                    if(CS != 0):
                        return
                    # 解析报文内容
                    RecvDataPkt = PL.DataPkt(0, Pkt=data)
                    NewSid = ''
                    if RecvDataPkt.N_sid != 0:
                        NewSid += hex(RecvDataPkt.N_sid).replace('0x',
                                                                 '').zfill(32)
                    if RecvDataPkt.L_sid != 0:
                        NewSid += hex(RecvDataPkt.L_sid).replace('0x',
                                                                 '').zfill(40)
                    # 暂时将全部收到的校验和正确的data包显示出来
                    self.signals.pathdata.emit(
                        0x73 | (RecvDataPkt.B << 8), NewSid, RecvDataPkt.PIDs, RecvDataPkt.PktLength, 0)
                    if(RecvDataPkt.B == 0):
                        # 收到数据包
                        # 判断是否为当前代理请求内容
                        PL.Lock_gets.acquire()
                        if NewSid not in PL.gets.keys():
                            PL.Lock_gets.release()
                            return
                        SavePath = PL.gets[NewSid]
                        PL.Lock_gets.release()
                        ReturnIP = ''
                        if (len(RecvDataPkt.PIDs) <= 1):
                            # 域内请求
                            if (RecvDataPkt.nid_pro in PL.PeerProxys.keys()):
                                ReturnIP = PL.PeerProxys[RecvDataPkt.nid_pro]
                            else:
                                self.signals.output.emit(1,
                                                         "未知的NID：" + hex(RecvDataPkt.nid_pro).replace('0x', '').zfill(32))
                        else:
                            PX = RecvDataPkt.PIDs[1] >> 16
                            if (PX in PL.PXs.keys()):
                                ReturnIP = PL.PXs[PX]
                            else:
                                self.signals.output.emit(
                                    1, "未知的PX："+hex(PX).replace('0x', '').zfill(4))
                        # 视频流数据
                        if isinstance(SavePath, int) and SavePath == 1:
                            FrameCount = RecvDataPkt.SegID >> 16
                            ChipCount = RecvDataPkt.SegID % (1 << 16)
                            Lock_VideoCache.acquire()
                            if (FrameCount in VideoCache.keys()):
                                # 已经收到过当前帧的其他片
                                VideoCache[FrameCount][ChipCount] = RecvDataPkt.load[1:]
                                if (RecvDataPkt.load[0] == 1):
                                    MergeFlag[FrameCount] = ChipCount + 1
                                if MergeFlag[FrameCount] == len(VideoCache[FrameCount]):
                                    # 当前帧接收完成
                                    stringData = b''
                                    for Chip in range(MergeFlag[FrameCount]):
                                        stringData += VideoCache[FrameCount][Chip]
                                    stringData = zlib.decompress(stringData)
                                    # 将获取到的字符流数据转换成1维数组
                                    data = np.frombuffer(stringData, np.uint8)
                                    decimg = cv2.imdecode(
                                        data, cv2.IMREAD_COLOR)  # 将数组解码成图像
                                    pops = []
                                    for frame in VideoCache.keys():
                                        if frame == FrameCount or frame == ((FrameCount - 1) % (1 << 16)) or frame == ((FrameCount - 2) % (1 << 16)):
                                            pops.append(frame)
                                    for frame in pops:
                                        VideoCache.pop(frame)
                                        MergeFlag.pop(frame)
                                    FrameSid.put(NewSid)
                                    FrameCache.put(decimg)
                            else:
                                # 新的视频帧(这里默认不能单片完成传输，所以不包含显示逻辑)
                                CacheKeys = list(VideoCache.keys())
                                if(len(CacheKeys) != 0):
                                    Max = max(CacheKeys)
                                    if (Max == (1 << 16) - 1) or (Max == (1 << 16) - 2):
                                        # 可能出现了重置情况
                                        if (2 in CacheKeys):
                                            Max = 2
                                        elif (1 in CacheKeys):
                                            Max = 1
                                    NewMax = Max
                                    if (FrameCount < 10):
                                        if (Max > (1 << 16) - 10) or (FrameCount > Max):
                                            NewMax = FrameCount
                                    elif(FrameCount > (1 << 16) - 10):
                                        if (Max > 10) and (FrameCount > Max):
                                            NewMax = FrameCount
                                    elif(FrameCount > Max):
                                        NewMax = FrameCount
                                else:
                                    NewMax = FrameCount
                                # 存入视频帧
                                if FrameCount not in VideoCache.keys():
                                    VideoCache[FrameCount] = {}
                                VideoCache[FrameCount][ChipCount] = RecvDataPkt.load[1:]
                                MergeFlag[FrameCount] = ChipCount + \
                                    1 if (RecvDataPkt.load[0] == 1) else 0
                                # 重置缓冲区
                                pops = []
                                for frame in VideoCache.keys():
                                    if frame != NewMax and frame != ((NewMax - 1) % (1 << 16)) and frame != ((NewMax - 2) % (1 << 16)):
                                        pops.append(frame)
                                for frame in pops:
                                    VideoCache.pop(frame)
                                    MergeFlag.pop(frame)
                            Lock_VideoCache.release()
                            if(RecvDataPkt.R == 0):
                                return
                        # 握手数据
                        elif NewSid not in RecvingSid.keys() and RecvDataPkt.load[0] == 2:
                            if RecvDataPkt.SegID > 1:
                                ESS.gotoNextStatus(
                                    RecvDataPkt.nid_pro, NewSid, loads=RecvDataPkt.load)
                            else:
                                ESS.newSession(RecvDataPkt.nid_pro, NewSid,
                                               RecvDataPkt.PIDs[1:][::-
                                                                    1], ReturnIP,
                                               flag=False, loads=RecvDataPkt.load, pkt=RecvDataPkt)
                        # 定长数据（包括普通文件，数据库查询结果等）
                        elif NewSid not in RecvingSid.keys():
                            # 新内容
                            if ((RecvDataPkt.load[0] & 1) == 1):
                                # 使用一个data包完成传输
                                PL.Lock_gets.acquire()
                                PL.gets.pop(NewSid)  # 传输完成
                                PL.Lock_gets.release()
                                endflag = 1
                            elif (RecvDataPkt.SegID == 0):
                                # 存在后续相同SIDdata包
                                RecvingSid[NewSid] = 1  # 记录当前SID信息
                                endflag = 0
                            else:
                                return
                            # 将接收到的数据存入缓冲区
                            text = ESS.Decrypt(RecvDataPkt.nid_pro, NewSid, RecvDataPkt.load[1:]) if (
                                RecvDataPkt.load[0] & 4) == 4 else RecvDataPkt.load[1:]
                            if isinstance(SavePath, int):
                                if SavePath == 3:
                                    Lock_SqlResultCache.acquire()
                                    SqlResultCache[RecvDataPkt.nid_pro] = text
                                    Lock_SqlResultCache.release()
                                    if (endflag == 1):
                                        Lock_SqlResultCache.acquire()
                                        SqlResult = SqlResultCache.pop(
                                            RecvDataPkt.nid_pro)
                                        Lock_SqlResultCache.release()
                                        SqlResult = pickle.loads(SqlResult)
                                        print(
                                            "接收到来自NID为<" + str(RecvDataPkt.nid_pro) + ">的数据库查询结果：")
                                        print(SqlResult)
                                elif SavePath == 4:
                                    Lock_ServerQueryCache.acquire()
                                    ServerQueryCache[RecvDataPkt.nid_pro] = text
                                    Lock_ServerQueryCache.release()
                                    if (endflag == 1):
                                        Lock_ServerQueryCache.acquire()
                                        QueryText = pickle.loads(ServerQueryCache.pop(RecvDataPkt.nid_pro))
                                        Lock_ServerQueryCache.release()
                                        SqlResult = self.SqlQuery(QueryText)
                                        if (SqlResult != -1):
                                            SqlResult = pickle.dumps(SqlResult)
                                            Lock_ServerResultCache.acquire()
                                            ServerResultCache[RecvDataPkt.nid_pro] = SqlResult
                                            Lock_ServerResultCache.release()
                            else:
                                PL.ConvertByte(text, SavePath)  # 存储数据
                        else:
                            # 此前收到过SID的数据包
                            if(RecvDataPkt.S != 0) and (RecvDataPkt.SegID == RecvingSid[NewSid]):
                                # 正确的后续数据包
                                if((RecvDataPkt.load[0] & 1) == 1):
                                    # 传输完成
                                    RecvingSid.pop(NewSid)
                                    PL.Lock_gets.acquire()
                                    PL.gets.pop(NewSid)
                                    PL.Lock_gets.release()
                                    endflag = 1
                                else:
                                    RecvingSid[NewSid] += 1
                                    endflag = 0
                                # 将接收到的数据存入缓冲区
                                text = ESS.Decrypt(RecvDataPkt.nid_pro, NewSid, RecvDataPkt.load[1:]) if (
                                    RecvDataPkt.load[0] & 4) == 4 else RecvDataPkt.load[1:]
                                if isinstance(SavePath, int):
                                    if SavePath == 3:
                                        Lock_SqlResultCache.acquire()
                                        SqlResultCache[RecvDataPkt.nid_pro] += text
                                        Lock_SqlResultCache.release()
                                        if (endflag == 1):
                                            Lock_SqlResultCache.acquire()
                                            SqlResult = SqlResultCache.pop(
                                                RecvDataPkt.nid_pro)
                                            Lock_SqlResultCache.release()
                                            SqlResult = pickle.loads(SqlResult)
                                            print(
                                                "接收到来自NID为<" + str(RecvDataPkt.nid_pro) + ">的数据库查询结果：")
                                            print(SqlResult)
                                    elif SavePath == 4:
                                        Lock_ServerQueryCache.acquire()
                                        ServerQueryCache[RecvDataPkt.nid_pro] += text
                                        Lock_SqlResultCache.release()
                                        if (endflag == 1):
                                            Lock_ServerQueryCache.acquire()
                                            QueryText = pickle.loads(ServerQueryCache.pop(RecvDataPkt.nid_pro))
                                            Lock_SqlResultCache.release()
                                            SqlResult = self.SqlQuery(QueryText)
                                            if (SqlResult != -1):
                                                SqlResult = pickle.dumps(SqlResult)
                                                Lock_ServerResultCache.acquire()
                                                ServerResultCache[RecvDataPkt.nid_pro] = SqlResult
                                                Lock_ServerResultCache.release()
                                else:
                                    PL.ConvertByte(text, SavePath)  # 存储数据
                            elif(RecvDataPkt.S != 0) and (RecvDataPkt.SegID < RecvingSid[NewSid]):
                                # 此前已收到数据包（可能是ACK丢失）,仅返回ACK
                                self.signals.output.emit(0, '此前已收到数据包，重传ACK')
                            else:
                                return
                        # 返回ACK
                        NewDataPkt = PL.DataPkt(
                            1, 1, 0, 0, NewSid, nid_pro=RecvDataPkt.nid_pro, SegID=RecvDataPkt.SegID, PIDs=RecvDataPkt.PIDs[1:][::-1])
                        Tar = NewDataPkt.packing()
                        PL.SendIpv4(ReturnIP, Tar)
                    else:
                        # ACK包
                        # 视频流
                        NidCus = RecvDataPkt.nid_cus
                        if (isinstance(PL.AnnSidUnits[NewSid].path, int) and PL.AnnSidUnits[NewSid].path == 1):
                            Lock_WaitingACK.acquire()
                            if (NidCus in WaitingACK.keys()):
                                WaitingACK[NidCus] = 0
                            Lock_WaitingACK.release()
                            return
                        # 回应加密握手包
                        if ESS.checkSession(RecvDataPkt.nid_cus, NewSid) or RecvDataPkt.SegID == 3:
                            ESS.gotoNextStatus(
                                RecvDataPkt.nid_cus, NewSid, SegID=RecvDataPkt.SegID)
                        if (NewSid not in SendingSid.keys()) or (RecvDataPkt.SegID != SendingSid[NewSid][2]-1):
                            return
                        # 定长数据（包括普通文件，数据库查询结果等）
                        if(SendingSid[NewSid][0] > SendingSid[NewSid][2]):
                            # 发送下一片
                            ESSflag = SendingSid[NewSid][5]
                            NidCus = SendingSid[NewSid][3]
                            PL.Lock_AnnSidUnits.acquire()
                            SidPath = PL.AnnSidUnits[NewSid].path
                            PL.Lock_AnnSidUnits.release()
                            # 判断是否传递特殊内容
                            if isinstance(SidPath, int):
                                if SidPath == 3:
                                    Data = ServerResultCache[NidCus]
                                elif SidPath == 4:
                                    Data = QueryCache[NidCus]
                            else:
                                Data = PL.ConvertFile(SidPath)
                            lpointer = SendingSid[NewSid][1] * \
                                SendingSid[NewSid][2]
                            if(SendingSid[NewSid][0] == SendingSid[NewSid][2]+1):
                                # 最后一片
                                text = Data[lpointer:]
                                load = PL.ConvertInt2Bytes(
                                    5 if ESSflag else 1, 1) + (ESS.Encrypt(NidCus, NewSid, text) if ESSflag else text)
                                endflag = 1
                            else:
                                text = Data[lpointer:lpointer +
                                            SendingSid[NewSid][1]]
                                load = PL.ConvertInt2Bytes(
                                    4 if ESSflag else 0, 1) + (ESS.Encrypt(NidCus, NewSid, text) if ESSflag else text)
                                endflag = 0
                            SegID = SendingSid[NewSid][2]
                            SendingSid[NewSid][2] += 1  # 下一片指针偏移
                            NewDataPkt = PL.DataPkt(
                                1, 0, 1, 0, NewSid, nid_cus=SendingSid[NewSid][3], SegID=SegID, PIDs=SendingSid[NewSid][4], load=load)
                            Tar = NewDataPkt.packing()
                            ReturnIP = ''
                            if (len(SendingSid[NewSid][4]) == 0):
                                # 域内请求
                                if (SendingSid[NewSid][3] in PL.PeerProxys.keys()):
                                    ReturnIP = PL.PeerProxys[SendingSid[NewSid][3]]
                                else:
                                    self.signals.output(
                                        "未知的NID：" + hex(SendingSid[NewSid][3]).replace('0x', '').zfill(32))
                            else:
                                PX = SendingSid[NewSid][4][-1] >> 16
                                if (PX in PL.PXs.keys()):
                                    ReturnIP = PL.PXs[PX]
                                else:
                                    self.signals.output(
                                        "未知的PX："+hex(PX).replace('0x', '').zfill(4))
                            PL.SendIpv4(ReturnIP, Tar)
                            # 内容发送完成的特殊操作
                            if isinstance(SidPath, int) and (endflag == 1):
                                if (SidPath == 3):
                                    Lock_ServerResultCache.acquire()
                                    ServerResultCache.pop(NidCus)
                                    Lock_ServerResultCache.release()
                                elif (SidPath == 4):
                                    # 数据库查询指令发送完成，获取查询内容
                                    Lock_QueryCache.acquire()
                                    QueryCache.pop(NidCus)
                                    Lock_QueryCache.release()
                                    SID = hex(NidCus).replace(
                                        '0x', '').zfill(32) + '3'.zfill(40)
                                    PL.Get(SID, 3)
                            # 重传判断，待完善锁机制 #
                            for i in range(3):
                                time.sleep(RTO)
                                if ((NewSid in SendingSid) and (SendingSid[NewSid][2] == SegID+1)):
                                    self.signals.output.emit(
                                        0, '第'+str(SegID)+'片，第'+str(i+1)+'次重传')
                                    PL.SendIpv4(ReturnIP, Tar)
                                    if isinstance(SidPath, int) and (SidPath == 4) and (endflag == 1):
                                        SID = hex(NidCus).replace(
                                            '0x', '').zfill(32) + '3'.zfill(40)
                                        PL.Get(SID, 3)
                                else:
                                    break
                        else:
                            # 发送完成，删除Sending信息
                            SendingSid.pop(NewSid)
                elif data[0] == 0x74:
                    # 收到网络中的control报文
                    # 校验和检验
                    CS = PL.CalculateCS(data[0:8])
                    if(CS != 0):
                        return
                    # 解析报文内容
                    NewCtrlPkt = PL.ControlPkt(0, Pkt=data)
                    self.signals.pathdata.emit(
                        0x74, "", [], NewCtrlPkt.HeaderLength + NewCtrlPkt.DataLength, 0)
                    if (NewCtrlPkt.tag == 8):
                        # 新proxy信息
                        if NewCtrlPkt.ProxyNid != PL.Nid:
                            # 过滤本代理信息
                            PL.PeerProxys[NewCtrlPkt.ProxyNid] = NewCtrlPkt.ProxyIP
                    elif (NewCtrlPkt.tag == 17):
                        # DATA包泄露警告
                        NewSid = ''
                        if NewCtrlPkt.N_sid != 0:
                            NewSid += hex(NewCtrlPkt.N_sid).replace('0x',
                                                                    '').zfill(32)
                        if NewCtrlPkt.L_sid != 0:
                            NewSid += hex(NewCtrlPkt.L_sid).replace('0x',
                                                                    '').zfill(40)
                        tmps = "泄露DATA包的节点源IP: " + NewCtrlPkt.ProxyIP + '\n'
                        tmps += "泄露DATA包内含的SID: " + NewSid + '\n'
                        tmps += "泄露DATA包的目的NID: " + f"{NewCtrlPkt.CusNid:032x}"
                        self.signals.output.emit(2, tmps)
                    elif (NewCtrlPkt.tag == 18):
                        # 外部攻击警告
                        tmps = "告警BR所属NID: " + \
                            f"{NewCtrlPkt.BRNid:032x}" + '\n'
                        for key in NewCtrlPkt.Attacks.keys():
                            tmps += "攻击所属AS号: " + \
                                str(key) + '\n'  # 若为0，则为未知AS来源的攻击
                            tmps += "对应AS号的攻击次数: " + \
                                str(NewCtrlPkt.Attacks[key]) + '\n'
                        self.signals.output.emit(2, tmps)


class ControlPktSender(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.signals = pktSignals()

    def run(self):
        # 向RM发送注册报文
        self.signals.output.emit(
            0, "向RM发送注册报文，注册IP：" + PL.IPv4 + "；注册NID：" + hex(PL.Nid))
        PL.AnnProxy()
        # 重传判断
        for i in range(3):
            time.sleep(RTO)
            if (PL.RegFlag == 0):
                self.signals.output.emit(0, '注册报文，第' + str(i+1) + '次重传')
                PL.AnnProxy()
            else:
                break


class video_customer(threading.Thread):
    flag = 0  # 等待状态标记

    def __init__(self):
        threading.Thread.__init__(self)
        self.flag = 0

    def run(self):
        while 1:
            if(self.flag == 0):
                frame = FrameCache.get()
                sid = FrameSid.get()
                self.flag = 1
                cv2.imshow("img", frame)  # 显示图像
                k = cv2.waitKey(10) & 0xff
            else:
                try:
                    frame = FrameCache.get(timeout=2)
                    sid = FrameSid.get()
                    cv2.imshow("img", frame)  # 显示图像
                    k = cv2.waitKey(10) & 0xff
                    if k == 27:
                        PL.Lock_gets.acquire()
                        if (sid in PL.gets.keys()):
                            PL.gets.pop(sid)
                            cv2.destroyAllWindows()
                        PL.Lock_gets.release()
                except:
                    self.flag = 0
                    break


class Monitor(threading.Thread):
    ''' docstring: 自行实现的监听线程类，继承自线程类 '''

    def __init__(self, message=None, path=None):
        threading.Thread.__init__(self)
        # 需要绑定的目标函数，初始化时保存，后面绑定
        self.message = message
        self.path = path

    def parser(self, packet):
        ''' docstring: 调用通用语法解析器线程 '''
        GeneralHandler = PktHandler(packet)
        # 绑定输出到目标函数
        GeneralHandler.signals.output.connect(self.message)
        GeneralHandler.signals.pathdata.connect(self.path)
        GeneralHandler.start()

    def run(self):
        AnnSender = ControlPktSender()
        AnnSender.signals.output.connect(self.message)
        AnnSender.signals.output.emit(0, "开启报文监听")
        AnnSender.start()
        VideoCus = video_customer()
        VideoCus.start()
        # sniff(filter="ip", iface = "VirtualBox Host-Only Network", prn=self.parser, count=0)
        sniff(filter="ip", prn=self.parser, count=0)
