#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdint.h>
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


/* 生成指定比特数的大数*, 最后将这个大数以字符串保存*/
void gene_random(char *random, int bits)
{
    BIGNUM *rnd = BN_new();
    BN_rand(rnd, bits, 0, 0);
    char *show = BN_bn2hex(rnd);
    strcpy(random, show);
    OPENSSL_free(show);
    BN_free(rnd);
}


/* 计算SHA256值 */
void calcSHA256(unsigned char *buff,unsigned char *md)
{
    int len;
    len = strlen(buff);
    SHA256_CTX c;
    SHA256_Init(&c);
    SHA256_Update(&c,buff,len);
    SHA256_Final(md,&c);
}


/* 以hex形式输出字符串 */
void writeString(size_t len, unsigned char *s, char * info)
{
    printf("%s\nlength:%u\ncontent:",info,(unsigned int)len);
    int i;
    for (i=0;i<len;++i) {
        printf("%02x", s[i]);
    }
    printf("\n\n");
}


/* 计算HKDF */
int OpenSSL_HKDF1(unsigned char *key, size_t key_len, unsigned char *out, size_t out_len)
{
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


/* 用RSA做加密 */
size_t RSAencrypt(unsigned char *input, size_t input_len, unsigned char *message, size_t message_len, unsigned char *result)
{
    BIO *bio;
    RSA *pubkey = NULL;
    do{
        bio = BIO_new_mem_buf((void *)input, input_len);
        if (bio == NULL)
        {
            printf("BIO_new_mem_buf pubkey error\n");
            break;
        }
        pubkey = PEM_read_bio_RSAPublicKey(bio, &pubkey, NULL, NULL);
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
    int ret = RSA_public_encrypt(message_len, message, encryptMsg, pubkey, RSA_PKCS1_PADDING);
    if (ret == 0)
    {
        printf("RSA_public_encrypt error\n");
        return 0;
    }
    memcpy(result, encryptMsg, ret);
    return ret;
}


int main(){
    // 测试RSA加密
    unsigned char test[20]="hello world";
    unsigned char input[500]="-----BEGIN RSA PUBLIC KEY-----\nMIIBCgKCAQEAtarHXdyugZ+8j6yqXn8X4yyaujOrcdREaJBBzoqLU3Qvk6LJEEER\nMFg9yckxqELb7n5mrJJz+zG9VA4iYHY0+ik422bvxen7z8ZUt3RI167AMddjRaD/\nwc3Ti4fv+JFZCF0J+/4igukjjYaTEWsSMeVKQMyNTj6FC1i5N/5aWiBNCf0ym5+/\nt/3vWnkSuaZXtmwrni8fmdViKEPtb9bxsBO6zux85IP589EyXFLEsXolZrI/VGCz\nQkaYeDdoFF1+zzcRPDipzOlLItdAJoflPeh9lIemRECG3F6HxBr1vrDyqlUFbeC4\n+WK41guosHvWCIOAE1icxMWZEveEs9dutwIDAQAB\n-----END RSA PUBLIC KEY-----\n";
    unsigned char encryptMsg[100];
    int ret = RSAencrypt(input, strlen(input), test, strlen(test), encryptMsg);
    if (ret) writeString(ret, encryptMsg, "RSA ciphertext");
    // 测试HKDF
    unsigned char hkdf[30];
    if (OpenSSL_HKDF1(test, 11, hkdf, 20)) writeString(20, hkdf, "HKDF result");
    // 测试随机数生成
    unsigned char random[100];
    gene_random(random, 80);
    writeString(80, random, "random");
    return 0;
}
