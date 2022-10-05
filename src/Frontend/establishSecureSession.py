# coding=utf-8


import os
import json
import time
import ProxyLib as PL
import ColorMonitor as CM
from threading import Thread
from PyQt5.QtCore import pyqtSignal, QObject
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import sys
__BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
sys.path.append(__BASE_DIR)
from CoLoRProtocol.CoLoRpacket import ColorData


class ESSsignals(QObject):
    output = pyqtSignal(int, object)

ESSsignal = ESSsignals()


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.hex()
        return json.JSONEncoder.default(self, obj)

class keys():
    ''' docstring: 密钥类，存储自身密钥 '''
    def __init__(self):
        self.private_key = None
        self.public_key = None
        self.nid = None
        self.public_key_bytes = ""
        self.rsa_private_key = None

    def loadKey(self, data):
        self.private_key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(data['private_key']))
        self.public_key_bytes = bytes.fromhex(data['public_key'])
        self.public_key = Ed25519PublicKey.from_public_bytes(self.public_key_bytes)
        self.nid = bytes.fromhex(data['myNID'])
        self.rsa_private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )

    def saveKey(self, path):
        with open(path, 'r') as f:
            data = json.load(f)
        data['private_key'] = self.private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        data['public_key'] = self.public_key_bytes
        data['myNID'] = self.nid
        with open(path, 'w') as f:
            json.dump(data, f, cls=MyEncoder)

    def regenerate(self):
        ''' docstring: 重新生成一次密钥对 '''
        self.private_key = Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        self.public_key_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        self.nid = HKDF(
            algorithm=hashes.SHA256(),
            length=16,
            salt=None,
            info=None
        ).derive(self.public_key_bytes)
        self.rsa_private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        rsa_public_key = self.rsa_private_key.public_key()
        self.rsa_public_key_bytes = rsa_public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.PKCS1
        )
        rsa_private_key_bytes = self.rsa_private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        # print(self.rsa_public_key_bytes)
        # print(rsa_private_key_bytes)
        # print("public key:", self.public_key_bytes.hex())
        # print("nid:", self.nid.hex())

def checkNidPublickey(nid, public_key_bytes):
    calcnid = HKDF(
        algorithm=hashes.SHA256(),
        length=16,
        salt=None,
        info=None
    ).derive(public_key_bytes)
    return nid == calcnid.hex()

def checkSignature(message, signature, public_key_bytes):
    public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
    try:
        public_key.verify(signature, message)
    except InvalidSignature:
        return False
    finally:
        return True

Agent = keys()
sessionlist = {} # key: nid+sid, value:Session()
specsid2sid = {} # key:sid, value:sid
# TODO: 遗留问题，通过nid找sid，因为get包缺少第二个sid字段
RTO = 2 # 超时重传时间默认设置为两秒

