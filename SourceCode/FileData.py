# coding=utf-8
''' docstring: data store '''

import json

__DATA_PATH = 'data.db'

def changeDataPath(newpath):
    ''' docstring: change DATA_PATH '''
    global __DATA_PATH
    __DATA_PATH = newpath

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

    def rowCount(self):
        return len(self.__data)
    
    def columnCount(self):
        return len(self.__data[0])

    def load(self):
        ''' docstring: 从数据路径加载数据 '''
        with open(__DATA_PATH, 'r') as f:
            self.__data = json.load(f)

    def save(self):
        ''' docstring: 将数据保存到数据路径中 '''
        with open(__DATA_PATH, 'w') as f:
            json.dump(self.__data, f)

if __name__ == '__main__':
    a = FileData()
    print(a.__doc__, a.save.__doc__)
    print(__DATA_PATH)
    changeDataPath('./'+__DATA_PATH)
    print(__DATA_PATH)
