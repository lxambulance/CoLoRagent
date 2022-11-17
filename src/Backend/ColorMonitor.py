# coding=utf-8
""" docstring: CoLoR监听线程，负责与网络组件的报文交互 """


import cv2
import zlib
import queue
import socket
import asyncio
import numpy as np
from scapy.all import *
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ModuleNotFoundError:
    pass


import BackendFunctionLib as bfl
import establishSecureSession as ESS
from SlideWindow import SendingWindow, ReceivingWindow
from CoLoRProtocol.CoLoRpacket import ColorGet, ColorData, ColorControl, IP, COLOR_PROTOCOL_NUMBER


# 文件传输相关全局变量
RX_QUEUE_SIZE = 1024
SendingSid = {}  # 记录内容发送情况，key:SID，value:[片数，单片大小，下一片指针，customer的nid，pid序列]
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


# class pktSignals(QObject):
#     """ docstring: 包处理的信号 """
#     # finished用于任务结束信号
#     finished = pyqtSignal()
#     # output用于输出信号
#     output = pyqtSignal(int, object)
#     # pathdata用于输出路径相关信息
#     pathdata = pyqtSignal(int, str, list, int, str)


class Monitor(threading.Thread):
    """ docstring: 监听线程类 """
    MAX_RX_NUM = 5
    MAX_PX_NUM = 5
    sending_threads = {}

    def __init__(self):
        threading.Thread.__init__(self)
        # 监听raw_socket中color编号的IP报文
        self.s = socket.socket(socket.AF_INET, socket.SOCK_RAW, COLOR_PROTOCOL_NUMBER)
        self.s.bind((bfl.IPv4, 0))
        self.msgqueue = asyncio.Queue(maxsize=RX_QUEUE_SIZE)
        self.controlflag = True

    def run(self):
        loop = asyncio.get_event_loop()
        receiver_tasks = [self.receiver() for _ in range(Monitor.MAX_RX_NUM)]
        parser_tasks = [self.parser(x+1) for x in range(Monitor.MAX_PX_NUM)]
        loop.run_until_complete(asyncio.gather(*receiver_tasks, *parser_tasks))

    async def receiver(self):
        loop = asyncio.get_event_loop()
        count = 0
        while self.controlflag:
            count += 1
            pkt = await loop.sock_recv(self.s, 2048)
            try:
                self.msgqueue.put_nowait(pkt)
            except asyncio.QueueFull:
                print(f"too many packet received! {count}")

    async def parser(self, time):
        """ docstring: 收包处理程序 """
        count = 0
        while self.controlflag:
            try:
                raw_data = self.msgqueue.get_nowait()
            except asyncio.QueueEmpty:
                # 没有需要处理的报文，协程等待，不同协程等待时间不同
                await asyncio.sleep(time)
                continue
            count += 1
            self.packet = IP(raw_data)
            # TODO: 存入二进制字符串 没有必要？建议删除
            # data = bytes(self.packet.payload)  
            # PktLength = len(data)
            if bfl.RegFlag == 0:
                # TODO: 添加任务协程，
                # 注册中状态
                # 过滤掉其他格式的包
                if PktLength < 8 or data[0] != 0x74 or data[5] != 6 or PktLength != (data[4] + data[6] + ((data[7]) << 8)):
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
                bfl.RegFlag = 1
            elif bfl.RegFlag == 1:
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
                        self.sending_threads[(new_sending_thread.sid,
                                              new_sending_thread.dst_nid)] = new_sending_thread
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
                                self.signals.output.emit(
                                    1, "未知的PX：" + hex(PX).replace('0x', '').zfill(4))
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
                                MergeFlag[FrameCount] = ChipCount + \
                                    1 if (RecvDataPkt.load[0] == 1) else 0
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
                                    recv_window.receive(RecvDataPkt.SegID &
                                                        ReceivingWindow.MAX_COUNT, text)
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
