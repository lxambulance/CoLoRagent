""" docstring: 将Test目录添加到当前执行搜索目录 """


import sys
import os


TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(TEST_DIR)
