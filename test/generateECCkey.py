# coding=utf-8


import json
import hashlib
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.hex()
        return json.JSONEncoder.default(self, obj)


if __name__ == '__main__':
    data = {}

    private_key = Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    print("私钥1", private_bytes, len(private_bytes))
    print("公钥1", public_bytes, len(public_bytes))
    
    nid = hashlib.sha256()
    nid.update(public_bytes)
    data['client']={
        "private":private_bytes,
        "public":public_bytes,
        "nid": nid.hexdigest()
    }

    private_key = Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    print("私钥2", private_bytes, len(private_bytes))
    print("公钥2", public_bytes, len(public_bytes))

    nid = hashlib.sha256()
    nid.update(public_bytes)
    data['server']={
        "private":private_bytes,
        "public":public_bytes,
        "nid": nid.hexdigest()
    }

    print(data)
    print(json.dumps(data, cls=MyEncoder))

    with open("./test/testKey.db","w") as f:
        json.dump(data, f, cls=MyEncoder)
