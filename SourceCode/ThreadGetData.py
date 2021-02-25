# coding=utf-8
'''
docstring: 获取数据子线程，初始化传入文件条目列表，信号传出结果
'''
from PyQt5.QtCore import QThread, pyqtSignal

class ThreadGetData(QThread):
    '''
    docstring: 获取数据类
    '''
    msg = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        # 传入时考虑

    def run(self):
        '''线程主体'''
        # 处理时考虑

    def getItemData(self):
        '''获取单个文件数据'''
        if self.selectItem is None or self.selectItem.text(2) == '是':
            return
        print('start getting item data', self.selectItem)
        self.getData(self.selectItem)

    def getItemsData(self):
        '''获取多个文件数据'''
        print('start getting items data')
        size = window.ui.treeWidget.topLevelItemCount()
        for i in range(size):
            item = window.ui.treeWidget.topLevelItem(i)
            if item.text(2) == '否':
                print(item.text(0))
                self.getData(item)

    def getData(self, item):
        '''获取数据本体'''
        if item.text(1) == '否':
            return
        # 计算sid，发送get包，收取data包
        item.setText(2, '是')
        fpath = self.home_dir+'/'+item.text(0)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write('Hello World!')
            f.close()
        item.setText(3, fpath)
        self.statusBar().showMessage('下载 ' + item.text(0) + ' 完成')

if __name__ == '__main__':
    print('ThreadGetData module test start')
    print('ThreadGetData module test end')
