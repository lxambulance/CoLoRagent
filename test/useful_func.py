# coding=utf-8


def CalcChecksum(tar):
    """ docstring: 校验和计算 tar: bytes字符串 """
    length = len(tar)
    pointer = 0
    sum = 0
    while (length - pointer > 1):
        # 两字节相加
        temp = tar[pointer] << 8
        temp += tar[pointer+1]
        pointer += 2
        sum += temp
    if (length - pointer > 0):
        sum += tar[pointer] << 8
    sum = (sum >> 16) + (sum & 0xffff)
    sum = (sum >> 16) + (sum & 0xffff)  # 防止上一步相加后结果大于16位
    return (sum ^ 0xffff)  # 按位取反后返回


def int2Bytes(data, length):
    """ docstring: 将int类型转成bytes类型（大端存储） data: 目标数字，length: 目标字节数 """
    return data.to_bytes(length, byteorder='big')


def int2BytesLE(data, length):
    """ docstring: 将int类型转成bytes类型（小端存储） data：目标数字，length：目标字节数 """
    return data.to_bytes(length, byteorder='little')

