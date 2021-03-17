# CoLoR监听线程，负责与网络组件的报文交互
from scapy.all import *
import threading
import ProxyLib as PL
import math
import time


SendingSid = {}  # 记录内容发送情况，key:SID，value:[片数，单片大小，下一片指针，customer的nid，pid序列]
RecvingSid = {}  # 记录内容接收情况，key:SID，value:下一片指针
RTO = 1  # 超时重传时间


class PktHandler(threading.Thread):
    packet = ''

    def __init__(self, packet):
        threading.Thread.__init__(self)
        self.packet = packet

    def run(self):
        if 'Raw' in self.packet:
            data = bytes(self.packet['Raw'])  # 存入二进制字符串
            PktLength = len(data)
            if PktLength < 4 or PktLength != (data[2]+(data[3] << 8)):
                # 长度不匹配
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
                    NewSid += hex(NewGetPkt.N_sid).replace('0x', '').zfill(32)
                if NewGetPkt.L_sid != 0:
                    NewSid += hex(NewGetPkt.L_sid).replace('0x', '').zfill(40)
                if NewSid not in PL.AnnSidUnits.keys():
                    return
                # 返回数据
                SidPath = PL.AnnSidUnits[NewSid].path
                NidCus = NewGetPkt.nid
                PIDs = NewGetPkt.PIDs.copy()
                # 按最大长度减去IP报文和DATA报文头长度(QoS暂默认最长为1字节)，预留位占4字节，数据传输结束标志位位于负载内占1字节
                SidLoadLength = NewGetPkt.MTU-60-86-(4*len(PIDs)) - 4 - 1
                # SidLoadLength = 1000  # 仅在报文不经过RM的点对点调试用
                DataLength = len(PL.ConvertFile(SidPath))
                if (DataLength <= SidLoadLength):
                    ChipNum = 1
                    ChipLength = DataLength
                    load = PL.ConvertInt2Bytes(1, 1) + PL.ConvertFile(SidPath)
                else:
                    ChipNum = math.ceil(DataLength/SidLoadLength)
                    ChipLength = SidLoadLength
                    load = PL.ConvertInt2Bytes(
                        0, 1) + PL.ConvertFile(SidPath, rpointer=SidLoadLength)
                SendingSid[NewSid] = [ChipNum, ChipLength, 1, NidCus, PIDs]
                NewDataPkt = PL.DataPkt(
                    1, 0, 1, 0, NewSid, nid_cus=NidCus, SegID=0, PIDs=PIDs, load=load)
                Tar = NewDataPkt.packing()
                PL.SendIpv4(PL.GetBRip(), Tar)
                # 重传判断，待完善锁机制 #
                for i in range(3):
                    time.sleep(RTO)
                    if ((NewSid in SendingSid) and (SendingSid[NewSid][2] == 1)):
                        print('第'+str(SendingSid[NewSid]
                                      [2]-1)+'片，第'+str(i+1)+'次重传')
                        PL.SendIpv4(PL.GetBRip(), Tar)
                    else:
                        break
            elif (data[0] == 0x73):
                # 收到网络中的data报文(ACK)
                # 校验和检验
                CS = PL.CalculateCS(data)
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
                if(RecvDataPkt.B == 0):
                    # 收到数据包，存储到本地并返回ACK
                    # 判断是否为当前代理请求内容
                    if NewSid not in PL.gets.keys():
                        return
                    SavePath = PL.gets[NewSid]
                    if NewSid not in RecvingSid.keys():
                        # 新内容
                        if (RecvDataPkt.load[0] == 1):
                            # 使用一个data包完成传输
                            PL.Lock_gets.acquire()
                            PL.gets.pop(NewSid)  # 传输完成
                            PL.Lock_gets.release()
                        elif (RecvDataPkt.SegID == 0):
                            # 存在后续相同SIDdata包
                            RecvingSid[NewSid] = 1  # 记录当前SID信息
                        else:
                            return
                        PL.ConvertByte(RecvDataPkt.load[1:], SavePath)  # 存储数据
                    else:
                        # 此前收到过SID的数据包
                        if(RecvDataPkt.S != 0) and (RecvDataPkt.SegID == RecvingSid[NewSid]):
                            # 正确的后续数据包
                            if(RecvDataPkt.load[0] == 1):
                                # 传输完成
                                RecvingSid.pop(NewSid)
                                PL.Lock_gets.acquire()
                                PL.gets.pop(NewSid)
                                PL.Lock_gets.release()
                            else:
                                RecvingSid[NewSid] += 1
                            PL.ConvertByte(
                                RecvDataPkt.load[1:], SavePath)  # 存储数据
                        elif(RecvDataPkt.S != 0) and (RecvDataPkt.SegID < RecvingSid[NewSid]):
                            # 此前已收到数据包（可能是ACK丢失）,仅返回ACK
                            print('此前已收到数据包，重传ACK')
                        else:
                            return
                    # 返回ACK
                    NewDataPkt = PL.DataPkt(
                        1, 1, 0, 0, NewSid, nid_pro=RecvDataPkt.nid_pro, SegID=RecvDataPkt.SegID, PIDs=RecvDataPkt.PIDs[1:])
                    Tar = NewDataPkt.packing()
                    PL.SendIpv4(PL.GetBRip(), Tar)
                else:
                    # ACK包
                    if NewSid not in SendingSid.keys():
                        return
                    if(SendingSid[NewSid][0] > SendingSid[NewSid][2]):
                        # 发送下一片
                        SidPath = PL.AnnSidUnits[NewSid].path
                        lpointer = SendingSid[NewSid][1] * \
                            SendingSid[NewSid][2]
                        if(SendingSid[NewSid][0] == SendingSid[NewSid][2]+1):
                            # 最后一片
                            load = PL.ConvertInt2Bytes(
                                1, 1) + PL.ConvertFile(SidPath, lpointer=lpointer)
                        else:
                            load = PL.ConvertInt2Bytes(
                                0, 1) + PL.ConvertFile(SidPath, lpointer=lpointer, rpointer=lpointer+SendingSid[NewSid][1])
                        SegID = SendingSid[NewSid][2]
                        SendingSid[NewSid][2] += 1  # 下一片指针偏移
                        NewDataPkt = PL.DataPkt(
                            1, 0, 1, 0, NewSid, nid_cus=SendingSid[NewSid][3], SegID=SegID, PIDs=SendingSid[NewSid][4], load=load)
                        Tar = NewDataPkt.packing()
                        PL.SendIpv4(PL.GetBRip(), Tar)
                        # 重传判断，待完善锁机制 #
                        for i in range(3):
                            time.sleep(RTO)
                            if ((NewSid in SendingSid) and (SendingSid[NewSid][2] == SegID+1)):
                                print('第'+str(SegID)+'片，第'+str(i+1)+'次重传')
                                PL.SendIpv4(PL.GetBRip(), Tar)
                            else:
                                break
                    else:
                        # 发送完成，删除Sending信息
                        SendingSid.pop(NewSid)


class Monitor(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def parser(self, packet):
        # 调用通用语法解析器线程
        GeneralHandler = PktHandler(packet)
        GeneralHandler.start()

    def run(self):
        print("报文监听线程开启")
        sniff(filter="ip", prn=self.parser, count=0)
