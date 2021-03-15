# ProjectCloud

[TOC]

## introduce

这是一个CoLoR网络架构下的简单网盘系统，主要语言是python，前端使用了pyqt库，后端使用了scapy库绑定网卡直接发自定义包。

文件夹内Icon包含一些图标文件，PageUI包含所有QT的ui文件，SourceCode包含代码源文件（目前只有一个文件夹，可能后期考虑前后端代码分离看起来方便，会另建文件夹）。

## schedule

- 2021.2.24 目前只包含前端几个页面以及一些简单的按钮逻辑。
- 2021.3.10 前端基本完成，开始考虑前后交互的逻辑。
- 2021.3.15 美化了前端几个界面的设计，开始阅读后端代码。

作为git练手，dev分支可能会出现许多无聊地提交

### 原文件拆分重构

两部分要求：一是做到前后端分离；二是item缺少对应结构。

前后端分离基本结构是对于每个耗时操作编写对应线程类，通过qthread由子线程完成，完成后通过信号返回。

### 界面需求

#### 主界面功能

添加，下载，切换模式。

#### 通告功能

指定路径、指定白名单操作作为按钮显示在拓扑图中，可以勾选，右侧显示相应的附加指令

#### 获取功能

除了一个按钮获取，暂时不知道其他要求（可以加一个进度条表示下载进度。如何提前获取文件大小？）。

#### 异常处理

待分析

#### 命令行

待分析

### 网络层接口

1. def AddCacheSidUnit(path, AM, n_sid, l_sid, nid, level, whitelist) #将通告加入缓存
2. def Hash(path) #计算文件hash
3. def DeleteCacheSidUnit(path) #删除通告缓存
4. def SidAnn(ttl, publickey, P) #生产通告文件
5. def SendPkt_ipv4(ipdst, pkt) #发送通告ipv4域
6. def Get(SID, path, ttl, publickey, QoS, SegId) #获取文件

可能需要进一步改进

## problem

### 1. 拆分model/view [nearly solved]

> 问题描述：如果使用qfilesystemmodel将没法添加文件自定义属性（没找到相关修改方法）；如果使用qstandarditemmodel暂时无法和三种view联动；如果使用自己实现model与前者类似，不法重载data函数以应对三种view调用

解决方法（暂时）：一个data多个model、一个model一个view的方式实现。

### 2. 前后端的服务类能否共用一个 [unsolved]

> 问题描述：为了存储数据条目，前后端分别实现了一个服务类，能否共用一个？这用交互起来还方便一些。

### 3. graphicview中多个graphicitem坐标定位 [solved]

> 问题描述：多个graphicitem虽然可以一起移动，但是显示坐标与预期不符。

item的坐标原点与view一开始一致，通过setpos可以修改item坐标原点，这时两个坐标系需要转化

### 4. python类变量与qt信号 [solved]

> 问题描述：python类变量如果是可变类型，那么由于类共享，可以被实例修改。但是qt信号看起来比较特殊，它只能作为类变量，并且不会被实例修改。

看起来qt在信号与槽的连接上做了一定的封装，不过简单来说信号就是个函数指针，connect的时候会先new一个指针作为实例的成员变量，再连接函数。

## appendix

### pyqt学习记录

#### widget dialog layout

占坑

#### model/view模型

占坑

#### extra data signal

占坑

#### Threads&processes

占坑

### json

**J**ava**S**cript **O**bject **N**otation（javascript对象表示法），存储和交换文本信息的语法，类似XML。由于其字符串的存储形式，便于进程交互，另外python自带的库文件可以直接解析相应结构。

#### 简单操作

```python
import json #python3.9自带
a = json.dumps(['foo',{'bar':('baz',None,1.0,2)}]) #将json格式转化为python str
b = json.loads(a) #将python str转化为json格式（python list）
```

#### Json Python类型转换表

|     JSON     | Python |
| :----------: | :----: |
|    object    |  dict  |
|    array     |  list  |
|    string    |  str   |
| number(int)  |  int   |
| number(real) | float  |
|     true     |  True  |
|    false     | False  |
|     null     |  None  |