class Session():
    ''' docstring: 会话类，主要的存储对象 '''
    def __init__(self, nid, sid, pids, ip):
        self.nid = nid
        self.sid = sid
        self.pids = pids
        self.ip = ip
        self.myStatus = 0
        self.sessionId = None # TODO: 处理快速连接
        self.ECDH_private_key_self = ec.generate_private_key(ec.SECP384R1()) # 由于后续两端使用位置不一致，这里直接初始化
        self.ECDH_shared_key = None
        self.random_client = None
        self.random_server = None
        self.mainKey = None
        self.remote_ECDH_public_key_bytes = None
        self.remote_public_key_bytes = None
        self.randomnum = None

    def sendFirstHandshake(self, nid=None, sid=None, pids=None, ip=None):
        ''' docstring: 发送第一个握手包 '''
        self.random_server = os.urandom(20)
        ECDH_public_key_bytes = self.ECDH_private_key_self.public_key().public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )
        signature = Agent.private_key.sign(
            str.encode("ECDHE_ECDSA_WITH_AES_256_GCM_SHA256") + \
            ECDH_public_key_bytes + \
            self.random_server + \
            Agent.public_key_bytes
        )
        data = {
            "cypher_suite":"ECDHE_ECDSA_WITH_AES_256_GCM_SHA256",
            "keyexchange_pare":ECDH_public_key_bytes,
            "random":self.random_server,
            "public_key":Agent.public_key_bytes,
            "signature":signature
        }
        loads = json.dumps(data, cls=MyEncoder)
        ESSsignal.output.emit(0, f"第一次握手信息{loads}")
        NewDataPkt = PL.DataPkt(1, 0, 1, 0,
            sid if sid else self.sid,
            nid_cus=nid if nid is not None else int(self.nid, base=16), SegID=1,
            PIDs=pids if pids else self.pids, load=b'\x02'+str.encode(loads))
        colordatapkt = NewDataPkt.packing()
        self.myStatus = 1
        self.ensureSend(ip if ip else self.ip, colordatapkt, 1)

    def sendSecondHandshake(self, nid=None, sid=None, pids=None, ip=None):
        ''' docstring: 发送第二个握手包 '''
        self.random_client = os.urandom(20)
        ECDH_public_key_bytes = self.ECDH_private_key_self.public_key().public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )
        self.calcSharedKey()
        signature = Agent.private_key.sign(
            str.encode("ECDHE_ECDSA_WITH_AES_256_GCM_SHA256") + \
            ECDH_public_key_bytes + \
            self.random_client + \
            Agent.public_key_bytes
        )
        data = {
            "cypher_suite":"ECDHE_ECDSA_WITH_AES_256_GCM_SHA256",
            "keyexchange_pare":ECDH_public_key_bytes,
            "random":self.random_client,
            "public_key":Agent.public_key_bytes,
            "signature":signature
        }
        loads = json.dumps(data, cls=MyEncoder)
        ESSsignal.output.emit(0, f"第二次握手信息{loads}")
        NewDataPkt = PL.DataPkt(1, 0, 1, 0,
            sid if sid else self.sid,
            nid_cus=nid if nid is not None else int(self.nid, base=16), SegID=2,
            PIDs=pids if pids else self.pids, load=b'\x02' + str.encode(loads))
        colordatapkt = NewDataPkt.packing()
        self.myStatus = 4
        self.ensureSend(ip if ip else self.ip, colordatapkt, 4)

    def sendThirdHandshake(self, nid=None, sid=None, pids=None, ip=None):
        ''' docstring: 发送第三个握手包 '''
        session_id = os.urandom(8)
        self.sessionId = session_id
        signature = Agent.private_key.sign(str.encode("finished") + session_id)
        data = {
            "status": "finished",
            "session_id": session_id,
            "signature": signature
        }
        loads = json.dumps(data, cls=MyEncoder)
        ESSsignal.output.emit(0, f"第三次握手信息{loads}")
        NewDataPkt = PL.DataPkt(1, 0, 1, 0,
            sid if sid else self.sid,
            nid_cus=nid if nid is not None else int(self.nid, base=16), SegID=3,
            PIDs=pids if pids else self.pids, load=b'\x02' + str.encode(loads))
        colordatapkt = NewDataPkt.packing()
        self.myStatus = 5
        self.ensureSend(ip if ip else self.ip, colordatapkt, 5)

    def sendGet(self, SegID):
        SegID_str = f"{SegID:08x}"
        tmpsid = SegID_str[0:6] + "00"*16 + '02'
        specsid2sid[self.nid + tmpsid] = self.sid
        PL.Get(self.nid + tmpsid, 2)
        # TODO: 需要重传确认

    def ensureSend(self, ip, pkt, num):
        ''' docstring: 保证可靠传输。TODO:信号存在问题，暂时不用，假定传输可靠 '''
        if self.randomnum is not None:
            tmppkt = ColorData(pkt)
            tmppkt.checksum = None
            tmppkt.Flags.C = True
            tmppkt.HMAC = self.randomnum
            tmppkt.header_length = None
            tmppkt.pkg_length = None
            pkt = tmppkt
        PL.SendIpv4(ip, pkt)
        # for i in range(3):
        #     time.sleep(RTO)
        #     if self.myStatus == num:
        #         ESSsignal.output.emit(0, f'第{num}次握手包，第{i+1}次重传')
        #         PL.SendIpv4(ip, pkt)
        #     else:
        #         break

    def calcSharedKey(self):
        ''' docstring: 计算共享密钥和会话主秘钥 '''
        remote_ECDH_public_key = ec.EllipticCurvePublicKey.from_encoded_point(
            ec.SECP384R1(),
            self.remote_ECDH_public_key_bytes
        )
        self.ECDH_shared_key = self.ECDH_private_key_self.exchange(
            ec.ECDH(),
            remote_ECDH_public_key
        )
        prekey = self.ECDH_shared_key + self.random_client + self.random_server
        # print("ECDH shared key:", self.ECDH_shared_key, "prekey:", prekey)
        self.mainKey = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.random_client + self.random_server,
            info=None
        ).derive(prekey)
        # print(self.mainKey)

