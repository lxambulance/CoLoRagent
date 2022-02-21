# coding=utf-8


import json
import hashlib
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.hex()
        return json.JSONEncoder.default(self, obj)


count = 0


def keyGenerate():
    global count
    count += 1
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
    tmpnid = hashlib.sha256()
    tmpnid.update(public_bytes)
    nid = HKDF(
        algorithm=hashes.SHA256(),
        length=16,
        salt=None,
        info=None
    ).derive(tmpnid.digest())
    print("私钥"+str(count), private_bytes, len(private_bytes))
    print("公钥"+str(count), public_bytes, len(public_bytes))
    print("nid", nid.hex())
    return private_key, private_bytes, public_key, public_bytes, nid.hex()


def publicKeyCheck(nid_hex, publick_key_hex):
    tmpnid = hashlib.sha256()
    public_bytes = bytes.fromhex(publick_key_hex)
    tmpnid.update(public_bytes)


def loadKey(data):
    private_bytes = data['private']
    private_key = Ed25519PrivateKey.from_private_bytes(
        bytes.fromhex(data['private']))
    public_bytes = data['public']
    public_key = Ed25519PublicKey.from_public_bytes(
        bytes.fromhex(data['public']))
    nid = data['nid']
    print('私钥', private_bytes)
    print('公钥', public_bytes)
    print('nid ', nid)
    return private_key, public_key, nid


if __name__ == '__main__':
    data = {}

    private_key, private_bytes, public_key, public_bytes, nid = keyGenerate()

    data['client'] = {
        "private": private_bytes,
        "public": public_bytes,
        "nid": nid
    }

    private_key, private_bytes, public_key, public_bytes, nid = keyGenerate()

    data['server'] = {
        "private": private_bytes,
        "public": public_bytes,
        "nid": nid
    }

    print(json.dumps(data, cls=MyEncoder))

    with open("./data-ECCKey.json", "w") as f:
        json.dump(data, f, cls=MyEncoder)
