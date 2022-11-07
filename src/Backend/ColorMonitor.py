# coding=utf-8
""" docstring: CoLoR监听线程，负责与网络组件的报文交互 """
from enum import IntEnum
import queue
import zlib

import cv2
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal
from scapy.all import *
from scapy.layers.inet import IP

import ProxyLib as PL
import establishSecureSession as ESS

from CoLoRProtocol.CoLoRpacket import ColorGet, ColorData, ColorControl
from slideWindow import SendingWindow, ReceivingWindow

import socket
import asyncio
import uvloop


# 文件传输相关全局变量
SendingSid = {}  # 记录内容发送情况，key:SID，value:[片数，单片大小，下一片指针，customer的nid，pid序列]


class SendingSidField(IntEnum):
    CHIP_NUM = 0
    CHIP_LENGTH = 1
    CHIP_NEXT = 2
    NID_CUSTOMER = 3
    PIDS = 4
    ESS_FLAG = 5
    SENDING_WINDOW = 6

    INVALID = -1


RecvingSid = {}  # 记录内容接收情况，key: [SID, NID]，value:接收窗口
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


class pktSignals(QObject):
    """ docstring: 包处理的信号 """
    # finished用于任务结束信号
    finished = pyqtSignal()
    # output用于输出信号
    output = pyqtSignal(int, object)
    # pathdata用于输出路径相关信息
    pathdata = pyqtSignal(int, str, list, int, str)


class DataFlag(IntEnum):
    ESS = 0x4
    LAST = 0x1


