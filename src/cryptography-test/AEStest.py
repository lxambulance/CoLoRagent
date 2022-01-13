# coding = utf-8


import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


mainKey = b'\xd2N\xd7\xbb{\xb1~H\xff\xf8\x11\x13M>{\x02\xfc\xf3r\x1eF\xfbA\x8e\xac\xfa\xf0Z\xd3l\x16\xd4'
authenticate_code = b'lxambulance'


def Encrypt(text):
    iv = os.urandom(16)
    encryptor = Cipher(algorithms.AES(mainKey), modes.GCM(iv)).encryptor()
    encryptor.authenticate_additional_data(authenticate_code)
    ciphertext = encryptor.update(text) + encryptor.finalize()
    return iv + encryptor.tag + ciphertext

def Decrypt(load):
    iv = load[:16]
    tag = load[16:32]
    decryptor = Cipher(algorithms.AES(mainKey), modes.GCM(iv, tag)).decryptor()
    decryptor.authenticate_additional_data(authenticate_code)
    return decryptor.update(load[32:]) + decryptor.finalize()


if __name__ == '__main__':
    text = b'Hello world'
    print("text:", text)
    ciphertext = Encrypt(text)
    print("ciphertext:", ciphertext)
    resumetext = Decrypt(ciphertext)
    print("resumetext:", resumetext)
