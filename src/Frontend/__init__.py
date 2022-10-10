""" docstring: 将Frontend包目录添加到当前执行搜索目录 """


import sys
import os


FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(FRONTEND_DIR)
