# coding=utf-8
''' docstring: data store '''

# 添加文件路径../
import os
import sys
__BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
sys.path.append(__BASE_DIR)
HOME_DIR = __BASE_DIR + '/.tmp'

import json

DATA_PATH = __BASE_DIR + '/data.db'

class FileData:
    ''' docstring: class FileData '''

    def __init__(self, *, initData = None, nid = None):
        self.__data = initData or []
        self.nid = nid or f"{1:032x}"
        # TODO: raw data 放到别处去
        self.__raw_data = {}

    def getData(self, row, column = 0):
        ''' docstring: 获取数据 '''
        if row<0 or row>=self.rowCount() or column<0 or column>=len(self.__data[row]):
            return None
        return self.__data[row][column]

    def setData(self, row, column = 0, newData = None):
        ''' docstring: 写入数据 '''
        if row<0 or column<0 or row>=self.rowCount() or column>=self.columnCount():
            return
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

    def addItem(self, *, filename, filepath, isReg = 0, have = 1, **kwargs):
        ''' docstring: 添加文件时的处理 '''
        filehash = kwargs.get('filehash', None)
        # TODO: 处理file addtion text
        item = [filename, filepath, filehash, isReg * 100, have * 100]
        self.__data.append(item)

    def removeItem(self, row):
        if row < self.rowCount():
            del self.__data[row]

    def rowCount(self):
        return len(self.__data)

    def columnCount(self):
        return 5

    def load(self, Path = None):
        ''' docstring: 从数据路径加载数据 '''
        last = self.rowCount()
        if Path == None:
            Path = DATA_PATH
        pos = Path.find('db')
        if pos == -1:
            print('这不是一个合法的data类型文件')
            return
        with open(Path, 'r') as f:
            try:
                self.__raw_data = json.load(f)
            except:
                print('json格式转换失败，数据加载失败')
                return
            items = self.__raw_data['base data']
            for item in items:
                item_nid = item[2][:32]
                # print(item_nid)
                if self.nid != item_nid:
                    # 非本机通告文件
                    item[1] = HOME_DIR + '/' + item[0]
                    if item[3] != 100:
                        continue
                    elif not os.path.exists(item[1]) or not os.path.isfile(item[1]):
                        item[4] = 0
                else:
                    # 本机通告文件，存在性检测
                    if not os.path.exists(item[1]):
                        continue
                self.__data.append(item)

    def save(self, Path = None):
        ''' docstring: 将数据保存到数据路径中 '''
        if Path == None:
            Path = DATA_PATH
        with open(Path, 'w') as f:
            self.__raw_data['base data'] = self.__data
            json.dump(self.__raw_data, f)

if __name__ == '__main__':
    a = FileData()
    print(a.__doc__, a.save.__doc__)
    print(DATA_PATH)
    a.load()