class PktHandler(threading.Thread):
    """ docstring: 收包处理程序 """
    sending_threads = {}

    def __init__(self, msgqueue):
        super().__init__()
        self.queue = msgqueue
        # 请将所有需要输出print()的内容改写为信号的发射(self.signals.output.emit())
        self.signals = pktSignals()

    def video_provider(self, Sid, NidCus, PIDs, LoadLength, ReturnIP, randomnum):
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
                if ChipCount + 1 == ChipNum:
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
                if R == 1:
                    Lock_WaitingACK.acquire()
                    if NidCus not in WaitingACK.keys():
                        WaitingACK[NidCus] = 1
                    else:
                        WaitingACK[NidCus] += 1
                    Lock_WaitingACK.release()
                Tar = NewDataPkt.packing()
                if randomnum is None:
                    PL.SendIpv4(ReturnIP, Tar)
                else:
                    tmptar = ColorData(Tar)
                    tmptar.Checksum = None
                    tmptar.Flags.C = True
                    tmptar.HMAC = randomnum
                    tmptar.Header_Length = None
                    tmptar.Packet_Length = None
                    PL.SendIpv4(ReturnIP, tmptar)
                ChipCount += 1
            # 读取下一帧
            ret, frame = capture.read()
            FrameCount += 1
            cv2.imshow("img", frame)
            if cv2.waitKey(10) == 27:
                # 视频提供者主动退出
                Lock_WaitingACK.acquire()
                if NidCus in WaitingACK.keys():
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

    def run(self):
        asyncio.set_event_loop(uvloop.new_event_loop())
        # asyncio.run(self._run())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(*[self._run(x+1) for x in range(5)]))

    async def _run(self, time):
        count = 0
        while True:
            try:
                raw_data = self.queue.get_nowait()
            except asyncio.QueueEmpty:
                await asyncio.sleep(time)
                continue
            count += 1
            self.packet = IP(raw_data)
            data = bytes(self.packet.payload)  # 存入二进制字符串
            PktLength = len(data)
            if PL.RegFlag == 0:
                # 注册中状态
                # 过滤掉其他格式的包。
                if PktLength < 8 or data[0] != 0x74 or data[5] != 6 or PktLength != (
                        data[4] + data[6] + ((data[7]) << 8)):
                    continue
                # 校验和检验
                CS = PL.CalculateCS(data[0:8])
                if CS != 0:
                    continue
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
            elif PL.RegFlag == 1:
                # 正常运行状态
                # 过滤掉其他格式的包。
                if PktLength < 4:
                    continue
                if data[0] == 0x72:
                    # 收到网络中的get报文
                    # 校验和检验
                    CS = PL.CalculateCS(data)
                    if CS != 0:
                        continue
                    new_sending_thread = SendingThread(self.signals, data)
                    if new_sending_thread.ready:
                        new_sending_thread.send_block_packets()
                        new_sending_thread.start()
                        self.sending_threads[(new_sending_thread.sid, new_sending_thread.dst_nid)] = new_sending_thread
                elif data[0] == 0x73:
                    # 收到网络中的data报文(或ACK)
                    # 校验和检验
                    HeaderLength = data[6]
                    CS = PL.CalculateCS(data[0:HeaderLength])
                    if CS != 0:
                        continue
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
                        0x73 | (RecvDataPkt.B << 8), NewSid, RecvDataPkt.PIDs, RecvDataPkt.PktLength,
                        f'{RecvDataPkt.nid_pro:032x}')
                    if RecvDataPkt.B == 0:
                        # 收到数据包
                        # 判断是否为当前代理请求内容
                        PL.Lock_gets.acquire()
                        if NewSid not in PL.gets.keys():
                            PL.Lock_gets.release()
                            continue
                        SavePath = PL.gets[NewSid]
                        PL.Lock_gets.release()
                        ReturnIP = ''
                        if len(RecvDataPkt.PIDs) <= 1:
                            # 域内请求
                            if RecvDataPkt.nid_pro in PL.PeerProxys.keys():
                                ReturnIP = PL.PeerProxys[RecvDataPkt.nid_pro]
                            else:
                                self.signals.output.emit(1,
                                                         "未知的NID：" + hex(RecvDataPkt.nid_pro)
                                                         .replace('0x', '').zfill(32))
                        else:
                            PX = RecvDataPkt.PIDs[1] >> 16
                            if PX in PL.PXs.keys():
                                ReturnIP = PL.PXs[PX]
                            else:
                                self.signals.output.emit(1, "未知的PX：" + hex(PX).replace('0x', '').zfill(4))
                        # 视频流数据
                        if isinstance(SavePath, int) and SavePath == 1:
                            global VideoCache
                            global MergeFlag
                            FrameCount = RecvDataPkt.SegID >> 16
                            ChipCount = RecvDataPkt.SegID % (1 << 16)
                            Lock_VideoCache.acquire()
                            if FrameCount in VideoCache.keys():
                                # 已经收到过当前帧的其他片
                                VideoCache[FrameCount][ChipCount] = RecvDataPkt.load[1:]
                                if RecvDataPkt.load[0] == 1:
                                    MergeFlag[FrameCount] = ChipCount + 1
                                if MergeFlag[FrameCount] == len(VideoCache[FrameCount]):
                                    # 当前帧接收完成
                                    stringData = b''
                                    for Chip in range(MergeFlag[FrameCount]):
                                        stringData += VideoCache[FrameCount][Chip]
                                    stringData = zlib.decompress(stringData)
                                    # 将获取到的字符流数据转换成1维数组
                                    data = np.frombuffer(stringData, np.uint8)
                                    # 将数组解码成图像
                                    decimg = cv2.imdecode(data, cv2.IMREAD_COLOR)
                                    pops = []
                                    for frame in VideoCache.keys():
                                        if frame == FrameCount \
                                                or frame == ((FrameCount - 1) % (1 << 16)) \
                                                or frame == ((FrameCount - 2) % (1 << 16)):
                                            pops.append(frame)
                                    for frame in pops:
                                        VideoCache.pop(frame)
                                        MergeFlag.pop(frame)
                                    FrameSid.put(NewSid)
                                    FrameCache.put(decimg)
                            else:
                                # TODO: 测试清空视频缓存
                                VideoCache = {}
                                MergeFlag = {}
                                # 新的视频帧(这里默认不能单片完成传输，所以不包含显示逻辑)
                                CacheKeys = list(VideoCache.keys())
                                if len(CacheKeys) != 0:
                                    Max = max(CacheKeys)
                                    if (Max == (1 << 16) - 1) or (Max == (1 << 16) - 2):
                                        # 可能出现了重置情况
                                        if 2 in CacheKeys:
                                            Max = 2
                                        elif 1 in CacheKeys:
                                            Max = 1
                                    NewMax = Max
                                    if FrameCount < 10:
                                        if (Max > (1 << 16) - 10) or (FrameCount > Max):
                                            NewMax = FrameCount
                                    elif FrameCount > (1 << 16) - 10:
                                        if (Max > 10) and (FrameCount > Max):
                                            NewMax = FrameCount
                                    elif FrameCount > Max:
                                        NewMax = FrameCount
                                else:
                                    NewMax = FrameCount
                                # 存入视频帧
                                if FrameCount not in VideoCache.keys():
                                    VideoCache[FrameCount] = {}
                                VideoCache[FrameCount][ChipCount] = RecvDataPkt.load[1:]
                                MergeFlag[FrameCount] = ChipCount + 1 if (RecvDataPkt.load[0] == 1) else 0
                                # 重置缓冲区
                                pops = []
                                for frame in VideoCache.keys():
                                    if frame != NewMax \
                                            and frame != ((NewMax - 1) % (1 << 16)) \
                                            and frame != ((NewMax - 2) % (1 << 16)):
                                        pops.append(frame)
                                for frame in pops:
                                    VideoCache.pop(frame)
                                    MergeFlag.pop(frame)
                            Lock_VideoCache.release()
                            if RecvDataPkt.R == 0:
                                continue
                        # 握手数据
                        elif NewSid not in RecvingSid.keys() and RecvDataPkt.load[0] == 2:
                            if RecvDataPkt.SegID > 1:
                                ESS.gotoNextStatus(
                                    RecvDataPkt.nid_pro, NewSid, loads=RecvDataPkt.load)
                            else:
                                ESS.newSession(RecvDataPkt.nid_pro, NewSid,
                                               RecvDataPkt.PIDs[1:][::-1], ReturnIP,
                                               flag=False, loads=RecvDataPkt.load, pkt=RecvDataPkt)
                        # 定长数据（包括普通文件，数据库查询结果等） TODO: 可能需要加同步锁
                        elif NewSid not in RecvingSid.keys():
                            # 新内容
                            single_pkt = False
                            if (RecvDataPkt.load[0] & 1) == 1:
                                # 使用一个data包完成传输
                                single_pkt = True
                                PL.Lock_gets.acquire()
                                PL.gets.pop(NewSid)  # 传输完成
                                PL.Lock_gets.release()
                            elif RecvDataPkt.SegID == 0:
                                # 存在后续相同SIDdata包
                                RecvingSid[NewSid] = ReceivingWindow(SavePath)  # 记录当前SID信息
                            else:
                                continue
                            # 将接收到的数据存入缓冲区
                            text = ESS.Decrypt(RecvDataPkt.nid_pro, NewSid, RecvDataPkt.load[1:]) \
                                if (RecvDataPkt.load[0] & 4) == 4 \
                                else RecvDataPkt.load[1:]
                            if isinstance(SavePath, int):
                                pass
                                # ## DEPRECATED ##
                                # DataBase Operations
                            else:
                                # TODO: 按 SegID 进行存储
                                if single_pkt:
                                    PL.ConvertByte(text, SavePath)  # 存储数据
                                else:
                                    recv_window: ReceivingWindow = RecvingSid[NewSid]
                                    recv_window.receive(RecvDataPkt.SegID & ReceivingWindow.MAX_COUNT, text)
                        else:
                            # 此前收到过SID的数据包
                            if RecvDataPkt.S != 0:
                                recv_window: ReceivingWindow = RecvingSid[NewSid]
                                # 将接收到的数据存入缓冲区
                                text = ESS.Decrypt(RecvDataPkt.nid_pro, NewSid, RecvDataPkt.load[1:]) \
                                    if (RecvDataPkt.load[0] & 4) == 4 \
                                    else RecvDataPkt.load[1:]
                                if isinstance(SavePath, int):
                                    pass
                                    # ## DEPRECATED ##
                                    # DataBase Operations
                                else:
                                    # TODO: 按 SegID 进行存储
                                    recv_window.receive(RecvDataPkt.SegID & ReceivingWindow.MAX_COUNT, text,
                                                        RecvDataPkt.load[0])
                                    if recv_window.is_finish():
                                        recv_window.close()
                            else:
                                continue
                        # 返回ACK TODO: 根据 ReceivingWindow.receive 结果返回 ACK
                        ack_num = RecvDataPkt.SegID & SendingWindow.MAX_COUNT
                        wnd_size = SendingWindow.WINDOW_SIZE & SendingWindow.MAX_COUNT
                        new_seg_id = wnd_size << 0x10 | ack_num
                        NewDataPkt = PL.DataPkt(
                            1, 1, 0, 0, NewSid, nid_pro=RecvDataPkt.nid_pro, SegID=new_seg_id,
                            PIDs=RecvDataPkt.PIDs[1:][::-1])
                        Tar = NewDataPkt.packing()
                        PL.SendIpv4(ReturnIP, Tar)
                    else:
                        # ACK包
                        # 视频流
                        NidCus = RecvDataPkt.nid_cus
                        if isinstance(PL.AnnSidUnits[NewSid].path, int) and PL.AnnSidUnits[NewSid].path == 1:
                            Lock_WaitingACK.acquire()
                            if NidCus in WaitingACK.keys():
                                WaitingACK[NidCus] = 0
                            Lock_WaitingACK.release()
                            continue
                        # print(ESS.checkSession(NidCus, NewSid), RecvDataPkt.SegID)
                        # 回应加密握手包
                        if ESS.checkSession(RecvDataPkt.nid_cus, NewSid) or RecvDataPkt.SegID == 3:
                            ESS.gotoNextStatus(
                                NidCus, NewSid, SegID=RecvDataPkt.SegID)
                        if (NewSid, NidCus) not in self.sending_threads.keys():
                            continue
                        # TODO: 需要判断 SendingThread 状态吗?
                        sending_thread = self.sending_threads[(NewSid, NidCus)]
                        sending_thread.ack(RecvDataPkt)
                elif data[0] == 0x74:
                    # 收到网络中的control报文
                    # 校验和检验
                    CS = PL.CalculateCS(data[0:8])
                    if CS != 0:
                        continue
                    # 解析报文内容
                    NewCtrlPkt = PL.ControlPkt(0, Pkt=data)
                    controlpkt_v2 = ColorControl(data)
                    self.signals.pathdata.emit(
                        0x74, "", [], NewCtrlPkt.HeaderLength + NewCtrlPkt.DataLength, "from intra-domain")
                    if NewCtrlPkt.tag == 8:
                        # 新proxy信息
                        if NewCtrlPkt.ProxyNid != PL.Nid:
                            # 过滤本代理信息
                            PL.PeerProxys[NewCtrlPkt.ProxyNid] = NewCtrlPkt.ProxyIP
                    elif NewCtrlPkt.tag == 17:
                        # DATA包泄露警告
                        NewSid = ''
                        if NewCtrlPkt.N_sid != 0:
                            NewSid += hex(NewCtrlPkt.N_sid).replace('0x',
                                                                    '').zfill(32)
                        if NewCtrlPkt.L_sid != 0:
                            NewSid += hex(NewCtrlPkt.L_sid).replace('0x',
                                                                    '').zfill(40)
                        paths = controlpkt_v2[IP].payload.PID_List
                        path_str = '-'.join(map(lambda x: f"<{x:08x}>", paths))
                        tmps = f"泄露DATA包的节点源IP:\n{NewCtrlPkt.ProxyIP}\n"
                        tmps += f"泄露DATA包内含的SID:\n{NewSid}\n"
                        tmps += f"泄露DATA包的目的NID:\n{NewCtrlPkt.CusNid:032x}\n"
                        tmps += f"泄露DATA包的PID序列:\n{path_str}\n"
                        self.signals.output.emit(2, tmps)
                    elif NewCtrlPkt.tag == 18:
                        # 外部攻击警告
                        tmps = "告警BR所属NID: " + \
                               f"{NewCtrlPkt.BRNid:032x}" + '\n'
                        for key in NewCtrlPkt.Attacks.keys():
                            tmps += "攻击所属AS号: " + \
                                    str(key) + '\n'  # 若为0，则为未知AS来源的攻击
                            tmps += "对应AS号的攻击次数: " + \
                                    str(NewCtrlPkt.Attacks[key]) + '\n'
                        self.signals.output.emit(2, tmps)


