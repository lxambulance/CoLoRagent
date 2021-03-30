# ProjectCloud

[TOC]

## introduce

这是一个CoLoR网络架构下的简单网盘系统，主要语言是python，前端使用了pyqt库，后端使用了scapy库绑定网卡直接发自定义包。

文件夹内Icon包含一些图标文件，PageUI包含所有QT的ui文件，SourceCode包含代码源文件（目前只有一个文件夹，可能后期考虑前后端代码分离看起来方便，会另建文件夹）。

## schedule

- 2021.2.24 目前只包含前端几个页面以及一些简单的按钮逻辑。
- 2021.3.10 前端基本完成，开始考虑前后交互的逻辑。
- 2021.3.15 美化了前端几个界面的设计，开始阅读后端代码。
- 2021.3.18 前后端融合完成，非常简陋的初始版本。
- 2021.3.29 做了一定美化，暂时没有时间更新readme。

作为git练手，dev分支可能会出现许多无聊地提交

### 前端原文件拆分重构

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

### 前端数据文件存储

以json格式存储数据条目，二维结构

```json
{
	{
	"name",
	"path",
    sid,
	is_reg,
	is_down
	},
	...
}
```

每列含义（./SourceCode/serviceTableModel.py）如下：

```python
COLUMN = ['文件名', '路径', 'SID', '是否通告', '是否下载']
```

是否通告是包含两位（bit）信息，0x2表示向RM通告，0x1表示本地通告缓存。

### 代理用户层接口函数说明（from ProxyLib）

#### 太长不看版

1. def Sha1Hash(path) #计算文件hash，path为文件路径。
2. def AddCacheSidUnit(path, AM, N, L, I, level) #将通告加入缓存，path为文件路径，AM表示通告单元动作类型（新增0x1、更新0x2、注销0x3），N、L、I分别表示n_sid，l_sid，nid能否省略，level表示信息级别（密级通告？），可暂时不理。
3. def DeleteCacheSidUnit(path) #删除通告缓存，删除对应缓存文件，path为文件路径。
4. def SidAnn(ttl, publickey, P) #发送通告文件，所有参数均为默认值
5. def Get(SID, path, ttl, publickey, QoS, SegId) #获取文件，SID为服务ID，path为存放路径，后边参数暂时设为默认值，不管

传递时文件以文件路径做唯一标记（可能不是最好的实现方式，待改进）。

#### 01 Sha1Hash(path):

##### 功能说明：

使用Sha1算法，计算特定文件的160位哈希值。

调用需要提供SID的函数（如ANN），或进行内容验证时会用到。

##### 参数说明：

path： String类型，为特定文件对应的路径字符串，如'F:\\研一下\\系统搭建\\代码实现\\kebiao.png'。

#### 02 AddCacheSidUnit(path, AM, N, L, I, level=-1):

##### 功能说明：

生成单个SID通告单元到待通告Cache中。

##### 参数说明：

path：同上

AM：含义同announce_unit的AM字段（详见：包格式8文档）。int类型，可为1~3。

N：含义同announce_unit的N字段。int类型，可为0~1。

L：含义同announce_unit的L字段。int类型，可为0~1。

I：含义同announce_unit的I字段。int类型，可为0~1。

level：可选策略字段，标注当前SidUnit等级。int类型，可为1~10，或不填。

#### 03 DeleteCacheSidUnit(path):

##### 功能说明：

从待通告Cache中删除已生成但未通告的SID策略单元。

##### 参数说明：

path：同上

#### 04 SidAnn(ttl=64, PublicKey='', P=1):

##### 功能说明：

从待通告Cache中整合已生成SID策略单元，向RM发送对应ANN报文。

##### 参数说明：

ttl：可选字段，含义同通告包的ttl字段。int类型，可为0~255。

PublicKey：可选字段，含义同通告包的Public_key字段。String类型，规定内含字符为16进制字符（0~9，a~f），字符串长度为2的倍数，最短长度为2。

