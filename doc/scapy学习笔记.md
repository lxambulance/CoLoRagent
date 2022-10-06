# Scapy

## 自定义新协议

scapy是一个有趣的可以交互的网络工具库，当前为了方便发包，详细阅读了相关教程文档[Adding a new protocols](https://scapy.readthedocs.io/en/latest/build_dissect.html)，完成了几个小工具，文件均存放在test/下，后续可能用来做交互界面。

scapy的强大在于写完包格式框架后，对于一段网络报文，它可以自己推导构建，省去了诸多不方便的地方，另外还可以诸如自动计算checksum，pkg_length等报文字段，用 **/** 符号可以连接上下层协议。以下记录了一些使用心得。

scapy报文存在三种格式，**i**(nternal)是scapy内部存储的格式，与python对象基本没有区别，各种字段的值就是int或str或list；**m**(achine)是网络报文格式，是实际发包的内容，一般在发包前做最后的转化；**h**(uman)是便于人类读取的格式，将python对象有层次的展示出来，便于命令行交互。

定义报文只需要编写fields_desc列表各字段格式，[教程文档](https://scapy.readthedocs.io/en/latest/build_dissect.html)里详细介绍了报文定义之后后续代码如何转换，简单来说Packet使用Field类定义各字段，Field类不是一个个实体，反而有点像一个专用处理组件，负责处理自己这个字段的格式转换，然后Packet工厂按字段顺序交给组件处理，最后拼接形成网络报文，还比较有趣。

遇到的第一个比较头疼的问题是Field字段大小，一下给了一些常用字段大小，看名字基本可以猜出字段大小，然后前面加**X**表示16进制，加**Signed**表示有符号数，加**LE**表示字段为小端表示。其他有些可以自定义大小，非常方便，具体如何可以使用参考源码。

```python
ByteField
XByteField

ShortField
SignedShortField
LEShortField
XShortField

X3BytesField        # three bytes as hex
LEX3BytesField      # little endian three bytes as hex
ThreeBytesField     # three bytes as decimal
LEThreeBytesField   # little endian three bytes as decimal

IntField
SignedIntField
LEIntField
LESignedIntField
XIntField

LongField
SignedLongField
LELongField
LESignedLongField
XLongField
LELongField

IEEEFloatField
IEEEDoubleField
BCDFloatField       # binary coded decimal

BitField
XBitField

BitFieldLenField    # BitField specifying a length (used in RTP)
FlagsField
FloatField
```

第二个主要使用的功能是变长类型字段，有一个字段描述列表字段个数或长度，然后列表字段存储相应个数或长度的内容，这个只需要使用在字段后加count_of和count_from即可（长度对应length_of和length_from），如下代码所示，值得注意的是adjust可以调整count出的结果，对于一些数量不实际对应列表数量的字段非常方便。这里有一点疑惑的是为什么需要两个函数，一个count_of，一个count_from而且二者看起来是反函数。原因是两者用于不同的流程，一是构造，一是解包，前者需要在生成时自动统计个数，后者需要在解析时确定列表大小。

```python
class TestPLF(Packet):
    fields_desc=[ 
        FieldLenField("len", None, count_of="plist", 
        	adjust=lambda pkt,x:x),
        PacketListField("plist", None, IP,
        	count_from=lambda pkt:pkt.len)
    ]
```

第三个主要使用的功能是后处理自动计算checksum字段。使用post_build函数可以在基本字段构造完后，再处理一些需要最后处理的字段，比如报文总长度和checksum，具体代码如下。这个时候需要直接操作最后的网络报文，需要知道对应字段所在字节位置，另外这个结果是个python的bytes类型。

```python
def post_build(self, pkt, pay):
        if self.header_length is None:
            self.header_length = len(pkt)
            pkt = pkt[:6] + int2Bytes(self.header_length, 1) + pkt[7:]
        if self.pkg_length is None:
            self.pkg_length = len(pkt) + len(pay)
            pkt = pkt[:2] + int2BytesLE(self.pkg_length, 2) + pkt[4:]
        if self.checksum is None:
            self.checksum = CalcChecksum(pkt)
            pkt = pkt[:4] + int2Bytes(self.checksum, 2) + pkt[6:]
        # print(self.pkg_length, self.header_length, self.checksum)
        return pkt + pay
```

最后要说的是scapy一个比较灵活的胶水语言特性，bind_layers函数，用法如下，然后构造是可以直接在CoLoR_Control包后边接IP_nid包，解析时也会根据tag推敲后续包类型。比较坑爹的一点是无法处理冲突，即有多个条件满足的时候是会使用第一个定义类型，所以有时候不如不用（因为其原理只是简单的将判断条件添加到了一个列表packet.payload_guess，然后逐条匹配）。bind_layers更进一步的推导函数是guess_payload_class(self, payload)，它可以有更丰富的条件判断。

```python
# 用于解析时推导负载字段
bind_layers(CoLoR_Control, IP_nid, tag="PROXY_REGISTER")
# 用于构建时自动填写tag字段
bind_layers(CoLoR_Control, IP_nid, {'tag':5})
# 更丰富的猜测负载方法
class Dot11(Packet):
    def guess_payload_class(self, payload):
        if self.FCfield & 0x40:
            return Dot11WEP
        else:
            return Packet.guess_payload_class(self, payload)
```

## scapy具体解析步骤

主要函数是**Packet.dissect()**

```python
def dissect(self, s):
    s = self.pre_dissect(s)
    s = self.do_dissect(s)
    s = self.post_dissect(s)
    payl,pad = self.extract_padding(s)
    self.do_dissect_payload(payl)
    if pad and conf.padding:
        self.add_payload(Padding(pad))
def do_dissect_payload(self, s):
    cls = self.guess_payload_class(s)
    p = cls(s, _internal=1, _underlayer=self)
    self.add_payload(p)
def do_dissect(self, s):
    flist = self.fields_desc[:]
    flist.reverse()
    while s and flist:
        f = flist.pop()
        s,fval = f.getfield(self, s)
        self.fields[f] = fval
    return s
```

以下为每个函数主要功能：

-   pre_dissect() 用于处理前准备
-   do_dissect() 实际的处理函数
-   post_dissection() 用于最后更新某些字段，比如校验和等
-   extract_padding() 用于区分载荷和填充字段
-   do_dissect_payload() 用于解析载荷，主要用于猜测后续协议，是scapy胶水特性的主要体现

想要添加新协议，需要搞清楚上述函数主要功能，重载需要改变的部分。

scapy包的build过程也是一个类似的情况，具体推荐[官方教程](https://scapy.readthedocs.io/en/latest/build_dissect.html)