class SendingThread(threading.Thread):
    def __init__(self, signals, data):
        super().__init__()
        self.signals = signals
        self.ready = False

        # 解析报文内容
        getpktv2 = ColorGet(data)
        randomnum = None if not getpktv2.Flags.R else getpktv2.Random_Num
        get_pkt = PL.GetPkt(0, Pkt=data)
        # 判断是否为代理当前提供内容
        sid = ''
        if get_pkt.N_sid != 0:
            sid += hex(get_pkt.N_sid).replace('0x', '').zfill(32)
        if get_pkt.L_sid != 0:
            sid += hex(get_pkt.L_sid).replace('0x', '').zfill(40)
        self.signals.pathdata.emit(
            0x72, sid, get_pkt.PIDs, get_pkt.PktLength, f'{get_pkt.nid:032x}')
        PL.Lock_AnnSidUnits.acquire()
        if sid not in PL.AnnSidUnits.keys():
            PL.Lock_AnnSidUnits.release()
            return
        # 返回数据
        sid_unit_level = PL.AnnSidUnits[sid].Strategy_units.get(1, 0)  # 获取密级以备后续使用，没有默认为0
        sid_path = PL.AnnSidUnits[sid].path
        PL.Lock_AnnSidUnits.release()
        nid = get_pkt.nid
        pids = get_pkt.PIDs.copy()
        # 按最大长度减去IP报文和DATA报文头长度(QoS暂默认最长为1字节)，预留位占4字节，数据传输结束标志位位于负载内占1字节
        # sid_load_length = get_pkt.MTU-60-86-(4*len(pids)) - 4 - 1
        sid_load_length = 1200  # 仅在报文不经过RM的点对点调试用
        return_ip: str
        if len(pids) == 0:
            # 域内请求
            if nid in PL.PeerProxys.keys():
                return_ip = PL.PeerProxys[nid]
            else:
                self.signals.output.emit(1, "未知的NID：" +
                                         hex(nid).replace('0x', '').zfill(32))
                return
        else:
            PX = pids[-1] >> 16
            if PX in PL.PXs.keys():
                return_ip = PL.PXs[PX]
            else:
                self.signals.output.emit(
                    1, "未知的PX：" + hex(PX).replace('0x', '').zfill(4))
                return
        # 判断是否传递特殊内容
        if isinstance(sid_path, int):
            if sid_path == 1:
                # 视频服务
                PktHandler.video_provider(self,
                                          sid, nid, pids, sid_load_length, return_ip, randomnum)
                return
            elif (sid_path & 0xff) == 2:
                # 安全链接服务
                ESS.gotoNextStatus(
                    nid, sid, pids=pids, ip=return_ip, randomnum=randomnum)
                return
            else:
                # 未知的特殊内容
                return
        # 非特殊内容
        # 特定密集文件，开启加密传输
        ess_flag = ESS.checkSession(nid, sid)
        if int(sid_unit_level) > 5:
            if not ess_flag:
                ESS.newSession(nid, sid, pids,
                               return_ip, pkt=data, randomnum=randomnum)
                # TODO:                      ^ data 是否可用？
                return
            elif not ESS.sessionReady(nid, sid):
                self.signals.output.emit(1, "收到重复Get，但安全连接未建立")
                return
        # 包解析结束
        self.data = PL.ConvertFile(sid_path)
        self.sid = sid
        self.dst_nid = nid
        self.dst_ip = return_ip
        self.pids = pids
        self.sid_unit_level = sid_unit_level
        self.sid_load_length = sid_load_length
        self.ess_flag = ess_flag
        if ess_flag:
            self.sid_load_length -= 32
        # 新建 SendingWindow
        data_len = len(self.data)
        self.chip_num = math.ceil(data_len / self.sid_load_length)
        self.chip_len = min(self.sid_load_length, data_len)
        self.sending_window = SendingWindow(self.chip_num)
        self.msg_queue = queue.Queue()
        self.ready = True

        self.count_send = 0

    def send_block_packets(self):
        """
        使用滑动窗口对定长数据（如文件） 进行可靠传输
         子函数：
            `send_packet`: 发送单个数据包
            `resend`:      重发所有未收到 ACK 的数据包
         流程：
            1. 从参数中获取并计算相关包头数据
            2. 从滑动窗口中获取待发送包编号和实际文件块号列表
            3. 依次调用 `send_packet` 发送单个数据包
            4. 向滑动窗口更新计时器，注册 `resend` 函数以供超时重传
        """
        data_flag = 0

        def send_packet(pkt_seg_id: int, pkt_chip_index: int):
            """
            发送单个数据包
            """
            end_flag = 0
            start = pkt_chip_index * self.chip_len
            if pkt_chip_index + 1 == self.chip_num:  # 最后一片
                text = self.data[start:]
                end_flag = 1
            else:
                text = self.data[start:start + self.chip_len]
            load = PL.ConvertInt2Bytes(data_flag | end_flag, 1) \
                   + (ESS.Encrypt(self.dst_nid, self.sid, text) if self.ess_flag else text)
            data_pkt = PL.DataPkt(
                1, 0, 1, 0, self.sid,
                nid_cus=self.dst_nid, SegID=pkt_seg_id, PIDs=self.pids, load=load)
            Tar = data_pkt.packing()
            PL.SendIpv4(self.dst_ip, Tar)

        def resend():
            """
            向滑动窗口注册的超时重传回调函数
            会重发所有未收到 ACK 的数据包，并检查本次传输是否已经完成
            若已完成，则会将发送任务从 SendingSid 列表中移除
            """
            for (r_seg_id, r_chip_index) in self.sending_window.resend():
                send_packet(r_seg_id, r_chip_index)
            if self.sending_window.is_finish():
                self.signals.output.emit(1, "发送完成")
                self.ready = False

        for (seg_id, chip_index) in self.sending_window.send_all():
            self.count_send += 1
            # print(self.count_send)
            send_packet(seg_id, chip_index)
        self.sending_window.update_timer(resend)

    def run(self) -> None:
        while True:
            # 收到网络中的data报文(或ACK)
            ack_pkt = self.msg_queue.get()
            # TODO: 添加滑动窗口相关内容
            # 滑动窗口收到 ACK 消息
            # self.sending_window.ack(ack_pkt.SegID & SendingWindow.MAX_COUNT)
            self.send_block_packets()

    def ack(self, ack_pkt):
        """
        发送线程收到 ACK 包
        """
        self.msg_queue.put(ack_pkt)


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
            if PL.RegFlag == 0:
                self.signals.output.emit(0, '注册报文，第' + str(i + 1) + '次重传')
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
            if self.flag == 0:
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
                        if sid in PL.gets.keys():
                            PL.gets.pop(sid)
                            cv2.destroyAllWindows()
                        PL.Lock_gets.release()
                except:
                    self.flag = 0
                    break


