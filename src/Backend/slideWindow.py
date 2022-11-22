from __future__ import annotations

from enum import IntEnum
import threading
from collections.abc import Callable

from bitmap import BitMap
import math
import queue

RTO = 1


class SendingSidField(IntEnum):
    CHIP_NUM = 0
    CHIP_LENGTH = 1
    CHIP_NEXT = 2
    NID_CUSTOMER = 3
    PIDS = 4
    ESS_FLAG = 5
    SENDING_WINDOW = 6
    INVALID = -1

# 滑动窗口相关


class SlideWindow:
    WINDOW_SIZE = 0xfffe
    MAX_COUNT = 0xffff

    def __init__(self, total_block: int, window_size: int = WINDOW_SIZE):
        # 线程同步操作锁
        self.__lock__ = threading.Lock()
        # 记录所有块
        self.blocks = total_block
        # 当前块
        self.cur_block = 0
        # 滑动窗口部分
        self.window_size = min(window_size, self.MAX_COUNT)
        self.left = 0
        self.right = min(self.left + self.window_size, self.blocks)
        self.cur = self.left
        # # 使用 BitMap 标记是否已经收到 ACK
        self.bitmap = BitMap(min(total_block, self.MAX_COUNT))
        # # 窗口大小更新相关
        self.cur_window_size = self.window_size

    def add_left(self) -> None:
        """ 窗口下界后移 """
        self.left += 1
        self.left &= self.MAX_COUNT
        self.cur_window_size -= 1
        self.cur_block += 1

    def add_right(self) -> None:
        """
        窗口上界后移
        在窗口缩小时不进行该操作以收缩窗口
        """
        while self.cur_window_size < self.window_size \
                and self.cur_block + self.cur_window_size < self.blocks:
            self.right += 1
            self.right &= self.MAX_COUNT
            self.cur_window_size += 1

    def is_finish(self):
        return self.cur_block >= self.blocks  # 可能是 ==


class SendingWindow(SlideWindow):
    """
    发送端滑动窗口
    """

    def __init__(self, total_block: int, window_size: int = SlideWindow.WINDOW_SIZE):
        super().__init__(total_block, window_size)
        # 超时重传相关
        self.timer = None

    def ack(self, ack_num: int, new_window_size: int = None) -> None:
        """
        接受 ACK 包，更新窗口
        """
        with self.__lock__:
            if isinstance(new_window_size, int):
                self.window_size = new_window_size
            index = self.left & self.MAX_COUNT
            while index != self.right:
                if index == ack_num:
                    if not self.bitmap.test(index):
                        self.bitmap.set(index)
                    break
                index += 1
                index &= self.MAX_COUNT
            while self.bitmap.test(self.left):
                self.bitmap.reset(self.left)
                self.add_left()
                self.add_right()

    def send(self, num=1) -> list[tuple[int, int]]:
        """
        :param num: 发送的数据包数量
        *尝试* 发送指定数量 (默认为 1 ) 的数据包
        """
        if num > self.MAX_COUNT or num <= 0:
            return []
        res = []
        with self.__lock__:
            while self.cur != self.right and len(res) < num:
                offset = self.cur - self.left
                if offset < 0:
                    offset += self.MAX_COUNT
                res.append((self.cur, self.cur_block + offset))
                self.cur += 1
                self.cur &= self.MAX_COUNT
            return res

    def send_all(self) -> list[tuple[int, int]]:
        """
        尝试发送 *所有* 当前能发送的数据包
        """
        return self.send(self.cur_window_size)

    def resend(self) -> list[tuple[int, int]]:
        """
        获取所有未收到 ACK 的数据包列表
        """
        res = []
        index = self.left
        with self.__lock__:
            while index != self.cur:
                if not self.bitmap.test(index):
                    offset = index - self.left
                    if offset < 0:
                        offset += self.MAX_COUNT
                    res.append((index, self.cur_block + offset))
                index += 1
                index &= self.MAX_COUNT
            return res

    def update_timer(self, callback: Callable, timeout=RTO):
        """
        :param callback: 超时后的回调函数
        :param timeout: 超时时间
        更新超时重传定时器
        """
        with self.__lock__:
            self.cancel_timer()
            # self.timer = threading.Timer(timeout, callback)
            # self.timer.start()

    def cancel_timer(self):
        """
        取消超时重传定时器
        """
        if isinstance(self.timer, threading.Timer):
            self.timer.cancel()
        self.timer = None


class ReceivingWindow(SlideWindow):
    """
    接收端滑动窗口
    """
    INT_MAX = 0xffff_ffff

    def __init__(self, save_path: str, window_size: int = SlideWindow.WINDOW_SIZE):
        super().__init__(self.INT_MAX, window_size)
        self.save_path = save_path
        self.file = open(save_path, 'wb')
        self.cache: dict[int, bytes] = {}
        self.ending = False

    def receive(self, seq_num: int, data: bytes, last_segment: int = 0) -> tuple[int, int]:
        """
        :param seq_num: 收到的数据包序号
        :param data: 收到的数据包数据
        :param last_segment: 是否还有后续数据包
        :return: (ACK 包序号, 接受包窗口大小)
        """
        with self.__lock__:
            index = self.left & self.MAX_COUNT
            while index != self.right:
                if index == seq_num:
                    if last_segment == 1:
                        self.ending = True
                        self.right = index + 1
                    if not self.bitmap.test(index):
                        self.cache[index] = data
                        self.bitmap.set(index)
                    break
                index += 1
                index &= self.MAX_COUNT
            while self.bitmap.test(self.left):
                self.cur_block += 1
                # 文件落盘，清除缓存
                self.file.write(self.cache.pop(self.left))
                self.bitmap.reset(self.left)
                self.add_left()
                if not self.ending:
                    self.add_right()
            recv_window = self.right - self.left
            if recv_window < 0:
                recv_window += self.MAX_COUNT
            return self.left, recv_window

    def is_finish(self):
        return self.ending and self.left == self.right

    def close(self):
        """
        释放缓存，关闭文件
        """
        with self.__lock__:
            self.cache.clear()
            self.cache = None
            self.file.close()


class SendingThread(threading.Thread):
    def __init__(self, data):
        super().__init__()
        self.ready = False
        
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

