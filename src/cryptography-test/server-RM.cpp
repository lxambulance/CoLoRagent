#include <bits/stdc++.h>
#include <arpa/inet.h>
#include "server-openssl.c"
using namespace std;

struct keyRecord{
    string pubKey;
    string token;
};
unordered_map<string, keyRecord> nid2key;
struct getRecord{
    vector<pair<string, int> > itemList;
};
unordered_map<string, getRecord> nidsid2get;

int hex2int(char x) {
    if (isdigit(x)) return x-'0';
    return x-'a'+10;
}
bool checkNidPubkey(string nid, string pubkey){
    unsigned char key[30];
    for (int i=0;i<pubkey.size();i+=2) key[i/2] = hex2int(pubkey[i])*16+hex2int(pubkey[i+1]);
    unsigned char hkdf[20];
    OpenSSL_HKDF1(key, pubkey.size()/2, hkdf, 16);
    for (int i=0;i<nid.size();i+=2) {
        int nid_i = hex2int(nid[i])*16+hex2int(nid[i+1]);
        if (nid_i != hkdf[i/2]) return false;
    }
    return true;
}
bool checkReplay(string nidsid, int timestamp, string nonce) {
    // printf("%s %d %s\n", nidsid.c_str(), timestamp, nonce.c_str());
    getRecord R = nidsid2get[nidsid];
    while (R.itemList.size()&&timestamp - R.itemList[0].second > 1200) R.itemList.erase(R.itemList.begin());
    for (int i=0;i<R.itemList.size();i++)
    if (nonce.compare(R.itemList[i].first)==0) return false;
    R.itemList.push_back(make_pair(nonce, timestamp));
    nidsid2get[nidsid] = R;
    return true;
}
bool checkHash(int textLen, unsigned char * text, unsigned char * hash) {
    unsigned char sha256[100];
    memset(sha256, 0, sizeof(sha256));
    calcSHA256(88, text, sha256);
    writeString(strlen((char *)sha256), sha256, (char *)"calc SHA256");
    // for (int i=0;i<32;++i) printf("\\x%02x", sha256[i]); puts("");
    for (int i=0;i<32;++i) if (sha256[i] != hash[i]) return false;
    return true;
}

int main() {
    nid2key.clear();
    nidsid2get.clear();

    // 功能测试1：收到注册
    string nid = "b0cd69ef142db5a471676ad710eebf3a";
    keyRecord R;
    R.pubKey = "21f17ee1c5d8678a164f5ad525ecb3787091d204c6b52afda91f811bf7e9f03f";
    // 1.1 校验nid是否为pubkey导出
    if (!checkNidPubkey(nid, R.pubKey)) {
        printf("check nid-pubkey fail\n");
        exit(1);
    }
    // 1.2 生成40字节token，这里为了后续测试一致，采用一组固定值
    unsigned char random[50] = "\x8d\x68\x04\x60\xc6\x57\xbb\x1b\x34\xa7\xd6\xc1\xf1\xfd\xd7\x2b\x2e\xed\x9c\x94\x6f\x8b\xbc\xc9\xf6\x3b\xf3\x18\x05\x87\x85\xa3\xd1\xa2\x47\xab\xa9\x30\x6f\xbf";
    // gene_random(random, 40);
    // for (int i=0;i<40;++i) printf("\\x%02x", random[i]);
    R.token = (char *)random;
    // 1.3 记录nid-pubkey-token
    nid2key[nid] = R;
    // 1.4 加密token并返回
    unsigned char RSApubkey[500]="-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAxPNSx10AvH7KQyMC7LC5\nhh+/oZAhbZo/S1auZOjaqB9mNy4zjRqr0KZ4kvRRsBPrxdq3Cvh4gFwzJ6o4aoV+\nqTOOc2WchQnj6RxRLTx7JbTsBcXwVCzJHQA8AWXapyYPj3WOjlUqpCQvo9yvgpX3\nblZ5Lzov+Yjk3jLg01VBSsPJIAxOM9hsUz2cw9qG/OsSplPPxjWiIUP7TH5sFBdV\nn8BwFZ1FA3KIbUEYJOSi3CHuz/nw4lyVwU3Cn/VlYEo2u6+xl8/yEwMsAgY64tk0\nDEHJ/yjac15QIvGo3Dj9tygAUI83o4mwcuTmIHHKbGIuMpNEkh338getcHDHpDEv\nawIDAQAB\n-----END PUBLIC KEY-----\n";
    unsigned char encryptMsg[300];
    int ret = RSAencrypt(RSApubkey, strlen((char *)RSApubkey), random, 40, encryptMsg);
    if (ret) writeString(ret, encryptMsg, (char *)"Encrypted token");

    // 功能测试2：收到正常get
    // 2.1 提取get包参数
    int timestamp = 1630310815;
    unsigned char nonce[10] = "\xd9\xa1\xaf\x12\xd0\xe4\x85\xa1";
    unsigned char get_hash[40] = "\x8f\xef\x2c\x70\xcc\x68\x0f\x1e\x75\xc4\xb8\x10\x42\x9c\x86\x67\xf7\x7d\x0f\x91\xa2\x92\x6d\x3c\x4c\x51\x5f\x74\xd2\xde\x37\xe9";
    unsigned char text[1000];
    for (int i=0;i<nid.size();i+=2) text[i/2] = hex2int(nid[i])*16+hex2int(nid[i+1]);
    string sid = "db8ac1c259eb89d4a131b253bacfca5f319d54f2";
    for (int i=0;i<sid.size();i+=2) text[i/2+16] = hex2int(sid[i])*16+hex2int(sid[i+1]);
    // 2.2 获取token值
    memcpy(text+36, nid2key[nid].token.c_str(), 40);
    // 2.3 重放攻击检测
    if (!checkReplay(nid+sid, timestamp, (char *)nonce)) {
        printf("check replay fail\n");
        exit(1);
    }
    // 重复两遍测试效果
    // if (!checkReplay(nid+sid, timestamp, (char *)nonce)) {
    //     printf("check replay fail\n");
    //     exit(1);
    // }
    int timestamp_n = htonl(timestamp);
    memcpy(text+76, (char *)(&timestamp_n), 4);
    memcpy(text+80, nonce, 8);
    // 2.4 校验hash值
    if (!checkHash(88, text, get_hash)) {
        printf("check hash fail!\n");
        exit(1);
    }

    return 0;
}

/*
*/
