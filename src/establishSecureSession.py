# coding=utf-8

import json
import hashlib
import ProxyLib as PL
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

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
        self.nid = data['myNID']
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
        data['public_key'] = self.public_key
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
        tmpnid = hashlib.sha256()
        tmpnid.update(self.public_key_bytes)
        self.nid = HKDF(
            algorithm=hashes.SHA256(),
            length=16,
            salt=None,
            info=None
        ).derive(tmpnid.digest())
        self.rsa_private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        rsa_public_key = self.rsa_private_key.public_key()
        self.rsa_public_key_bytes = rsa_public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        # print("public key:", self.public_key_bytes.hex())
        # print("nid:", self.nid.hex())
        # print("rsa public key:", self.rsa_public_key_bytes.hex())

Agent = keys()
Session_list = {}

class Session():
    ''' docstring: 会话类，主要的存储对象 '''
    def __init__(self, nid, sid):
        self.nid = nid
        self.sid = sid

def annSpecServer():
    ''' docstring: 注册一个特殊类型服务，用于反向传输数据 '''
    pass

def newSession(nid:int, sid:str, pids:list):
    ''' docstring: 建立一个新的会话 '''
    nid_str = f"{nid:032x}"
    session_key = nid_str+sid
    newsession = Session_list.get(session_key, None)
    if newsession:
        # TODO: 一次异常的重连
        return
    newsession = Session(nid_str, sid)
    sendFirstHandshake(nid, sid, pids)

def sendFirstHandshake(nid, sid, pids):
    ''' docstring: 发送第一个握手包 '''
    loads = ""
    NewDataPkt = PL.DataPkt(1, 0, 1, 0, sid, nid_cus=nid, SegID=0, PIDs=pids, load=loads)
    

def sendSecondHandshake():
    ''' docstring: 发送第二个握手包 '''
    pass

def sendThirdHandshake():
    ''' docstring: 发送第三个握手包 '''
    pass
