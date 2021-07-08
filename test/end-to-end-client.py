# coding=utf-8


import json
from generateECCkey import loadKey, MyEncoder


if __name__=='__main__':
    data = {}
    with open("./test/testKey.db", "r") as f:
        data = json.load(f)
    # 载入公私钥，后续做验证
    private_key, public_key, nid = loadKey(data['client'])
    public_key_bytes = bytes.fromhex(data['client']['public'])
    private_key_remote, public_key_remote, nid_remote = loadKey(data['server'])
    public_key_remote_bytes = bytes.fromhex(data['server']['public'])


    from scapy.all import *
    from CoLoR_Get import CoLoR_Get
    g = CoLoR_Get()
    g.N_sid = bytes.fromhex(nid_remote)
    g.L_sid = b'\xff'*20
    g.nid = bytes.fromhex(nid)
    pkt = IP(dst="192.168.56.101", proto=150)/g
    pkt.show()
    send(pkt, verbose=0) # 发起Get


    from CoLoR_Data import CoLoR_Data
    pkts = sniff(filter="ip src 192.168.56.101", iface="VirtualBox Host-Only Network", count=1) # 接收Data
    d1 = CoLoR_Data(pkts[0].load)
    d1.show()
    data = json.loads(d1.load.decode())
    random_server = bytes.fromhex(data['random'])
    signature_str = str.encode("ECDHE_ECDSA_WITH_AES_256_GCM_SHA256") + \
        bytes.fromhex(data['keyexchange_pare']) + \
        random_server + \
        bytes.fromhex(data['public_key'])
    if (data['cypher_suite'] != "ECDHE_ECDSA_WITH_AES_256_GCM_SHA256"
     or bytes.fromhex(data['public_key']) != public_key_remote_bytes
     or public_key_remote.verify(bytes.fromhex(data['signature']), signature_str)):
        print('加密套件不支持、公钥有误或签名错误')
        exit(1)
    import os
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    ECDH_private_key = ec.generate_private_key(ec.SECP384R1())
    ECDH_peer_public_key = ec.EllipticCurvePublicKey.from_encoded_point(
        ec.SECP384R1(),
        bytes.fromhex(data['keyexchange_pare'])
    )
    ECDH_shared_key = ECDH_private_key.exchange(
        ec.ECDH(),
        ECDH_peer_public_key
    )


    random_client = os.urandom(20)
    ECDH_public_key_bytes = ECDH_private_key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    signature = private_key.sign(
        str.encode("ECDHE_ECDSA_WITH_AES_256_GCM_SHA256") + \
        ECDH_public_key_bytes + \
        random_client + \
        public_key_bytes
    )
    data = {
        "cypher_suite":"ECDHE_ECDSA_WITH_AES_256_GCM_SHA256",
        "keyexchange_pare":ECDH_public_key_bytes,
        "random":random_client,
        "public_key":public_key_bytes,
        "signature":signature
    }
    data_json = json.dumps(data, cls=MyEncoder)
    print("第二次握手信息", data_json)
    from CoLoR_Data import CoLoR_Data
    d2 = CoLoR_Data()
    d2.Flags.B = True
    d2.N_sid = d1.N_sid
    d2.L_sid = d1.L_sid
    d2.nid_cus = d1.nid_cus
    d2.PIDs = d1.PIDs[1:][::-1]
    d2.show()
    pkt = IP(dst="192.168.56.101", proto=150)/d2/data_json
    pkt.show()
    send(pkt, verbose=0) # 发送第二个data，客户端发起第二次握手，交换密钥
    
    
    pkts = sniff(filter="ip src 192.168.56.101", iface="VirtualBox Host-Only Network", count=1) # 接收Data
    d3 = CoLoR_Data(pkts[0].load)
    d3.show()
    data = json.loads(d3.load.decode())
    signature_str = str.encode(data['status']) + bytes.fromhex(data['session_id'])
    if (public_key_remote.verify(bytes.fromhex(data['signature']), signature_str)):
        print('签名错误')
        exit(1)
