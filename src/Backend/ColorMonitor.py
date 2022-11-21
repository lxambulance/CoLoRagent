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
import InnerConnectionServer as ics
import establishSecureSession as ESS
from SlideWindow import SendingWindow, ReceivingWindow, SendingThread
from CoLoRProtocol.CoLoRpacket import (
    ColorGet, ColorData, ColorControl, IP, COLOR_PROTOCOL_NUMBER,
    COLOR_NOW_VERSION, MINIMAL_PACKET_LENGTH
)


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


# 异步线程变量
background_tasks = set()


class Monitor(threading.Thread):
    """ docstring: 监听线程类 """
    MAX_RX_NUM = 5
    sending_threads = {}

    def __init__(self):
        threading.Thread.__init__(self)
        # 监听raw_socket中color编号的IP报文
        self.s = socket.socket(socket.AF_INET, socket.SOCK_RAW, COLOR_PROTOCOL_NUMBER)
        self.s.bind((bfl.IPv4, 0))
        self.controlflag = True

    def run(self):
        loop = asyncio.get_event_loop()
        self.msgqueue = [asyncio.Queue(maxsize=RX_QUEUE_SIZE) for _ in range(Monitor.MAX_RX_NUM)]
        receiver_tasks = [self.receiver(x) for x in range(Monitor.MAX_RX_NUM)]
        parser_tasks = [self.parser(x) for x in range(Monitor.MAX_RX_NUM)]
        loop.run_until_complete(asyncio.gather(*receiver_tasks, *parser_tasks))

    async def receiver(self, id):
        loop = asyncio.get_event_loop()
        count = 0
        while self.controlflag:
            count += 1
            pkt = await loop.sock_recv(self.s, 2048)
            try:
                self.msgqueue[id].put_nowait(pkt)
            except asyncio.QueueFull:
                print(f"too many packet received! {count}")

    def add_tasks(self, function):
        """ docstring: 添加后台任务 """
        task = asyncio.create_task(function)
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)

    async def parser(self, id):
        """ docstring: 收包处理程序 """
        count = 0
        while self.controlflag:
            try:
                raw_data = self.msgqueue[id].get_nowait()
            except asyncio.QueueEmpty:
                # 没有需要处理的报文，协程等待，不同协程等待时间不同
                await asyncio.sleep(id+1)
                continue
            count += 1
            packet = IP(raw_data)
            # 过滤掉非法报文
            if packet.payload.Packet_Length < MINIMAL_PACKET_LENGTH or packet.payload.Version != COLOR_NOW_VERSION:
                continue
            if bfl.RegFlag == 0:
                # 注册状态
                # 过滤掉其他格式的包
                if packet.payload.Packet_Length < 8 or packet.payload.Type != 4 or packet.payload.Subtype != ColorControl.PROXY_REGISTER_REPLY:
                    return
                self.add_tasks(self.RMhello(packet.payload))
            elif bfl.RegFlag == 1:
                # 运行状态
                if packet.payload.Type == 2:
                    # 收到网络中的get报文
                    self.add_tasks(self.handleGet(packet.payload))
                elif packet.payload.Type == 3:
                    # 收到网络中的data报文
                    self.add_tasks(self.handleData(packet.payload))
                elif packet.payload.Type == 4:
                    # 收到网络中的control报文
                    self.add_tasks(self.handleControl(packet.payload))
                else:
                    # 收到网络中的ann报文，当做错误忽略
                    return

    async def RMhello(self, controlpacket):
        """ docstring: 注册流程处理 """
        # 校验和检验
        if bfl.CalculateCS(bytes(controlpacket)[0:8]) != 0:
            return
        # 解析报文内容
        for proxy in controlpacket.ASInfo.IP_NID_List:
            if proxy.NID != bfl.NID:
                bfl.Proxys[proxy.NID] = proxy.IP
        for BR in controlpacket.ASInfo.PX_IP_List:
            bfl.BRs[BR.PX] = BR.IP
        # 发送前端信息
        reply = {"type": "message", "data": {"messageType": 0, "message": "代理注册完成，开启网络功能"}}
        await ics.put_reply_await(reply)
        bfl.RegFlag = 1

    async def handleGet(self, getpacket):
        """ docstring: 处理Get报文 """
        # 校验和检验
        if bfl.CalculateCS(bytes(getpacket)) != 0:
            return
        # 发送前端信息
        SID = getpacket.NSID.hex()+getpacket.LSID.hex()
        self.signals.pathdata.emit(
            0x72, SID, getpacket.PID_List, getpacket.Packet_Length, getpacket.NID.hex())
        reply = {"type": "pathdata", "data": {
            "pkttype": 0x72,
            "SID": SID,
            "paths": getpacket.PID_List,
            "size": getpacket.Packet_Length,
            "NID": getpacket.NID.hex()}}
        await ics.put_reply_await(reply)
        # 判断是否为已通告条目
        if SID not in bfl.AnnSidUnits.keys():
            return
        # TODO: 修改起线程方式
        new_sending_thread = SendingThread(getpacket)
        if new_sending_thread.ready:
            new_sending_thread.send_block_packets()
            new_sending_thread.start()
            self.sending_threads[(new_sending_thread.sid,
                                  new_sending_thread.dst_nid)] = new_sending_thread

    async def handleData(self, datapacket):
        """ docstring: 处理Data报文 """
        # 校验和检验
        HeaderLength = datapacket.Header_Length
        if bfl.CalculateCS(bytes(datapacket)[0:HeaderLength]) != 0:
            return
        # 发送前端信息
        NewSID = datapacket.NSID.hex() + datapacket.LSID.hex()
        reply = {"type": "pathdata", "data": {
            "pkttype": 0x73 | (datapacket.Flags.B << 8),
            "SID": NewSID,
            "paths": datapacket.PID_List,
            "size": datapacket.Packet_Length,
            "NID": datapacket.Source_NID.hex()}}
        await ics.put_reply_await(reply, myNID=datapacket.Destination_NID.hex())
        if datapacket.Flags.B == 0:
            # 收到“真”数据包
            # 判断是否已请求条目
            if NewSID not in bfl.gets.keys():
                return
            SavePath = bfl.gets[NewSID]
            ReturnIP = ''
            if datapacket.PID_Num <= 1:
                # 域内
                PeerNID = datapacket.Source_NID
                if PeerNID in bfl.Proxys.keys():
                    ReturnIP = bfl.Proxys[PeerNID]
                else:
                    reply = {"type": "message", "data": {
                        "messageType": 1, "message": "未知的NID=" + PeerNID.hex()}}
                    await ics.put_reply_await(reply)
            else:
                # 域外
                PX = datapacket.PID_List[1] >> 16
                if PX in bfl.BRs.keys():
                    ReturnIP = bfl.BRs[PX]
                else:
                    reply = {"type": "message", "data": {
                        "messageType": 1, "message": f"未知的PX={PX:x}"}}
                    await ics.put_reply_await(reply)
            # warning: returnIP为空不一定错误
            # TODO：goto VideoApp 视频流数据
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
                        FrameSid.put(NewSID)
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
            elif NewSID not in RecvingSid.keys() and RecvDataPkt.load[0] == 2:
                if RecvDataPkt.SegID > 1:
                    ESS.gotoNextStatus(
                        RecvDataPkt.nid_pro, NewSID, loads=RecvDataPkt.load)
                else:
                    ESS.newSession(RecvDataPkt.nid_pro, NewSID,
                                   RecvDataPkt.PIDs[1:][::-1], ReturnIP,
                                   flag=False, loads=RecvDataPkt.load, pkt=RecvDataPkt)
            # 定长数据（包括普通文件，数据库查询结果等） TODO: 可能需要加同步锁
            elif NewSID not in RecvingSid.keys():
                # 新内容
                single_pkt = False
                if (RecvDataPkt.load[0] & 1) == 1:
                    # 使用一个data包完成传输
                    single_pkt = True
                    PL.Lock_gets.acquire()
                    PL.gets.pop(NewSID)  # 传输完成
                    PL.Lock_gets.release()
                elif RecvDataPkt.SegID == 0:
                    # 存在后续相同SIDdata包
                    RecvingSid[NewSID] = ReceivingWindow(SavePath)  # 记录当前SID信息
                else:
                    continue
                # 将接收到的数据存入缓冲区
                text = ESS.Decrypt(RecvDataPkt.nid_pro, NewSID, RecvDataPkt.load[1:]) \
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
                        recv_window: ReceivingWindow = RecvingSid[NewSID]
                        recv_window.receive(RecvDataPkt.SegID &
                                            ReceivingWindow.MAX_COUNT, text)
            else:
                # 此前收到过SID的数据包
                if RecvDataPkt.S != 0:
                    recv_window: ReceivingWindow = RecvingSid[NewSID]
                    # 将接收到的数据存入缓冲区
                    text = ESS.Decrypt(RecvDataPkt.nid_pro, NewSID, RecvDataPkt.load[1:]) \
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
            ack_num = datapacket.Segment_ID & SendingWindow.MAX_COUNT
            wnd_size = SendingWindow.WINDOW_SIZE & SendingWindow.MAX_COUNT
            new_seg_id = wnd_size << 0x10 | ack_num
            bfl.SendIpv4(ReturnIP,
                         bytes(ColorData(Flags="B", NSID=NewSID[:16], LSID=NewSID[16:], Destination_NID=datapacket.Source_NID,
                                         Segment_ID=new_seg_id, PID_List=datapacket.PID_List[1:][::-1])))
        else:
            # 收到 “ACK” 数据包
            # TODO：goto VideoApp。转视频流
            NidCus = datapacket.Destination_NID
            if isinstance(PL.AnnSidUnits[NewSID].path, int) and PL.AnnSidUnits[NewSID].path == 1:
                Lock_WaitingACK.acquire()
                if NidCus in WaitingACK.keys():
                    WaitingACK[NidCus] = 0
                Lock_WaitingACK.release()
                return
            # 回应加密握手包
            if ESS.checkSession(RecvDataPkt.nid_cus, NewSID) or RecvDataPkt.SegID == 3:
                ESS.gotoNextStatus(NidCus, NewSID, SegID=RecvDataPkt.SegID)
            if (NewSID, NidCus) not in self.sending_threads.keys():
                return
            # TODO: 需要判断 SendingThread 状态吗?
            sending_thread = self.sending_threads[(NewSID, NidCus)]
            sending_thread.ack(RecvDataPkt)

    async def handleControl(self, controlpacket):
        """ docstring: 处理Control报文 """
        # 校验和检验
        if bfl.CalculateCS(bytes(controlpacket)[0:8]) != 0:
            return
        # 发送前端信息
        reply = {"type": "pathdata", "data": {
            "pkttype": 0x74,
            "SID": "",
            "paths": [],
            "size": controlpacket.Packet_Length+controlpacket.Header_Length,
            "NID": "from intra-domain"}}
        await ics.put_reply_await(reply)
        # 分类处理
        if controlpacket.Subtype == "CONFIG_PROXY":
            # 新proxy信息
            if controlpacket.IP_NID.NID != bfl.NID:
                bfl.Proxys[controlpacket.IP_NID.NID] = controlpacket.IP_NID.IP
        elif controlpacket.Subtype == "ODC_WARNING":
            # DATA包泄露警告
            realpacket = controlpacket.payload.payload
            NewSID = realpacket.NSID.hex() + realpacket.LSID.hex()
            paths = controlpacket.payload.payload.PID_List
            path_str = '-'.join(map(lambda x: f"<{x:08x}>", paths))
            tmps = f"泄露DATA包的节点源IP:\n{controlpacket.payload.src}\n"
            tmps += f"泄露DATA包内含的SID:\n{NewSID}\n"
            tmps += f"泄露DATA包的目的NID:\n{realpacket.Destination_NID:032x}\n"
            tmps += f"泄露DATA包的PID序列:\n{path_str}\n"
            reply = {"type": "message", "data": {"messageType": 2, "message": tmps}}
            await ics.put_reply_await(reply)
        elif controlpacket.Subtype == "ATTACK_WARNING":
            # 外部攻击警告
            tmps = "告警BR所属NID: " + controlpacket.BR_NID.hex() + '\n'
            for attacksummaryunit in controlpacket.Attack_List:
                # 若ASID为0，则为未知AS来源的攻击
                tmps += "攻击所属AS号: " + str(attacksummaryunit.ASID) + '\n'
                tmps += "对应AS号的攻击次数: " + str(attacksummaryunit.Attack_Num) + '\n'
            reply = {"type": "message", "data": {"messageType": 2, "message": tmps}}
            await ics.put_reply_await(reply)