def Encrypt(nid, sid, text):
    ''' docstring: 对特定服务做加密，返回值是CoLoR_data_load加密包格式的bytes串 '''
    session = sessionlist.get(f"{nid:032x}" + sid, None)
    iv = os.urandom(16)
    encryptor = Cipher(algorithms.AES(session.mainKey), modes.GCM(iv)).encryptor()
    encryptor.authenticate_additional_data(session.random_client + session.random_server)
    ciphertext = encryptor.update(text) + encryptor.finalize()
    # print(encryptor.tag, len(encryptor.tag))
    # print(session.mainKey, iv, session.random_client + session.random_server)
    return iv + encryptor.tag + ciphertext

def Decrypt(nid, sid, load):
    ''' docstring: 对特定服务做解密，返回值明文bytes串 '''
    session = sessionlist.get(f"{nid:032x}" + sid, None)
    iv = load[:16]
    tag = load[16:32]
    # print(tag, len(tag))
    # print(session.mainKey, iv, session.random_client + session.random_server)
    decryptor = Cipher(algorithms.AES(session.mainKey), modes.GCM(iv, tag)).decryptor()
    decryptor.authenticate_additional_data(session.random_client + session.random_server)
    return decryptor.update(load[32:]) + decryptor.finalize()

def newSession(nid:int, sid:str, pids:list, ip:str, flag = True, loads = b'', pkt = None, randomnum = None):
    ''' docstring: 建立一个新的会话 '''
    ESSsignal.output.emit(0, f"文件（{sid}）\n建立加密会话\n")
    nid_str = f"{nid:032x}"
    session_key = nid_str+sid
    newsession = sessionlist.get(session_key, None)
    if newsession:
        # TODO: 一次异常的重连
        return
    newsession = Session(nid_str, sid, pids, ip)
    sessionlist[session_key] = newsession
    # 开始握手
    if flag:
        newsession.pkt = pkt
        newsession.randomnum = randomnum
        newsession.sendFirstHandshake(nid=nid)
    else:
        newsession.myStatus = 2
        # 验证签名并保存参数
        data = json.loads(loads[1:])
        if data["cypher_suite"] != "ECDHE_ECDSA_WITH_AES_256_GCM_SHA256":
            ESSsignal.output.emit(1, "加密套件不支持")
            return
        newsession.remote_ECDH_public_key_bytes = bytes.fromhex(data["keyexchange_pare"])
        newsession.random_server = bytes.fromhex(data["random"])
        newsession.remote_public_key_bytes = bytes.fromhex(data["public_key"])
        if not checkNidPublickey(nid_str, newsession.remote_public_key_bytes):
            ESSsignal.output.emit(1, "公钥自证明错误，建立会话失败\n")
            return
        message = str.encode(data["cypher_suite"]) \
            + newsession.remote_ECDH_public_key_bytes \
            + newsession.random_server \
            + newsession.remote_public_key_bytes
        signature = bytes.fromhex(data["signature"])
        if not checkSignature(message, signature, newsession.remote_public_key_bytes):
            ESSsignal.output.emit(1, "公钥签名错误，建立会话失败\n")
            return
        # 发送特殊通告包
        specsid = os.urandom(3)
        newSID = specsid.hex() + '00'*16 + '02'
        while specsid2sid.get(newSID, None):
            specsid = os.urandom(3)
            newSID = specsid.hex() + '00'*16 + '02'
        specsid2sid[Agent.nid.hex() + newSID] = sid
        pkt.SegID = int(specsid.hex()+'01', 16)
        PL.AddCacheSidUnit(int(newSID,16),1,1,1,1)
        PL.SidAnn()

