# CoLoRagent

[TOC]

## introduce

这是一个CoLoR网络架构下的代理系统，有一个界面和一个后端监听，主语言是python，前端使用了pyqt库，后端使用了scapy库绑定网卡直接发自定义包。

文件夹内Icon包含一些图标文件，PageUI包含QT的ui文件，SourceCode包含代码源文件（目前只有一个文件夹，前后端代码不多，都在这里了），test文件夹下放了一些测试用文件，可以随意添加。

## schedule

- 2021.2.24 目前只包含前端几个页面以及一些简单的按钮逻辑。
- 2021.3.10 前端基本完成，开始考虑前后交互的逻辑。
- 2021.3.15 美化了前端几个界面的设计，开始阅读后端代码。
- 2021.3.18 前后端融合完成，非常简陋的初始版本。
- 2021.3.29 做了一定美化，暂时没有时间更新readme。
- 2021.3.30 删除了无用的页面，增加和细化了一些功能。

作为git练习，dev分支可能会出现许多无聊地、甚至错误地提交。

## 界面需求分析

### 主界面功能

添加，下载，切换模式，鼠标左右点击。

### 通告功能

指定路径、指定白名单操作作为按钮显示在拓扑图右侧，可以勾选，并显示相应的附加指令

左侧拓扑图实时显示信息传递

### 获取功能

通过按键获取，并添加一个进度条表示下载进度

关于SID获取，暂时在添加文件界面加入了一个从网络添加SID的功能，可以引入其他电脑的SID文件。

我认为应用使用时，应该自行生成诸如文件名称、格式、大小、路径等配置文件SID，可以简单的使用json格式存储，然后传输时首先获取这个SID，然后顺藤摸瓜获取文件本体。

### 异常处理

待分析

### 易用性

主要还是体现在图形化界面操作和收发包显示上。

## 前端数据文件存储

以json格式存储 1、基本数据条目，二维结构；2、拓扑图

```json
{
	"base data":[
        [
        "name",
        "path",
        "SID",
        is_reg,
        is_down
        ],
        []
    ],
    "topo map":{
        "node type":[
            1,3,2
        ],
        "node name":[
            "hello",
            "",
            "world"
        ],
        "edge":[
            [1,3]
        ],
        "AS":{
            2:[1,3]
        }
    }
}
```

每列含义（./SourceCode/serviceTable.py）如下：

```python
COLUMN = ['文件名', '路径', 'SID', '是否通告', '是否下载']
```

拓扑中node type含义如下：

```python
NodeType = ['router', 'BR', 'RM', 'cloud']
```



## 代理用户层接口函数说明（ProxyLib.py）

### 简介

1. def Sha1Hash(path) #计算文件hash，path为文件路径。
2. def AddCacheSidUnit(path, AM, N, L, I, level) #将通告加入缓存，path为文件路径，AM表示通告单元动作类型（新增0x1、更新0x2、注销0x3），N、L、I分别表示n_sid，l_sid，nid能否省略，level表示信息级别（密级通告？），可暂时不理。
3. def DeleteCacheSidUnit(path) #删除通告缓存，删除对应缓存文件，path为文件路径。暂时缺少应用场景。
4. def SidAnn(ttl, publickey, P) #发送通告文件，所有参数均为默认值
5. def Get(SID, path, ttl, publickey, QoS, SegId) #获取文件，SID为服务ID，path为存放路径，后边参数暂时设为默认值，不管

传递时文件以文件路径做唯一标记（可能不是最好的实现方式，待改进）。

### AddCacheSidUnit(path, AM, N, L, I, level=-1)详细说明

path：文件路径

AM：含义同announce_unit的AM字段（详见：包格式文档）。int类型，可为1~3。

N：含义同announce_unit的N字段。int类型，可为0~1。

L：含义同announce_unit的L字段。int类型，可为0~1。

I：含义同announce_unit的I字段。int类型，可为0~1。

level：可选策略字段，标注当前SidUnit等级。int类型，可为1~10，或不填。

### SidAnn(ttl=64, PublicKey='', P=1)详细说明

功能：从待通告Cache中整合已生成SID策略单元，向RM发送对应ANN报文。

ttl：可选字段，含义同通告包的ttl字段。int类型，可为0~255。

PublicKey：可选字段，含义同通告包的Public_key字段。String类型，规定内含字符为16进制字符（0~9，a~f），字符串长度为2的倍数，最短长度为2。

P：可选字段，含义同通告包的P字段。int类型，可为0~1。

### Get(SID, path, ttl=64, PublicKey='', QoS='', SegID=-1, A=1)详细说明

功能：发送Get报文，从网络中获取特定SID对应的内容，存储到规定位置。

SID：希望从网络中获取内容的SID。String类型，规定内含字符为16进制字符（0~9，a~f），长度为32（仅N_sid）、40（仅L_sid）或72（完整SID）。

path：从网络获取内容后期望存储的位置（含文件名！）。格式同此前path。

ttl：可选字段，含义同get包的ttl字段。int类型，可为0~255。

PublicKey：可选字段，含义同get包的Public_key字段。格式同此前PublicKey。

