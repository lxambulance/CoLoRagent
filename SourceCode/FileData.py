# coding=utf-8
''' docstring: data store '''

# 添加文件路径../
import os
import sys
__BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
sys.path.append(__BASE_DIR)

import json

DATA_PATH = __BASE_DIR + '/data.db'

class FileData:
    ''' docstring: class FileData '''

    def __init__(self, initData = None):
        self.__data = initData or []

    def getData(self, row, column = 0):
        ''' docstring: 获取数据 '''
        return self.__data[row][column]

    def setData(self, row, column = 0, newData = None):
        ''' docstring: 写入数据 '''
        self.__data[row][column] = newData

    def getItem(self, row):
        ''' docstring: 获取整个条目 '''
        return self.__data[row]

    def setItem(self, row, item):
        ''' docstring: 存入整个条目 '''
        if row < self.rowCount():
            self.__data[row] = item
        else:
            self.__data.append(item)

    def setItem(self, *, filename, filepath, isReg = 0, have = 1, **kwargs):
        ''' docstring: 添加文件时的处理 '''
        filehash = kwargs.get('filehash', None)
        item = [filename, filepath, filehash, isReg, have * 100]
        self.__data.append(item)
        # todo: 处理file addtion text

    def removeItem(self, row):
        if row < self.rowCount():
            del self.__data[row]

    def rowCount(self):
        return len(self.__data)

    def columnCount(self):
        return len(self.__data[0])

    def load(self, Path = None, option = 0):
        ''' docstring: 从数据路径加载数据 '''
        last = self.rowCount()
        if Path == None:
            Path = DATA_PATH
        pos = Path.find('db')
        if pos == -1:
            return
        with open(Path, 'r') as f:
            if (self.__data == None):
                self.__data = json.load(f)
            else:
                items = json.load(f)
                for item in items:
                    self.__data.append(item)
        if (option&1) == 1:
            for i in range(last, self.rowCount()):
                self.__data[i][3] = 100
                self.__data[i][4] = 0

    def save(self, Path = None):
        ''' docstring: 将数据保存到数据路径中 '''
        if Path == None:
            Path = DATA_PATH
        with open(Path, 'w') as f:
            json.dump(self.__data, f)

if __name__ == '__main__':
    a = FileData()
    print(a.__doc__, a.save.__doc__)
    print(DATA_PATH)
