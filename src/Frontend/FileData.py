# coding=utf-8
""" docstring: 数据暂存，支撑数据表示 """


from enum import IntEnum


FILEDATA_SIZE = 7
REG_OR_DOW_COMPLETED = 100
UNREG_COMPLETED = 0


class FileDataEnum(IntEnum):
    FILENAME = 0
    FILEPATH = 1
    FILEHASH = 2
    ISREG = 3
    ISDOW = 4
    SECURITYLEVEL = 5
    WHITELIST = 6


class FileData:
    """ docstring: 文件数据类 """

    def __init__(self, *, initData=None, NID=None):
        self.__data = initData or []
        self.NID = NID

    def getData(self, row, column=0):
        """ docstring: 获取数据 """
        if row < 0 or row >= self.rowCount() or column < 0 or column >= len(self.__data[row]):
            return None
        return self.__data[row][column]

    def setData(self, row, column=0, newData=None):
        """ docstring: 写入数据 """
        if row < 0 or column < 0 or row >= self.rowCount() or column >= self.columnCount():
            return
        self.__data[row][column] = newData

    def getItem(self, row):
        """ docstring: 获取整个条目 """
        return self.__data[row]

    def setItem(self, row, item):
        """ docstring: 存入整个条目 """
        if row < self.rowCount():
            self.__data[row] = item
        else:
            self.__data.append(item)

    def addItem(self, *, filename, filepath, isReg=0, have=1, **kwargs):
        """ docstring: 添加文件时的处理 """
        filehash = kwargs.get('filehash', None)
        # TODO: 处理file addtion text
        item = [filename, filepath, filehash, isReg * 100, have * 100, "0", ""]
        self.__data.append(item)

    def removeItem(self, row):
        if row < self.rowCount():
            del self.__data[row]

    def rowCount(self):
        return len(self.__data)

    def columnCount(self):
        return FILEDATA_SIZE

    def save(self):
        return self.__data


if __name__ == '__main__':
    import os
    __BASE_DIR = os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))).replace('\\', '/')
    HOME_DIR = __BASE_DIR + '/.tmp'
    DATA_PATH = __BASE_DIR + '/data.json'
    a = FileData()
    print(a.__doc__, a.save.__doc__)
    print(DATA_PATH)
    a.load()
