# CoLoRagent

[TOC]

## 简介

这是一个CoLoR网络架构下的代理系统，有一个简单的界面和一个监听进程，主语言是python，前端使用了pyqt5以及相关的一些库，后端使用了scapy库绑定网卡直接发自定义格式包。

### 前端现状

该前端是一个简易的网盘系统，支持“生产者”注册文件，然后“消费者”抓取文件。主界面分为两大部分，上方是文件列表，支持基本文件操作，下方是网络拓扑，支持基本图形操作以及一些与文件列表的结合操作，下方右边是一些信息反馈以及控制相关，将所有不太适合做在拓扑图里的功能放在这里，并且通过标签页切换。 

![image-20210520205141762](https://raw.githubusercontent.com/lxambulance/cloudimg/master/img/image-20210520205141762.png)

以上是项目网盘功能的基础展示，为了更好地体现CoLoR的特性，诸如溯源、防止攻击等。接下来将罗列一些待添加或待改进的功能。

- 收包显示（做到图中）
- AS统计信息（做到图中）
- 攻击溯源（类似收包，换种颜色）
- 数据包泄露检测

### 进度

- 2021.2.24 目前只包含前端几个页面以及一些简单的按钮逻辑。
- 2021.3.10 前端基本完成，开始考虑前后交互的逻辑。
- 2021.3.15 美化了前端几个界面的设计，开始阅读后端代码。
- 2021.3.18 前后端融合完成，非常简陋的初始版本。
- 2021.3.29 做了一定美化，暂时没有时间更新readme。
- 2021.3.30 删除了无用的页面，增加和细化了一些功能。
- 2021.4.25 完成了一次完整联调，还有待改进的点，以及一些小功能。
- 2021.5.11 完成了联调，主要功能完成，操作体验上还有优化空间。

作为git练习，dev分支可能会出现许多无聊地、甚至错误地提交。

warning: proxylib后端耦合度太高，可以适当拆分。但重构他人代码可能是大忌，修改的同时容易埋更多bug，不建议修改，当做黑盒能用就行。

## 前端数据文件存储

以Json格式存储 1、基本数据条目，二维结构；2、拓扑图；3、其余一些客户端代理配置信息

```json
{
    "base data":[
        [
        "name", "path", "SID", is_reg, is_down
        ]
    ],
    "topo map":{
        "nodes": [
			{"type":1, "name":"RM1", "nid":"11111111111111111111111111111111"}, 
			{"type":4}, 
			{"type":2, "nid":"11111111111111112222222222222222"}, 
			{"type":0, "name":"AS1", "size": 384}
        ],
        "edges":[
            [1,3]
        ],
        "ASinfo":{
            "2":[1,3]
        }
    },
    "filetmppath":"D:/CodeHub/CoLoRagent/.tmp/",
    "myNID":"11111111111111111111111111111110"
}
```

"base data"每列含义（./SourceCode/serviceTable.py）如下：

```python
COLUMN = ['文件名', '路径', 'SID', '是否通告', '是否下载']
```

"topo map"中"nodes"."type"含义如下：

```python
NodeType = ['cloud', 'RM', 'BR', 'router', 'switch', 'PC']
```

## 前端逻辑

[![](https://mermaid.ink/img/eyJjb2RlIjoiZ3JhcGggTFJcbiAgICBBWy9tYWluL10tLS0-fG1haW4gdGhyZWFkfEJbbWFpbndpbmRvd11cbiAgICBBLS4tPnxuZXcgdGhyZWFkfENbQ29Mb1JNb25pdG9yXVxuICAgIEItLS1EW0ZpbGUgbGlzdF1cbiAgICBCLS0tRVt0b3BvbG9naWNhbCBncmFwaF1cbiAgICBDLS4tPnxzaG93IG1lc3NhZ2V8RFxuICAgIEMtLi0-fHNob3cgcmVjZWl2ZSBwYWNrYWdlfEVcbiAgICBELS0tPnxhY3Rpb258RntuZWVkIHRpbWU_fVxuICAgIEUtLS0-fGFjdGlvbnxGXG4gICAgRi0tLT58WWVzfEdbbmV3IHRocmVhZCB0byBkb11cbiAgICBGLS0tPnxOb3xIW2RvIGl0IHJpZ2h0IG5vd11cbiAgICBHLS4tPkl7bG9vcH1cbiAgICBILS4tPklcbiAgICBJLS4tPnxZZXN8QlxuICAgIEktLi0-fE5vfEpbL0VuZC9dIiwibWVybWFpZCI6eyJ0aGVtZSI6ImRlZmF1bHQifSwidXBkYXRlRWRpdG9yIjpmYWxzZX0)](https://mermaid-js.github.io/mermaid-live-editor/#/edit/eyJjb2RlIjoiZ3JhcGggTFJcbiAgICBBWy9tYWluL10tLS0-fG1haW4gdGhyZWFkfEJbbWFpbndpbmRvd11cbiAgICBBLS4tPnxuZXcgdGhyZWFkfENbQ29Mb1JNb25pdG9yXVxuICAgIEItLS1EW0ZpbGUgbGlzdF1cbiAgICBCLS0tRVt0b3BvbG9naWNhbCBncmFwaF1cbiAgICBDLS4tPnxzaG93IG1lc3NhZ2V8RFxuICAgIEMtLi0-fHNob3cgcmVjZWl2ZSBwYWNrYWdlfEVcbiAgICBELS0tPnxhY3Rpb258RntuZWVkIHRpbWU_fVxuICAgIEUtLS0-fGFjdGlvbnxGXG4gICAgRi0tLT58WWVzfEdbbmV3IHRocmVhZCB0byBkb11cbiAgICBGLS0tPnxOb3xIW2RvIGl0IHJpZ2h0IG5vd11cbiAgICBHLS4tPkl7bG9vcH1cbiAgICBILS4tPklcbiAgICBJLS4tPnxZZXN8QlxuICAgIEktLi0-fE5vfEpbL0VuZC9dIiwibWVybWFpZCI6eyJ0aGVtZSI6ImRlZmF1bHQifSwidXBkYXRlRWRpdG9yIjpmYWxzZX0)

<details>
    <summary>查看源码</summary>
	<pre><code>graph LR
    A[/main/]--->|main thread|B[mainwindow]
    A-.->|new thread|C[CoLoRMonitor]
    B---D[File list]
    B---E[topological graph]
    C-.->|show message|D
    C-.->|show receive package|E
    D--->|action|F{need time?}
    E--->|action|F
    F--->|Yes|G[new thread to do]
    F--->|No|H[do it right now]
    G-.->I{loop}
    H-.->I
    I-.->|Yes|B
    I-.->|No|J[/End/]</code></pre>
</details>

### 前端相关文件结构

[![](https://mermaid.ink/img/eyJjb2RlIjoiZ3JhcGggVERcblx0QVttYWluLnB5XSAtLS0-IGJbbG9nSW5XaW5kb3cucHldXG5cdGIgLS0tPiBCW01haW5XaW5kb3cucHldXG5cdEIgLS0tPiBDW0FkZEl0ZW1XaW5kb3cucHldXG5cdEIgLS0tPiBEW0dyYXBoaWNXaW5kb3cucHldXG5cdEIgLS0tPiBFW0ZpbGVEYXRhLnB5XVxuXHRCIC0tLT4gRltzZXJ2aWNlTGlzdC5weV1cblx0QiAtLS0-IEdbc2VydmljZVRhYmxlLnB5XVxuXHRGIC0tLT4gRVxuXHRHIC0tLT4gRVxuXHRCIC0tLT4gSFt3b3JrZXIucHldXG5cdEQgLS0tPiBJW3RvcG9HcmFwaFZpZXcucHldXG5cdEQgLS0tPiBKW3RvcG9HcmFwaFNjZW5lLnB5XVxuXHRKIC0tLT4gS1tOb2RlRWRnZS5weV1cblx0SSAtLS0-IEpcblx0SSAtLS0-IEtcblx0QiAtLS0-IHJjWy9yZXNvdXJjZV9yYy5weS9dXG5cdEsgLS0tPiByY1xuXHRiIC0tLT4gbG9nSW5bL2xvZ0luRGlhbG9nLnB5L11cblx0QiAtLS0-IG1haW5bL01haW5QYWdlLnB5L11cblx0QyAtLS0-IGFkZFsvYWRkSXRlbURpYWxvZy5weS9dXG5cdG1lW-S4u-imgeS5puWGmeS7o-eggV1cblx0bm90bWVbL-W3peWFt-eUn-aIkOS7o-eggS9dIiwibWVybWFpZCI6eyJ0aGVtZSI6ImRlZmF1bHQifSwidXBkYXRlRWRpdG9yIjpmYWxzZX0)](https://mermaid-js.github.io/mermaid-live-editor/#/edit/eyJjb2RlIjoiZ3JhcGggVERcblx0QVttYWluLnB5XSAtLS0-IGJbbG9nSW5XaW5kb3cucHldXG5cdGIgLS0tPiBCW01haW5XaW5kb3cucHldXG5cdEIgLS0tPiBDW0FkZEl0ZW1XaW5kb3cucHldXG5cdEIgLS0tPiBEW0dyYXBoaWNXaW5kb3cucHldXG5cdEIgLS0tPiBFW0ZpbGVEYXRhLnB5XVxuXHRCIC0tLT4gRltzZXJ2aWNlTGlzdC5weV1cblx0QiAtLS0-IEdbc2VydmljZVRhYmxlLnB5XVxuXHRGIC0tLT4gRVxuXHRHIC0tLT4gRVxuXHRCIC0tLT4gSFt3b3JrZXIucHldXG5cdEQgLS0tPiBJW3RvcG9HcmFwaFZpZXcucHldXG5cdEQgLS0tPiBKW3RvcG9HcmFwaFNjZW5lLnB5XVxuXHRKIC0tLT4gS1tOb2RlRWRnZS5weV1cblx0SSAtLS0-IEpcblx0SSAtLS0-IEtcblx0QiAtLS0-IHJjWy9yZXNvdXJjZV9yYy5weS9dXG5cdEsgLS0tPiByY1xuXHRiIC0tLT4gbG9nSW5bL2xvZ0luRGlhbG9nLnB5L11cblx0QiAtLS0-IG1haW5bL01haW5QYWdlLnB5L11cblx0QyAtLS0-IGFkZFsvYWRkSXRlbURpYWxvZy5weS9dXG5cdG1lW-S4u-imgeS5puWGmeS7o-eggV1cblx0bm90bWVbL-W3peWFt-eUn-aIkOS7o-eggS9dIiwibWVybWFpZCI6eyJ0aGVtZSI6ImRlZmF1bHQifSwidXBkYXRlRWRpdG9yIjpmYWxzZX0)

<details>
    <summary>查看源码</summary>
	<pre><code>graph TD
	A[main.py] ---> b[logInWindow.py]
	b ---> B[MainWindow.py]
	B ---> C[AddItemWindow.py]
	B ---> D[GraphicWindow.py]
	B ---> E[FileData.py]
	B ---> F[serviceList.py]
	B ---> G[serviceTable.py]
	F ---> E
	G ---> E
	B ---> H[worker.py]
	D ---> I[topoGraphView.py]
	D ---> J[topoGraphScene.py]
	J ---> K[NodeEdge.py]
	I ---> J
	I ---> K
	B ---> rc[/resource_rc.py/]
	K ---> rc
	b ---> logIn[/logInDialog.py/]
	B ---> main[/MainPage.py/]
	C ---> add[/addItemDialog.py/]
	me[主要书写代码]
	notme[/工具生成代码/]</code></pre>
</details>

## 后端逻辑

[![](https://mermaid.ink/img/eyJjb2RlIjoiZ3JhcGggTFJcbiAgICBBWy9tYWluL10tLS0-fHN0YXJ0IHRocmVhZHxCW0NvTG9STW9uaXRvcl1cbiAgICBCLS0tPnxsaXN0ZW58Q3twYWNrYWdlLnR5cGU_fVxuICAgIEMtLWdldC0tPiBEW2NoZWNrIGRhdGFiYXNlIHRoZW4gc2VuZF1cbiAgICBDLS1kYXRhLS0-IEVbc3RvcmUgZGF0YWJhc2VdXG4gICAgQy0tY29udHJvbC0tPiBGW2NoYW5nZSBvcHRpb25dXG4gICAgRC0tLT4gR3tuZXh0P31cbiAgICBFLS0tPiBHXG4gICAgRi0tLT4gR1xuICAgIEctLi0-fFllc3xDXG4gICAgRy0tLT58Tm98SFsvRW5kL10iLCJtZXJtYWlkIjp7InRoZW1lIjoiZGVmYXVsdCJ9LCJ1cGRhdGVFZGl0b3IiOmZhbHNlfQ)](https://mermaid-js.github.io/mermaid-live-editor/#/edit/eyJjb2RlIjoiZ3JhcGggTFJcbiAgICBBWy9tYWluL10tLS0-fHN0YXJ0IHRocmVhZHxCW0NvTG9STW9uaXRvcl1cbiAgICBCLS0tPnxsaXN0ZW58Q3twYWNrYWdlLnR5cGU_fVxuICAgIEMtLWdldC0tPiBEW2NoZWNrIGRhdGFiYXNlIHRoZW4gc2VuZF1cbiAgICBDLS1kYXRhLS0-IEVbc3RvcmUgZGF0YWJhc2VdXG4gICAgQy0tY29udHJvbC0tPiBGW2NoYW5nZSBvcHRpb25dXG4gICAgRC0tLT4gR3tuZXh0P31cbiAgICBFLS0tPiBHXG4gICAgRi0tLT4gR1xuICAgIEctLi0-fFllc3xDXG4gICAgRy0tLT58Tm98SFsvRW5kL10iLCJtZXJtYWlkIjp7InRoZW1lIjoiZGVmYXVsdCJ9LCJ1cGRhdGVFZGl0b3IiOmZhbHNlfQ)

<details>
    <summary>查看源码</summary>
	<pre><code>graph LR
    A[/main/]--->|start thread|B[CoLoRMonitor]
    B--->|listen|C{package.type?}
    C--get--> D[check database then send]
    C--data--> E[store database]
    C--control--> F[change option]
    D---> G{next?}
    E---> G
    F---> G
    G-.->|Yes|C
    G--->|No|H[/End/]</code></pre>
</details>

## 后端接口函数

### proxylib.py功能函数简介

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

## 后端公共变量定义

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

## 项目文件夹说明

- Icon包含一些图标文件
- PageUI包含QT的ui文件
- SourceCode包含代码源文件（目前只有一个文件夹，前后端代码不多，都在这里了）
- test包含一些测试用文件，可以随意修改。

## 踩坑记录

### 前端设计

#### 1. 拆分model/view [solved]

> 问题描述：如果使用qfilesystemmodel将没法添加文件自定义属性（没找到相关修改方法）；如果使用qstandarditemmodel暂时无法和三种view联动；如果使用自己实现model与前者类似，不法重载data函数以应对三种view调用

解决方法：一个data多个model、一个model一个view的方式实现。

#### 2. 前后端的服务类能否共用一个 [solved]

> 问题描述：为了存储数据条目，前后端分别实现了一个服务类，能否共用一个？这用交互起来还方便一些。

需求不一，暂时分开存数据。

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

#### 7. 图元操作异常 [solved]

> 问题描述：删除连边不成功。

无法解决，猜测是图元类与信号的不合理混用，通过重构正常实现功能。

#### 8. 联合调试错误 [solved]

> 问题起因：单后端联合调试成功，加上前端报错，错误位置在后端，但是仅仅是报错，不影响使用。

最后发现是前端调试语句没有删除，多加了一句“后端注册成功”，然后多线程启动后端的时候出岔子了。

#### 9.拓扑图生成时存在交叉 [unsolved]

> 问题描述：一开始生成的拓扑图存在交叉线段

通过简单的判断交叉然后交换位置消除的方法不行，存在交换后新生成交叉的情况，还需要进一步处理。

## Appendix

### A. pyqt学习记录

#### Widget dialog layout

widget意为小组件，QWidget是一块空白块，一般qtdesignor里使用的都是xxxwidget，有特定功能，比较方便，比如Qmainwindow有菜单栏和状态栏。

dialog是特化的用户交互窗口，一般有yes、no选项，以及一些用户需要填写的信息，调用该窗口一般希望阻塞其他用户操作，逼迫其填写完毕后执行后续操作。

layout是小组件里嵌套组件的基本布局。萌新时期不懂这个作用，直接拖widget写了个窗口发现窗口禁不起拖动，因为组件坐标是绝对值，拉长之后不会重新布局。使用了layout就可以在窗口拖动后实现自动的重新布局，虽然可能效果不理想，需要进一步微调，但起码不至于离谱到找不到了。

#### 坐标系

在实现graphics一系列操作时不可避免地涉及到坐标系，pyqt总共有三个坐标系。

- 视图坐标（view coordinates），显示器物理坐标。所有小组件（widget）都使用这个坐标，即坐标原点在窗口左上角，y轴正方向向下。这是一个比较符合计算机书写逻辑的坐标系（参照excel表格），这个时候窗口大小也比较好表示，就是右下角坐标值。
- 场景坐标（scene coordinates），场景逻辑坐标。这是为了方便场景表示而采用的坐标系，即在qgraphicsscene中，坐标原点可以不是左上角（但是y轴还是朝下），程序员可以自定义取景框，取景框大小也不一定需要与视图大小一致，即支持放缩。场景中的顶层物体基于这个坐标系存储位置，与视图坐标之间存在转换矩阵。
- 图元坐标（item coordinates），图元逻辑坐标。为了方便图元之间实现嵌套表示而采用的坐标系，与场景坐标之间存在一个变换。嵌套的图元采用这个坐标系存储位置。

#### Model/view模型

[model / view programming](https://doc.qt.io/qt-5/model-view-programming.html)

##### 简介

MVC模型分离了数据、视图和操作，在Qt里简化成了M/V模型。具体到项目中遇到了一份数据两种形式显示的问题，虽然使用成熟的widget组件也可以轻松完成，但是数据需要存两份，同步起来不方便，也不利于后续数据库扩展（maybe），另外也是为了练手，采用model/view模型。

这里model/view虽然本意是一个model对应多个view，但是项目中两个view差异过大，不太容易用一个model表示，故写了两个model（数据还是只有一份，model可以看做基本数据操作模型）

![modelview-overview](https://raw.githubusercontent.com/lxambulance/cloudimg/master/img/modelview-overview.png?token=AGF5OL5FNAG3UCNCZGLSOSLAUINEK)

Qt中model都是根据QAbstractItemModel这个抽象类继承而来，该类定义了基本的视图或代理访问数据的接口，数据没有必要直接存在model里（就可以很方便的改写接数据库），而是由数据结构、分离的类、文件、数据库或其他应用组件完成。

Qt提供三种基本的视图，QListView、QTreeView和QTableView，使得用户可以定义少量的函数就直接使用。

##### 代理模型

简单来说就是遇到类似选择、排序和过滤等操作时，通过一层叠加的模型可以比较方便实现。（没有具体了解，或许项目中两个视图显示一份数据可以通过代理模型过滤）

##### 代表

代表delegate用于处理一些实时的渲染逻辑，比如重写paint()函数实现进度条加载。目前项目中只在进度条这用到了。简单阅读了文档，还可以做一些简单的功能例如编辑等操作。

##### 图形视图结构

类似于模型视图结构，不过这次的模型是图元，相对来说比model复杂一点，因为要考虑显示。使用图形视图结构的好处在于

- 提供了快速的接口管理大量的图元
- 可以传递事件到每个具体选择的图元
- 统一管理图元的状态信息，比如选择和关注（focus不知道怎么翻译，具体意思就是获取键盘控制权）
- 提供渲染转换函数，方便输出

题外话：Qt提供了四种类用于处理图像信息：QImage、QPixmap、QBitmap和QPicture。QImage是设计用于优化读写以及直接的像素级访问和操作，QPixmap是设计用于优化屏幕显示，QBitmap是一个继承于QPixmap且每个像素只有0/1的简单图像，QPixture是跟随画图类定义的一个用于执行画图操作的类。

#### 扩展数据信号

基本的Qt信号使用如下，就这么玩。

```python
from PyQt5.QtCore import QObject , pyqtSignal

class CustSignal(QObject):
    #声明无参数的信号
    signal1 = pyqtSignal()
    #声明带一个int类型参数的信号
    signal2 = pyqtSignal(int)
    #声明带int和str类型参数的信号
    signal3 = pyqtSignal(int,str)
    #声明带一个列表类型参数的信号
    signal4 = pyqtSignal(list)
    #声明带一个字典类型参数的信号
    signal5 = pyqtSignal(dict)
    #声明一个多重载版本的信号，包括带int和str类型参数的信号和带str类型参数的信号
    signal6 = pyqtSignal([int,str], [str])
    
    #将信号连接到指定槽函数
    self.signal1.connect(self.signalCall1)
    self.signal2.connect(self.signalCall2)
    self.signal3.connect(self.signalCall3)
    self.signal4.connect(self.signalCall4)
    self.signal5.connect(self.signalCall5)
    #重载版本的使用需要指明类型
    self.signal6[int,str].connect(self.signalCall6)
    self.signal6[str].connect(self.signalCall6OverLoad)
```

通过lambda函数可以做一些简单的扩展，更复杂的操作建议写闭包，lambda功能有限。

```python
    #将接受一个变量的槽改成了不接受变量的槽，通常这些操作用在循环里，i是循环变量
    self.signal2.connect(lambda:self.signalCall2(i))
```

#### 多线程与进程

具体参考[PyQt5 tutorial](https://www.mfitzp.com/courses/pyqt/)

本项目参考上述教程，直接将新建线程的操作抽象为新建一个worker类，然后通过信号绑定的操作实现线程之间的内容交互。

#### qt中exec_和show的区别

遇到窗口调用的时候老是遇到，总是存在疑问，暂时混用也没遇到什么大问题。

> QDialog的显示有两个函数show()和exec()。
>
> **show():**
> 显示一个非模态对话框。控制权即刻返回给调用函数。弹出窗口是否为模态对话框，取决于modal属性的值。
> （原文：Shows the dialog as a modeless dialog. Control returns immediately to the calling code. The dialog will be modal or modeless according to the value of the modal property. ）
>
> **exec():**
> 显示一个模态对话框，并且锁住程序直到用户关闭该对话框为止。函数返回一个DialogCode结果。在对话框弹出期间，用户不可以切换同程序下的其它窗口，直到该对话框被关闭。
> （原文：Shows the dialog as a modal dialog, blocking until the user closes it. The function returns a DialogCode result. Users cannot interact with any other window in the same application until they close the dialog. ）

在实现上，exec仅仅是在show的基础上加了一个事件循环来阻塞当前事件。所以使用show()加modal=True的方式仅仅是半模态，当前事件不会停止，立刻进行后续动作，与exec还是存在区别。

### B. Packaging文件打包

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

### C. Json

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

### D. pylint代码书写规则

1. 模块，类，函数都要用格式'''docstring:...'''写docstring且不能为空，描述相应对象用来做什么即可
2. 模块命名采用snake_case naming style，即单词用小写，连接单词用下划线
3. 类命名采用PascalCase naming style，即类名第一个字母大写，其他小写
4. 代码块最后多且仅多一行
5. 等号左右都有空格
6. 用逗号分隔参数时，逗号后要有一个空格
7. 一个类最好至少两个public函数
8. constant常量用全大写来命名

虽然我也经常不遵守规则，但最好写代码清醒的时候起名注意点。

### E. git使用

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
git remote add git_address # 增加远程库关联
git clone git_address # 克隆远程库，默认下载master分支
git checkout -b dev origin/dev # 新建并连接本地库dev与远程库dev
git branch --set-upstream-to dev origin/dev # 连接远端库与本地库，远程库默认名origin，可以git remote rename改名

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
git clone git_address # 默认下载默认库
git checkout -b dev origin/dev

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
本项目中没有太大的架构，可以指明文件替代。

subject(必须)
subject是commit目的的简短描述，不超过50个字符。
建议使用中文（感觉中国人用中文描述问题能更清楚一些）。
结尾不加句号或其他标点符号。

范例
fix(DAO):用户查询缺少username属性
feat(Controller):用户查询接口开发
```