QoS：可选字段，含义同get包的QoS_requirements字段。格式同PublicKey。

SegID：可选字段，含义同get包的Seg_ID字段。int类型，可选范围为0~0xffffffff。

A：可选字段，含义同get包的A字段。int类型，可为0~1。

## ProxyLib.py公共变量说明

### CacheSidUnits = {key:value}

功能：暂存通过AddCacheSidUnit生成，但尚未调用SidAnn进行通告的SID通告单元。

Key: String类型，调用AddCacheSidUnit时使用的文件路径。

Value：通过AddCacheSidUnit生成的通告单元类（class SidUnit，记录了通告单元信息）。

### AnnSidUnits = {key:value}

功能：记录已向网络中通告的SID，以及对应的通告策略。

Key：SID。String类型，规定内含字符为16进制字符（0~9，a~f），长度为32（仅N_sid）、40（仅L_sid）或72（完整SID）。

Value：通告单元，格式同CacheSidUnits的Value。

### gets = {key:value}

功能：记录当前请求中（即发送了get但暂未完全接收到）的SID信息。

Key：SID。格式同上。

Value：目标存储路径(含文件名)，String类型。

## problem

### 前端设计

#### 1. 拆分model/view [solved]

> 问题描述：如果使用qfilesystemmodel将没法添加文件自定义属性（没找到相关修改方法）；如果使用qstandarditemmodel暂时无法和三种view联动；如果使用自己实现model与前者类似，不法重载data函数以应对三种view调用

解决方法：一个data多个model、一个model一个view的方式实现。

#### 2. 前后端的服务类能否共用一个 [unsolved]

> 问题描述：为了存储数据条目，前后端分别实现了一个服务类，能否共用一个？这用交互起来还方便一些。

#### 3. graphicview中多个graphicitem坐标定位 [solved]

> 问题描述：多个graphicitem虽然可以一起移动，但是显示坐标与预期不符。

item的坐标原点与view一开始一致，通过setpos可以修改item坐标原点，这时两个坐标系需要转化

#### 4. python类变量与qt信号 [solved]

> 问题描述：python类变量如果是可变类型，那么由于类共享，可以被实例修改。但是qt信号看起来比较特殊，它只能作为类变量，并且不会被实例修改。

看起来qt在信号与槽的连接上做了一定的封装，不过简单来说信号就是个函数指针，connect的时候会先new一个指针作为实例的成员变量，再连接函数。

#### 5. 异步操作时后续的危险操作 [unsolved]

> 问题描述：子线程执行时主线程的修改将会产生未定义的行为。

#### 6. 文件拖拽不成功 [solved]

> 问题描述：按照教程实现的文件拖拽不成功，阅读qt文档做修改也一样。

windows文件拖拽权限问题，explorer为中权限，运行环境为管理员权限，是最高权限，windows中不允许低权限向高权限拖拽。

## Appendix

### pyqt学习记录

#### Widget dialog layout

占坑

#### Model/view模型