def checkSession(nid, sid):
    session_key = f"{nid:032x}" + sid
    return sessionlist.get(session_key, None) != None

def sessionReady(nid, sid):
    session_key = f"{nid:032x}" + sid
    session = sessionlist.get(session_key, None)
    if not session:
        return False
    return session.myStatus == 6

def gotoNextStatus(nid:int, sid:str = None, pids = None, ip = None, loads = None, SegID = 0, randomnum = None):
    ''' docstring: session状态转移函数 '''
    if not checkSession(nid, sid):
        # 特殊sid转化为真实sid
        sid_origin = sid
        sid = specsid2sid.pop(sid, None)
        if not sid:
            return
    nid_str = f"{nid:032x}"
    session_key = nid_str+sid
    session = sessionlist.get(session_key, None)
    if not session or session.myStatus == 6:
        return
    # print(session.myStatus)
    if session.myStatus == 1:
        if (SegID & 0xff) != 1:
            return
        session.myStatus = 3
        session.sendGet(SegID)
    elif session.myStatus == 2:
        session.myStatus = 4
        session.randomnum = randomnum
        session.sendSecondHandshake(nid, sid_origin, pids, ip)
    elif session.myStatus == 3:
        session.myStatus = 5
        # 验证签名并保存参数
        data = json.loads(loads[1:])
        if data["cypher_suite"] != "ECDHE_ECDSA_WITH_AES_256_GCM_SHA256":
            ESSsignal.output.emit(1, "加密套件不支持")
            return
        session.remote_ECDH_public_key_bytes = bytes.fromhex(data["keyexchange_pare"])
        session.random_client = bytes.fromhex(data["random"])
        session.remote_public_key_bytes = bytes.fromhex(data["public_key"])
        if not checkNidPublickey(nid_str, session.remote_public_key_bytes):
            ESSsignal.output.emit(1, "公钥自证明错误，建立会话失败\n")
            return
        message = str.encode(data["cypher_suite"]) \
            + session.remote_ECDH_public_key_bytes \
            + session.random_client \
            + session.remote_public_key_bytes
        signature = bytes.fromhex(data["signature"])
        if not checkSignature(message, signature, session.remote_public_key_bytes):
            ESSsignal.output.emit(1, "公钥签名错误，建立会话失败\n")
            return
        session.calcSharedKey()
        session.sendThirdHandshake()
    elif session.myStatus == 4:
        session.myStatus = 6
        data = json.loads(loads[1:])
        session.sessionId = bytes.fromhex(data['session_id'])
        message = str.encode(data['status']) + bytes.fromhex(data['session_id'])
        if not checkSignature(message, bytes.fromhex(data['signature']), session.remote_public_key_bytes):
            ESSsignal.output.emit(1, "公钥签名错误，建立会话失败\n")
            return
    elif session.myStatus == 5:
        if SegID != 3:
            return
        # 握手阶段结束，开始处理加密通信
        session.myStatus = 6
        pkthandler = CM.PktHandler(session.pkt)
        pkthandler.start()
    if session.myStatus == 6:
        ESSsignal.output.emit(0, f"与节点{session.nid}的{session.sid}已建立加密通道")


# TODO: 需要一个线程处理失败的或超时的连接
# TODO: 需要处理服务器端注册
class sessionDaemon(Thread):
    
    def __init__(self):
        pass

    def run(self):
        pass
