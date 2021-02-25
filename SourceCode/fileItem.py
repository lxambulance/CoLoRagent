# coding=utf-8
'''
docstring: 文件条目模块
'''

FILE_ITEM_OPTION_LENGTH = 4

class FileItem:
    '''docstring: 文件条目类'''
    __option = [""] * FILE_ITEM_OPTION_LENGTH
    '''
    option[0]表示文件名
    option[1]表示文件路径
    option[2]表示是否注册
    option[3]表示是否本地缓存
    '''

    def __init__(self, name, filepath = "...", reg = "否", cache = "否"):
        self.__option[0] = name
        self.__option[1] = filepath
        self.__option[2] = reg
        self.__option[3] = cache

    def getOption(self, pos):
        '''获取option字段值'''
        if pos >= FILE_ITEM_OPTION_LENGTH:
            return None
        return self.__option[pos]

    def setOption(self, pos, val):
        '''修改option字段值'''
        if pos >= FILE_ITEM_OPTION_LENGTH:
            raise Exception("Invalid pos")
        self.__option[pos] = val

if __name__ == '__main__':
    item = FileItem("bilibili/AV170001")
    print("option[3]", item.getOption(3))
    print("option[4]", item.getOption(4))
    item.setOption(3, "否")
    item.setOption(4, "0")
