# CoLoRagent

[TOC]

## 简介

这是一个CoLoR网络架构下的代理系统，有一个简单的界面和一个监听进程，主语言是python，前端使用了pyqt5以及相关的一些库，后端使用了scapy库绑定网卡直接发自定义格式包。

### 前端现状

该前端是一个简易的网盘系统，支持“生产者”注册文件，然后“消费者”抓取文件。主界面分为两大部分，上方是文件列表，支持基本文件操作，下方是网络拓扑，支持基本图形操作以及一些与文件列表的结合操作，下方右边是一些信息反馈以及控制相关，将所有不太适合做在拓扑图里的功能放在这里，并且通过标签页切换。 

![截图1](https://raw.githubusercontent.com/lxambulance/cloudimg/master/img/%E6%88%AA%E5%9B%BE1.PNG)

![截图2](https://raw.githubusercontent.com/lxambulance/cloudimg/master/img/%E6%88%AA%E5%9B%BE2.PNG)

![截图3](https://raw.githubusercontent.com/lxambulance/cloudimg/master/img/%E6%88%AA%E5%9B%BE3.PNG)

以上是项目网盘功能的基础展示，为了更好地体现CoLoR的特性，诸如溯源、防止攻击等。接下来将罗列一些待添加或待改进的功能。

- 收包显示（做到图中）
- AS统计信息（做到图中）
- 攻击溯源（类似收包，换种颜色）
- 数据包泄露检测
- 流数据传输
- 安全认证

## 前端数据文件存储

以Json格式存储 1、基本数据条目，二维结构；2、拓扑图；3、其余一些客户端代理配置信息

```json
{
    "base data":[
        [ "name", "path", "SID",
         false,//is register
         false, //is download
         "secret level",
         "white list"
        ],
        [...]
    ],
    "topo map":{
        "nodes": [
			{"type","name","size","nid","pos","font","color"}, //all attributes
			{"type":0(AS), "size": 384, "tfont":, "tcolor":}, //tfont和tcolor用于AS通量统计
			{"type":1(RM), "nid":"11111111111111111111111111111111"}, 
			{"type":2(BR), "nid":"11111111111111112222222222222222"},
			{"type":3(normal router)}
			{"type":4(Switch)}
			{"type":5(agent-me), "nid":"11111111111111111111111111111110"}
        ],
        "edges":[
            [1, 3, "px", "font", "color"],
            [2, 4]
        ],
        "ASinfo":{
            "2":[1,3]
        }
    },
    "user info":{
    	"filetmppath":"D:/CodeHub/CoLoRagent/.tmp/",
    	"myNID":"11111111111111111111111111111110",
        "RMIPv4":"10.0.0.1",
        "myIPv4":"192.168.50.192"
    }
}
```

*注意：topo map中nodes第一组为完整格式说明，接下来6组分别举例了各类型节点必要属性，其余属性可不添加，另外nodes里pos属性如果存在那么所有节点都存在。*

"base data"每列含义（./SourceCode/serviceTable.py）如下：

```python
COLUMN = ['文件名', '路径', 'SID', '是否通告', '是否下载', '密级指定', '白名单']
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

## 编译器版本以及库依赖

python3.9.1

```
cryptography 3.4.7
opencv-python 4.5.3.56
PyQt5 5.15.4
pyqtgraph 0.11.1
pyqt5-tools 5.15.2.3.0.2
qdarkstyle 3.0.2
scapy 2.4.4
```

为了有较好的qt编程体验建议安装pyqt5-stubs，然后配置vscode中的pylint，这样可以让编译器联想和提示库函数。

## 进度

- 2021.2.24 目前只包含前端几个页面以及一些简单的按钮逻辑。
- 2021.3.10 前端基本完成，开始考虑前后交互的逻辑。
- 2021.3.15 美化了前端几个界面的设计，开始阅读后端代码。
- 2021.3.18 前后端融合完成，非常简陋的初始版本。
- 2021.3.29 做了一定美化，暂时没有时间更新readme。
- 2021.3.30 删除了无用的页面，增加和细化了一些功能。
- 2021.4.25 完成了一次完整联调，还有待改进的点，以及一些小功能。
- 2021.5.11 完成了联调，主要功能完成，操作体验上还有优化空间。
- 2021.6.1 研究了scapy发包库，添加了一些测试工具，接下去要从界面设计，后续功能添加等方面考虑。
- 2021.7.13 近期有点摸鱼，写不动代码，慢慢从细节修改。
- 2021.7.27 集成了视频流功能，界面基本更新完毕。

作为git练习，dev分支可能会出现许多无聊地、甚至错误地提交。

warning: 不要尝试重构他人代码（费力不讨好，学习除外），修改的同时容易埋更多bug，当做黑盒能用就行。
