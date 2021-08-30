# coding = utf-8


import hashlib

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key


def generateRSAkey():
    # generate RSA private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()
    
    # RSA key serialize
    private_key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    print("private key:", private_key_bytes)
    public_key_bytes = public_key.public_bytes(
       encoding=serialization.Encoding.PEM,
       format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    print("public key :", public_key_bytes)

    # RSA key load
    private_key = load_pem_private_key(private_key_bytes, None)
    public_key = load_pem_public_key(public_key_bytes)
    print("load key: ", type(private_key), type(public_key))
    return private_key, public_key


if __name__ == '__main__':
    # test: RSA encryption & decryption
    private_key, public_key = generateRSAkey()
    message = b"lxambulance"
    padding_OAEP = padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA1()),
        algorithm=hashes.SHA1(),
        label=None
    )
    ciphertext = public_key.encrypt(message, padding_OAEP)
    plaintext = private_key.decrypt(ciphertext, padding_OAEP)
    print("message:   ", message)
    print("ciphertext:", ciphertext.hex())
    print("plaintext: ", plaintext)
    print("result:    ", message == plaintext)

    # test: load private key & decrypt
    s_private_key = b'-----BEGIN RSA PRIVATE KEY-----\nMIIEpQIBAAKCAQEAxPNSx10AvH7KQyMC7LC5hh+/oZAhbZo/S1auZOjaqB9mNy4z\njRqr0KZ4kvRRsBPrxdq3Cvh4gFwzJ6o4aoV+qTOOc2WchQnj6RxRLTx7JbTsBcXw\nVCzJHQA8AWXapyYPj3WOjlUqpCQvo9yvgpX3blZ5Lzov+Yjk3jLg01VBSsPJIAxO\nM9hsUz2cw9qG/OsSplPPxjWiIUP7TH5sFBdVn8BwFZ1FA3KIbUEYJOSi3CHuz/nw\n4lyVwU3Cn/VlYEo2u6+xl8/yEwMsAgY64tk0DEHJ/yjac15QIvGo3Dj9tygAUI83\no4mwcuTmIHHKbGIuMpNEkh338getcHDHpDEvawIDAQABAoIBAQCLhwpk/MlRwM1Q\nJNSklErK72EWd4KHIFio6f7gtGp74srKWuvgkj2YsucGzRm2EVbeM6Wrmv3bifYf\nqqMPLAXgnwrTS/BH/Aq/kfUchBWGUBdJu8IYECZmak0YfG0cL4Wkj5bv1PxBjvVF\nNEoOzGmffJmb0LA+KzJhDFBkx6ha6vrsFVuThxzfduu1PNPel8JdhK9kawEQcZbk\nVnFCME0SRP5PqgiG8lp6rKYrNOOjuy+8XHgadxP+tPYX7AKkjcW8nQ4sjO7TfrLR\ngzX5xzsmoo3QPqBTdncZlvWp0kYBFcSynWo9Dct2vWH7mWipnKFFglqnTLjPp2V4\npczo3HNBAoGBAP1twdH/NmMpEfEeFPI6UY9vS21JNl1BChcV0O8tW4ZI0cDOMrhh\noAQhi2x36chcCN3n0Sw+Qf4ziYmdzPKyzXC2WOorze7mL2o7+RRYgiS9lngNiYWv\nmCvO7qtGGwKsR6S94c/ILjl4nL7rcjC0fSEQN6qRzlvb38Ec7OQOYc+hAoGBAMby\n31wJ61bpXNHL73JeSKGEayjKlcgvN/tZkTAUYoBlOrHVcEstjyFd+Hts3uTXQWQw\nkh+H4h3/cdTGFxOOXBd2hv4nbTtJYVajsdsfbSumIXNgBc6vb0vpUcUxR/rsumyK\n1KMcbObr2mQ9RFhTGddNYOZA3rP/cB6+f3PtXJOLAoGBALN7Hf9pbc1AcvJ+yXrb\njpO00Ihvh074FvtOehBJ4T3zKIoR/p3Slg8W6rVBH5LEi4sM+HkLBpXPTiLmXRWt\nSA4BNmtx5oDBCOeF3dto65K1qnEPtUu2lmDARwuJtOtps7uatuf+763IG8qi2NZh\nnRTjdWkZpjosOAV+RM8m2GLBAoGAaSWBsTY44GVTvjnnYm28O0kuDZAMW5HBJ6Gt\n31hWuv9FZymkQMdiZ0MwCaN/pjiyAc6929ZIRox0T/0lwxsxRuFI9VhHHddpj43S\neToBy9jwwvaT+ymzS86TfgHOxiqJWMaDHXXvhJhQgzvyPDAnbyghN3A/g6hUTJtn\n5xAjJoMCgYEAvOezr3QVhtTkZpXr4O8snKZsDiXRAHaP8YJb7uO2Q9sNkd6paBoB\n3z3Ebpb4EkyY756mTwL2H26B9EnPq3RfzoO4K9bqbrc3DVzUaCxlTbfAqudf9oVd\nDc898PJmnad/hr64sp5kpADe/kKrT3h4RAAKWa1QvzqNOjQTRqEtBQg=\n-----END RSA PRIVATE KEY-----\n'
    s_public_key = b'-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAxPNSx10AvH7KQyMC7LC5\nhh+/oZAhbZo/S1auZOjaqB9mNy4zjRqr0KZ4kvRRsBPrxdq3Cvh4gFwzJ6o4aoV+\nqTOOc2WchQnj6RxRLTx7JbTsBcXwVCzJHQA8AWXapyYPj3WOjlUqpCQvo9yvgpX3\nblZ5Lzov+Yjk3jLg01VBSsPJIAxOM9hsUz2cw9qG/OsSplPPxjWiIUP7TH5sFBdV\nn8BwFZ1FA3KIbUEYJOSi3CHuz/nw4lyVwU3Cn/VlYEo2u6+xl8/yEwMsAgY64tk0\nDEHJ/yjac15QIvGo3Dj9tygAUI83o4mwcuTmIHHKbGIuMpNEkh338getcHDHpDEv\nawIDAQAB\n-----END PUBLIC KEY-----\n'
    private_key = load_pem_private_key(s_private_key, None)
    ciphertext_hex = "0a45a2623b39f1a002d5437ede2660b4cf106956497c743f12b31ed12c1d0383d0c2d930c78a647c0b72bc4e7e5e06aa704ce3f430cd45ad7ebc52f78ece5f7c4a34642b928af243e4d299a293641c7709ee1cc9c4df229213f0cbaa03a302000ceeac72ed01be2e1f33c74f8873b6178ea5dca79e6412ad83517cb5397c7223dbb615d84279cfbffb38f2e428f748f56aee9655f4d0fb67e2d3e888754aef4793b3431175870411d7a0cf4d99d05d30c079b799b10470be3179059e8c7d4f47ef356429c4595681046cd095d4b18d44389499aafa8e0d57227ac66ee9fdfecd0b3c43982db706e13af3ba7117f067cf542cdac1bf1ebc902555a6cfac4303f7"
    ciphertext = bytes.fromhex(ciphertext_hex)
    message = private_key.decrypt(ciphertext, padding_OAEP)
    print(message)

    # test: calculate SHA256
    hash_SHA256 = hashlib.sha256()
    hash_SHA256.update(message)
    print(hash_SHA256.hexdigest())
