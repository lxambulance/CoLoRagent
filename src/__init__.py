""" docstring: 将src目录添加到当前执行搜索目录 """


import sys
import os


SRC_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SRC_DIR)
