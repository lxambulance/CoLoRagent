""" docstring: 将Backend目录添加到当前执行搜索目录 """


import sys
import os


BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BACKEND_DIR)
