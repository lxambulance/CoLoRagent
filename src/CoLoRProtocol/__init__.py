""" docstring: 将ColorProtocol包目录添加到当前执行搜索目录 """


import sys
import os


PROTOCOL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROTOCOL_DIR)
# print('\n'.join(sys.path))
