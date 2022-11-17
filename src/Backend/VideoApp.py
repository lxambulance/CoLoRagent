# coding=utf-8
""" docstring: 视频处理应用 """


class video_customer(threading.Thread):
    flag = 0  # 等待状态标记

    def __init__(self):
        threading.Thread.__init__(self)
        self.flag = 0

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
