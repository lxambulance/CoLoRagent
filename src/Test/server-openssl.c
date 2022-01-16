#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <openssl/bn.h>
#include <openssl/sha.h>
#include <openssl/crypto.h>
#include <openssl/evp.h>
#include <openssl/objects.h>
#include <openssl/hmac.h>
#include <openssl/rand.h>
#include <openssl/rsa.h>
#include <openssl/pem.h>
#include <openssl/kdf.h>


#ifdef __cplusplus
extern "C" {
#endif

/* 生成指定比特数的大数*, 最后将这个大数以字符串保存, bits指二进制位数，使用时字节数需要乘8 */
void gene_random(unsigned char *random, int Bytes);
/* 计算SHA256值 */
void calcSHA256(int len,unsigned char *buff,unsigned char *md);
/* 以hex string形式输出字符串 */
void writeString(size_t len, unsigned char *s, char * info);
/* 计算HKDF */
int OpenSSL_HKDF1(unsigned char *key, size_t key_len, unsigned char *out, size_t out_len);
/* 用RSA做加密 */
size_t RSAencrypt(unsigned char *input, size_t input_len, unsigned char *message, size_t message_len, unsigned char *result);

#ifdef __cplusplus
}
#endif


void gene_random(unsigned char *random, int Bytes) {
    int bits = Bytes*8;
    BIGNUM *rnd = BN_new();
    BN_rand(rnd, bits, 0, 0);
    BN_bn2bin(rnd, random);
    BN_free(rnd);
}

void calcSHA256(int len,unsigned char *buff,unsigned char *md) {
    SHA256_CTX c;
    SHA256_Init(&c);
    SHA256_Update(&c, buff, len);
    SHA256_Final(md, &c);
}

void writeString(size_t len, unsigned char *s, char * info) {
    printf("%s\nlength:%u\ncontent:",info,(unsigned int)len);
    int i;
    for (i=0;i<len;++i) {
        printf("%02x", s[i]);
    }
    printf("\n\n");
}

int OpenSSL_HKDF1(unsigned char *key, size_t key_len, unsigned char *out, size_t out_len) {
    EVP_PKEY_CTX *pctx = EVP_PKEY_CTX_new_id(EVP_PKEY_HKDF, NULL);
    
    size_t ret = EVP_PKEY_derive_init(pctx) <= 0
        || EVP_PKEY_CTX_hkdf_mode(pctx, EVP_PKEY_HKDEF_MODE_EXTRACT_AND_EXPAND) <= 0
        || EVP_PKEY_CTX_set_hkdf_md(pctx, EVP_sha256()) <= 0
        || EVP_PKEY_CTX_set1_hkdf_key(pctx, key, key_len) <= 0
        || EVP_PKEY_CTX_set1_hkdf_salt(pctx, NULL, 0) <= 0
        || EVP_PKEY_CTX_add1_hkdf_info(pctx, NULL, 0) <= 0
        || EVP_PKEY_derive(pctx, out, &out_len) <= 0;

    EVP_PKEY_CTX_free(pctx);
    
    return ret == 0;
}

size_t RSAencrypt(unsigned char *input, size_t input_len, unsigned char *message, size_t message_len, unsigned char *result) {
    BIO *bio;
    RSA *pubkey = NULL;
    do{
        bio = BIO_new_mem_buf((void *)input, input_len);
        if (bio == NULL)
        {
            printf("BIO_new_mem_buf pubkey error\n");
            break;
        }
        pubkey = PEM_read_bio_RSA_PUBKEY(bio, &pubkey, NULL, NULL);
        if (pubkey == NULL)
        {
            printf("PEM_read_bio_RSA_PUBKEY error\n");
            break;
        }
    }while(0);
    BIO_free_all(bio);
    if (pubkey == NULL) return 0;

    int encrypt_max_len = RSA_size(pubkey);
    if (encrypt_max_len < message_len)
    {
        printf("message length too long\n");
        return 0;
    }
    unsigned char *encryptMsg = (unsigned char *)malloc(encrypt_max_len);
    int ret = RSA_public_encrypt(message_len, message, encryptMsg, pubkey, RSA_PKCS1_OAEP_PADDING);
    if (ret == 0)
    {
        printf("RSA_public_encrypt error\n");
        return 0;
    }
    memcpy(result, encryptMsg, ret);
    return ret;
}


#ifndef __cplusplus

int main(){
    // openssl version: 1.1.1f
    // gcc version: 9.3.0
    // system: ubuntu 20.04

    // 测试：HKDF导出函数
    unsigned char test[20]="hello world";
    unsigned char hkdf[30];
    if (OpenSSL_HKDF1(test, 11, hkdf, 20)) writeString(20, hkdf, "HKDF result");
    
    // 测试：随机数生成
    unsigned char random[100];
    int random_len = 40;
    gene_random(random, random_len);
    writeString(random_len, random, "random");
    random[random_len]=0;
    
    // 测试：RSA加密
    unsigned char input[500]="-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAxPNSx10AvH7KQyMC7LC5\nhh+/oZAhbZo/S1auZOjaqB9mNy4zjRqr0KZ4kvRRsBPrxdq3Cvh4gFwzJ6o4aoV+\nqTOOc2WchQnj6RxRLTx7JbTsBcXwVCzJHQA8AWXapyYPj3WOjlUqpCQvo9yvgpX3\nblZ5Lzov+Yjk3jLg01VBSsPJIAxOM9hsUz2cw9qG/OsSplPPxjWiIUP7TH5sFBdV\nn8BwFZ1FA3KIbUEYJOSi3CHuz/nw4lyVwU3Cn/VlYEo2u6+xl8/yEwMsAgY64tk0\nDEHJ/yjac15QIvGo3Dj9tygAUI83o4mwcuTmIHHKbGIuMpNEkh338getcHDHpDEv\nawIDAQAB\n-----END PUBLIC KEY-----\n";
    unsigned char encryptMsg[300];
    int ret = RSAencrypt(input, strlen(input), random, random_len, encryptMsg);
    if (ret) writeString(ret, encryptMsg, "RSA ciphertext");

    // 测试：计算SHA256
    unsigned char sha256[100];
    memset(sha256, 0, sizeof(sha256));
    calcSHA256(11, test, sha256);
    writeString(strlen(sha256), sha256, "SHA256");

    // 测试：获取系统时间
    int x = time(NULL);
    printf("%d\n", x);

    return 0;
}

#endif
