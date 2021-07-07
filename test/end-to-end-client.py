# coding=utf-8


import json
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


if __name__=='__main__':
    data = {}
    with open("./test/testKey.db", "r") as f:
        data = json.load(f)
    
    private_key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(data['client']['private']))
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(data['client']['public']))
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    print('client私钥', private_bytes)
    print('client公钥', public_bytes)
