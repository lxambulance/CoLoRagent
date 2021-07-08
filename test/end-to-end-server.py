# coding=utf-8


import json
from generateECCkey import loadKey, MyEncoder


if __name__=='__main__':
    data = {}
    with open("./test/testKey.db", "r") as f:
        data = json.load(f)
    # 载入公私钥，后续做验证
    private_key, public_key, nid = loadKey(data['server'])
    public_key_bytes = bytes.fromhex(data['server']['public'])
    private_key_remote, public_key_remote, nid_remote = loadKey(data['client'])
    public_key_remote_bytes = bytes.fromhex(data['client']['public'])


    from scapy.all import *
    from CoLoR_Get import CoLoR_Get
    pkts = sniff(filter="ip src 192.168.56.1", count=1) # 接收Get
    g = CoLoR_Get(pkts[0].load)
    g.show()
    if (g.N_sid.hex() != nid or g.L_sid != b'\xff'*20):
        print("SID不匹配")
        exit(1)


    from scapy.all import *
    from CoLoR_Data import CoLoR_Data
    d1 = CoLoR_Data()
    d1.Flags.R = True
    d1.N_sid = g.N_sid
    d1.L_sid = g.L_sid
    d1.nid_cus = g.nid
    d1.nid_pro = bytes.fromhex(nid)
    d1.show()
    import os
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    random_server = os.urandom(20)
    ECDH_private_key = ec.generate_private_key(ec.SECP384R1())
    ECDH_public_key_bytes = ECDH_private_key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    signature = private_key.sign(
        str.encode("ECDHE_ECDSA_WITH_AES_256_GCM_SHA256") + \
        ECDH_public_key_bytes + \
        random_server + \
        public_key_bytes
    )
    data = {
        "cypher_suite":"ECDHE_ECDSA_WITH_AES_256_GCM_SHA256",
        "keyexchange_pare":ECDH_public_key_bytes,
        "random":random_server,
        "public_key":public_key_bytes,
        "signature":signature
    }
    data_json = json.dumps(data, cls=MyEncoder)
    print("第一次握手信息", data_json)
    pkt = IP(dst = "192.168.56.1", proto=150)/d1/data_json
    pkt.show()
    send(pkt, verbose=0) # 发送第一个data，服务器发起第一次握手，请求建立安全连接


    pkts = sniff(filter="ip src 192.168.56.1", count=1) # 接收Data
    d2 = CoLoR_Data(pkts[0].load)
    data = json.loads(d2.load.decode())
    random_client = bytes.fromhex(data['random'])
    signature_str = str.encode("ECDHE_ECDSA_WITH_AES_256_GCM_SHA256") + \
        bytes.fromhex(data['keyexchange_pare']) + \
        random_client + \
        bytes.fromhex(data['public_key'])
    if (data['cypher_suite'] != "ECDHE_ECDSA_WITH_AES_256_GCM_SHA256"
     or bytes.fromhex(data['public_key']) != public_key_remote_bytes
     or public_key_remote.verify(bytes.fromhex(data['signature']), signature_str)):
        print('加密套件不支持、公钥有误或签名错误')
        exit(1)
    ECDH_peer_public_key = ec.EllipticCurvePublicKey.from_encoded_point(
        ec.SECP384R1(),
        bytes.fromhex(data['keyexchange_pare'])
    )
    ECDH_shared_key = ECDH_private_key.exchange(
        ec.ECDH(),
        ECDH_peer_public_key
    )


    session_id = os.urandom(8)
    signature = private_key.sign(str.encode("finished") + session_id)
    data = {
        "status": "finished",
        "session_id": session_id,
        "signature": signature
    }
    data_json = json.dumps(data, cls=MyEncoder)
    print("第三次握手信息", data_json)
    pkt = IP(dst = "192.168.56.1", proto=150)/d1/data_json
    pkt.show()
    send(pkt, verbose=0) # 发送第三个data，服务器发起第三次握手，连接建立，握手结束