P：可选字段，含义同通告包的P字段。int类型，可为0~1。

#### 05 def Get(SID, path, ttl=64, PublicKey='', QoS='', SegID=-1, A=1):

##### 功能说明：

发送Get报文，从网络中获取特定SID对应的内容，存储到规定位置。

##### 参数说明：

SID：希望从网络中获取内容的SID。String类型，规定内含字符为16进制字符（0~9，a~f），长度为32（仅N_sid）、40（仅L_sid）或72（完整SID）。

path：从网络获取内容后期望存储的位置（含文件名！）。格式同此前path。

ttl：可选字段，含义同get包的ttl字段。int类型，可为0~255。

PublicKey：可选字段，含义同get包的Public_key字段。格式同此前PublicKey。

QoS：可选字段，含义同get包的QoS_requirements字段。格式同PublicKey。

SegID：可选字段，含义同get包的Seg_ID字段。int类型，可选范围为0~0xffffffff。

A：可选字段，含义同get包的A字段。int类型，可为0~1。

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

### 5. 异步操作时后续的危险操作 [unsolved]

> 问题描述：子线程执行时主线程的修改将会产生未定义的行为。

## Appendix

### pyqt学习记录

#### Widget dialog layout

占坑

#### Model/view模型

占坑

#### Extra data signal

占坑

#### Threads&processes

占坑

#### Packaging

##### pyinstaller

使用pyinstaller打包文件。

```bash
python -m venv packenv
call packenv\scripts\activate.bat
pip install pyqt5 pyinstaller
```

第一次打包直接运行pyinstaller app.py将生成build与dist两个文件夹，build包含调试用信息，dist(distribute)包含需要分发的所有文件（比如windows环境中包含exe）；另外生成了**.spec**文件，该文件是python语言的编译选项，可以做python运算。

之后修改后打包可以通过运行pyinstaller app.spec来完成。

运行pyinstaller时添加-n "app name"可以为生成的应用添加文件名，-w可以去除运行时的后端控制台，--onefile可以生成一个EXE文件（虽然便于分发，但是运行时启动比较慢），--icon可以指定生成的EXE文件的.ico图标，主窗口图标由主程序窗体类自行设置，windows菜单栏图标可以按照下方代码设置。

```python
try:
    # Include in try/except block if you're also targeting Mac/Linux
    from PyQt5.QtWinExtras import QtWin
    myappid = 'mycompany.myproduct.subproduct.version'
    QtWin.setCurrentProcessExplicitAppUserModelID(myappid)
    # or use ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID
except ImportError:
    pass
```

使用pyinstaller打包时，源文件中的文件路径指定的文件不会添加到打包文件夹中（当然，那就是个字符串路径，会硬编译到程序中），所以分发时需要带着资源文件一起分发，比较麻烦。

通过--add-data="your_icon.ico;."或者在.spec中analysis部分添加datas=[('your_icon.ico','.')]可以将资源文件导入dist文件夹。

除此之外，通过qt resources system可以直接将资源文件转化为python文件，就不需要考虑添加文件。

最后整个dist文件夹可以通过installForge软件打包成安装包，分发给用户安装。

##### fbs

fbs是跨平台pyqt5打包工具，它是基于pyinstaller的扩展版本，实现了更为简单的自动化打包。



### json

**J**ava**S**cript **O**bject **N**otation（javascript对象表示法），存储和交换文本信息的语法，类似XML。由于其字符串的存储形式，便于进程交互，另外python自带的库文件可以直接解析相应结构。

#### 简单操作

```python
import json # python3.9自带
a = json.dumps(['foo',{'bar':('baz',None,1.0,2)}]) # 将json格式转化为python str
b = json.loads(a) # 将python str转化为json格式（python list）
# 下面两个函数用于文件操作
json.dump(obj, fp)
obj = json.load(fp)
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