class Monitor(threading.Thread):
    """ docstring: 自行实现的监听线程类，继承自线程类 """

    def __init__(self, message=None, path=None):
        threading.Thread.__init__(self)
        # 需要绑定的目标函数，初始化时保存，后面绑定
        self.message = message
        self.path = path
        self.s = socket.socket(socket.AF_INET, socket.SOCK_RAW, 150)
        self.s.bind((PL.IPv4, 0))

    def parser(self, packet):
        """ docstring: 调用通用语法解析器线程 """
        GeneralHandler = PktHandler(packet)
        # 绑定输出到目标函数
        GeneralHandler.signals.output.connect(self.message)
        GeneralHandler.signals.pathdata.connect(self.path)
        GeneralHandler.start()

    def run(self):
        AgentRegisterSender = ControlPktSender()
        AgentRegisterSender.signals.output.connect(self.message)
        AgentRegisterSender.signals.output.emit(0, "开启报文监听")
        AgentRegisterSender.start()
        # VideoCus = video_customer()
        # VideoCus.start()

        asyncio.set_event_loop(uvloop.new_event_loop())
        self.msgqueue = asyncio.Queue(maxsize=1024)
        parser = PktHandler(self.msgqueue)
        parser.signals.output.connect(self.message)
        parser.signals.pathdata.connect(self.path)
        parser.start()
        # asyncio.run(self._run())
        loop = asyncio.get_event_loop()
        tasks = [ self._run() for _ in range(5) ]
        loop.run_until_complete(asyncio.gather(*tasks))

    async def _run(self):
        loop = asyncio.get_event_loop()
        count = 0
        while True:
            count += 1
            pkt = await loop.sock_recv(self.s, 2048)
            # print(count)
            try:
                self.msgqueue.put_nowait(pkt)
            except asyncio.QueueFull:
                print(f"too many packet received! {count}")