[model / view programming](https://doc.qt.io/qt-5/model-view-programming.html)

##### 简介

Model/View is a technology used to separate data from views in widgets that handle data sets.

Model/view also makes it easier to use more than one view of the same data because one model can be passed on to many views. 

![modelview-overview](https://doc.qt.io/qt-5/images/modelview-overview.png)

All item **models** are based on the [QAbstractItemModel](https://doc.qt.io/qt-5/qabstractitemmodel.html) class. This class defines an interface that is used by views and delegates to access data. The data itself does not have to be stored in the model; it can be held in a data structure or repository provided by a separate class, a file, a database, or some other application component.

Complete implementations are provided for different kinds of **views**: [QListView](https://doc.qt.io/qt-5/qlistview.html) displays a list of items, [QTableView](https://doc.qt.io/qt-5/qtableview.html) displays data from a model in a table, and [QTreeView](https://doc.qt.io/qt-5/qtreeview.html) shows model items of data in a hierarchical list. Each of these classes is based on the [QAbstractItemView](https://doc.qt.io/qt-5/qabstractitemview.html) abstract base class. Although these classes are ready-to-use implementations, they can also be subclassed to provide customized views.

##### proxy model

Views manage selections within a separate selection model, which can be retrieved with the [selectionModel()](https://doc.qt.io/qt-5/qabstractitemview.html#selectionModel) method. 

The selection model (as shown above) can be retrieved, but it can also be set with [QAbstractItemView::setSelectionModel](https://doc.qt.io/qt-5/qabstractitemview.html). This is how it's possible to have 3 view classes with synchronized selections because only one instance of a selection model is used. To share a selection model between 3 views use [selectionModel()](https://doc.qt.io/qt-5/qabstractitemview.html#selectionModel) and assign the result to the second and third view class with [setSelectionModel()](https://doc.qt.io/qt-5/qabstractitemview.html#setSelectionModel).

In the model/view framework, items of data supplied by a single model can be shared by any number of views, and each of these can possibly represent the same information in completely different ways. Custom views and delegates are effective ways to provide radically different representations of the same data. However, applications often need to provide conventional views onto processed versions of the same data, such as differently-sorted views onto a list of items.

Although it seems appropriate to perform sorting and filtering operations as internal functions of views, this approach does not allow multiple views to share the results of such potentially costly operations. The alternative approach, involving sorting within the model itself, leads to the similar problem where each view has to display items of data that are organized according to the most recent processing operation.

##### Delegates

The view has a [setItemDelegate()](https://doc.qt.io/qt-5/qabstractitemview.html#setItemDelegate) method that replaces the default delegate and installs a custom delegate. A new delegate can be written by creating a class that inherits from [QStyledItemDelegate](https://doc.qt.io/qt-5/qstyleditemdelegate.html). In order to write a delegate that displays stars and has no input capabilities, we only need to override 2 methods. 

[paint()](https://doc.qt.io/qt-5/qstyleditemdelegate.html#paint) draws stars depending on the content of the underlying data. The data can be looked up by calling [index.data()](https://doc.qt.io/qt-5/qmodelindex.html#data). The delegate's [sizeHint()](https://doc.qt.io/qt-5/qabstractitemdelegate.html#sizeHint) method is used to obtain each star's dimensions, so the cell will provide enough height and width to accommodate the stars.

##### The Graphics View Architecture

*QGraphicsScene* provides the Graphics View scene. The scene has the following responsibilities:

- Providing a fast interface for managing a large number of items
- Propagating events to each item
- Managing item state, such as selection and focus handling
- Providing untransformed rendering functionality; mainly for printing

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

### git

#### 基本操作

```shell
# 文件操作
git add/rm file/folder # 文件（文件夹）在暂存区添加/删除
git commit -m "message" # 提交到本地版本库
git checkout --filename # 撤销工作区文件修改
git reset HEAD filename # 撤销暂存区文件修改
git diff filename # 比较文件修改，先比较暂存区，没有时比较工作区

# 查看操作
git status # 查看工作区修改情况
git log # 查看git历史信息
git log --oneline # 一行简洁显示历史信息
git log --graph # 显示对应合并分支图

# 分支管理
git branch name # 创建分支，-d删除
git checkout name # 切换分支，-b创建且切换
git merge name # 将name分支与当前所在分支合并，此时默认会触发快速合并，加--no-ff可以关闭

# 连接github
git config --global user.email "email" # 设置本地全局用户邮箱
git config --global user.name "name" # 设置本地全局用户名
ssh-keygen -t rsa -C "email" # 生成ssh密钥，加密算法可换，生成的公钥文件内容需要添加到github网站方可正常访问。
ssh -v git@github.com # ssh连接测试

# 远程库管理
git remote -v # 显示远程库绑定情况
git remote rename a b # 将远程库a改名为b
git clone git_address # 克隆远程库，默认下载master分支
git checkout -b dev origin/dev # 连接本地库dev与远程库dev

# 其他
git config --global alias.lg "log --color --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit" # 设置命令别名

```

本地库目录下创建.gitignore 文件，然后把要忽略的文件名填进去，Git 就会自动忽略这些文件。

#### 多人协作

主分支master，开发分支dev只有一个。只上传dev分支，master分支视dev分支完成情况合并。

dev分支clone到本地后新建自己的分支，代码完事后合并到dev分支然后提交。一下代码主要描述由于多人协作发生的git push失败后的处理。

```shell
# 首先配置github的ssh，拥有访问权限

# 第一次获取代码
git clone git_address
git branch --set-upstream-to dev origin/dev # 远程库默认名origin，可以git remote rename改名

# 修改后提交
git push origin dev # dev是远程库对应分支名

# 出现冲突
git pull --rebase # 建议加rebase，这样简单的修改（不涉及到他人代码部分）直接变成一条分支，显示效果比较好

# 修改完冲突后再次正常提交即可
```

#### commit提交要求

```text
<type>(<scope>):<subject>

type(必须)
feat：新功能（feature）。
fix/to：修复bug，可以是QA发现的BUG，也可以是研发自己发现的BUG。
	fix：产生diff并自动修复此问题。适合于一次提交直接修复问题
	to：只产生diff不自动修复此问题。适合于多次提交。最终修复问题提交时使用fix
docs：文档（documentation）。
style：格式（不影响代码运行的变动）。
refactor：重构（即不是新增功能，也不是修改bug的代码变动）。
perf：优化相关，比如提升性能、体验。
test：增加测试。
chore：构建过程或辅助工具的变动。
revert：回滚到上一个版本。
merge：代码合并。
sync：同步主线或分支的Bug。

scope(可选)
scope用于说明 commit 影响的范围，比如数据层、控制层、视图层等等，视项目不同而不同。
例如在Angular，可以是location，browser，compile，compile，rootScope， ngHref，ngClick，ngView等。如果你的修改影响了不止一个scope，你可以使用*代替。

subject(必须)
subject是commit目的的简短描述，不超过50个字符。
建议使用中文（感觉中国人用中文描述问题能更清楚一些）。
结尾不加句号或其他标点符号。

范例
fix(DAO):用户查询缺少username属性
feat(Controller):用户查询接口开发
```