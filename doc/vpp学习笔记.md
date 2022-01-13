# vpp学习笔记

## 0 简介

当前机器已经有能力解决C10K问题，由于不同平台有不同的函数接口，推荐使用流行跨平台库，如libuv，libev等。

问题来到C10M，此时系统协议栈将成为阻碍，因此需要绕过。

> C10K: web servers to handle **ten thousand** clients simultaneously
> 
> C10M: ... **ten million** ...

DPDK(Data plane development kit)是一个比较优秀的工具，但是直接操作网卡，协议栈需要一步一步往上搭，比较麻烦。故考虑使用vpp(vector packet processing)，这是FD.io(Fast Data Project)项目的子项目，底层使用DPDK，具有2-4层多平台、快速、可扩展的网络协议栈，运行于linux操作系统，支持容器化操作管理，并且已经应用于多种场景(cisco赞助并使用)。vpp更上层还有honeycomb管理接口，适用于SDN；ligato管理接口，适用于云端实现虚拟网络函数。

## 1 安装

教程节选自[官方文档](https://s3-docs.fd.io/vpp/22.02/index.html) ，有部分参考[官方wiki](https://wiki.fd.io/view/VPP)

PS：事实上这两玩意应该一致，但是wiki有些文章未放到文档中，非常迷惑。

### 下载官方安装包

> 此方法一般用于vpp直接部署，依赖cli和配置文件修改运行逻辑，不涉及新协议。

在文件源 **/etc/apt/sources.list.d/99fd.io.list** 中添加

```textile
deb [trusted=yes] https://packagecloud.io/fdio/master/ubuntu bionic main
```

添加信任源

```shell
curl -L https://packagecloud.io/fdio/master/gpgkey | sudo apt-key add -
```

然后更新源并安装，最后一行为卸载包命令，其中vpp-api-python包看起来找不到（目测是python2停止使用），但不影响使用。

```shell
sudo apt-get update
sudo apt-get install vpp vpp-plugin-core vpp-plugin-dpdk
sudo apt-get install vpp-api-python python3-vpp-api vpp-dbg vpp-dev
sudo apt-get remove --purge "vpp*"
```

### 自行编译安装

> 此方法用于编写自己的vpp插件，编译过程自动集成自定义插件。

首先需要确保编译期间机器与 **github.com** 网站的连接稳定。

```shell
git clone https://gerrit.fd.io/r/vpp
cd vpp
# 使用较为稳定的v21.10.1版本
git checkout -b test v21.10.1
```

确保没有安装vpp和dpdk，如果有先 **apt-get remove**

```shell
dpkg -l | grep vpp
dpkg -l | grep DPDK
```

在主目录下运行以下命令

```shell
make install-dep # 安装依赖包
make build # 编译debug版本
make build-release # 编译release版本
make pkg-deb # 构建debian安装包
sudo dpkg -i *.deb # 在build-root文件夹下安装编译后的包
```

运行一般不会一次成功，按照提示运行相关命令或者重新编译。

##### 踩坑记录

系统选择ubuntu20.04，当前vpp版本22.02，避免部分包在低版本找不到或没法编译

大部分安装不通过是网络问题，请确保连通github，然后指令重复run几遍一般就好了

小部分安装不通过是未达到编译要求内存8GB

## 2 结构

### vpp整体结构

![vpp-layer](https://raw.githubusercontent.com/lxambulance/cloudimg/master/img/VPP_Layering.png)

1. vpp infra: 基础库，包含基础的函数和数据结构，向量、hash、定时器

2. vlib：矢量包处理库，包含基础管理功能，节点、缓冲区、线程

3. vnet：网络协议栈库，包含平台、设备无关的协议栈，2、3、4层矢量包处理节点，流量管理，控制面接口，设备接口

4. plugins：插件库，包含丰富功能的集合

> 狭义的vpp仅仅是一个数据面软件，一切为了达到极致的转发效率。当然考虑到方便开发和调试，vpp提供api和cli的控制面管理功能。

### feature&feature arc

> A ‘feature’ in this context is any subsystem/module/etc that wants to see/modify/fiddle with the packet as it traverses the switch-path.
> 
> A feature arc is a sub-graph of nodes – maybe graph is too flexible a word in this context as it’s really only an ordered linear set, or pipeline, of nodes.

以上为特性与特性弧的[官方wiki](https://wiki.fd.io/view/VPP/Feature_Arcs)定义。虽然wiki也简单地交代了其由来和功能，但是仍然存在诸多困惑。最大的问题是为什么特性弧只有十几个？按照个人理解至少每个节点一个。

```markdown
            |    Arc Name      |
            |------------------|
            | device-input     |
            | ethernet-output  |
            | interface-output |
            | ip4-drop         |
            | ip4-local        |
            | ip4-multicast    |
            | ip4-output       |
            | ip4-punt         |
            | ip4-unicast      |
            | ip6-drop         |
            | ip6-local        |
            | ip6-multicast    |
            | ip6-output       |
            | ip6-punt         |
            | ip6-unicast      |
            | mpls-input       |
            | mpls-output      |
            | nsh-output       |
```

最终该问题在一篇网络[博客](https://blog.actorsfit.com/a?ID=01000-c174f31c-9566-45fb-a7c4-d0aca03a0d7f)中得到解答。早期vpp节点框架是固定的，修改或添加新特性就不容易，因此添加特性机制，主要描述的就是节点中可以在运行时通过命令改变的一些功能。一个特性落实到一个节点上，一个节点可以有多个特性（个人推测，未证实），多个特性组合形成特性弧。只有高变化、可配置的数据路径才有特性弧，固定数据路径没有特征弧，因此总数量只有十几个。

#### 添加新节点

添加新节点可以通过添加特征的方式修改数据流向，唯一需要注意的就是特征弧的选择。

当然也可以**不依赖特征弧**，这时候需要在初始化的时候调用节点提供的重定向函数或是彻底重载部分函数，将固定连边转接到新节点上。

> ### L1
> 
> vnet_hw_interface_rx_redirect_to_node (vnet_main_t *vnm, u32 hw_if_index, u32 node_index) Redirect the rx data of a hw interface to a node, node_index is the index index of the node
> 
> ### L2, L3
> 
> ethernet_register_input_type (vlib_main_t *vm, ethernet_type_t type, u32 node_index) will insert a specific type of node after the "ethernet-input" node,  where type includes ethernet_type (0x806, ARP), ethernet_type (0x8100, VLAN), ethernet_type (0x800, IP4) such as two, three protocol  
> specific support of the relevant agreements, see src/vnet/ethernet/types.def file.
> 
> ### L4
> 
> ip4_register_protocol (u32 protocol, u32 node_index) will insert a specific protocol node after the "ip4-local" node, where the protocol includes ip_protocol (6, TCP), ip_protocol (17, UDP) and other four-layer protocols.  See the src/vnet/ip/protocols.def file for specific supported protocols.
> 
> ### L5
> 
> udp_register_dst_port (vlib_main_t * vm, udp_dst_port_t dst_port, u32 node_index, u8 is_ip4) will insert a specific dst_port node after the "ip4-udp-lookup" node, where dst_port includes five-layer application ports such as ip_port (WWW, 80).  See the src/vnet/ip/ports.def file for the specific supported ports.

由于color协议的固定性，这里推荐L4注册新协议的办法。

## 3 使用

### 运行

自行编译运行可以编译出deb包，然后正常安装，这样路径位置与直接安装编译包位置一致；若仅编译调试，相关api文件路径位置在build-root文件夹下，后续操作需要**留意并修改**

```shell
# 运行默认vpp，配置文件位于/etc/vpp/startup.conf
sudo service vpp start/stop
# 运行新配置文件
sudo /usr/bin/vpp -c ./your_startup_file
```

#### 配置文件说明

startup.conf 参数说明

### 调试

```shell
# 不带gdb运行，可以使用cli测试
make run-release
make run
# 带gdb运行
make debug-release
make debug
# gdb模式下可以输入配置文件运行
run -c /etc/vpp/startup.conf
```

### api简介

vpp api模块通过共享内存的方式提供交流接口，一般适用于自动化管理。

插件中定义的接口在编译阶段转变为c语言头文件和标准JSON格式，外部高级语言可以通过解析JSON文件并调用c语言头文件实现与vpp绑定。

#### c语言api

详细说明请参考[How to use the C API](https://wiki.fd.io/view/VPP/How_To_Use_The_C_API)，该教程结合源码介绍了Capi一些基础规定，对后续理解非常有帮助。

由于vpp本身采用C语言编写，所以c api最大的优势是可以直接调用c函数。

> 关于API定义，参见后文[VPP API 语言](#api-language)
> 
> 按照编写规定，request/reply 类型消息request名可以任意（但不要用dump结尾），reply会在对应request名后添加**\_reply**；dump/details 类型消息dump名以**\_dump** 结尾，返回消息details以 **\_details** 结尾。另外dump/details为了区分多条details是否结束，最后会返回一条**control\_ping**消息。

c/c++语言api头文件（由安装包 **vpp-dev\*.deb** 提供）一般位于路径 **/usr/include/vapi** ，包含自定义插件。

#### c++语言api绑定

c++

#### python语言api绑定

python语言绑定需要安装**python3-vpp-api\*.deb**，并且需要JSON文件路径作为索引。目测高级语言绑定都通过socket(/run/vpp/api.sock)，仅c/c++底层使用共享内存，故效率上有明显区别。

##### 踩坑记录

官方文档中的python绑定使用python2，但是在vpp21.10.1中已经没有python2了，全部改用python3。因此需要参照源码 **\vpp\src\vpp-api\python\vpp_papi\vpp_papi.py** 对实例代码做出一点微调。

主要修改部分：

1. import VPP修改为VPPApiClient

2. load_json_api_files路径修改

```python
#!/usr/bin/env python

from __future__ import print_function

import os
import fnmatch

from vpp_papi import VPPApiClient

CLIENT_ID = "client"
VPP_JSON_DIR = '/usr/share/vpp/api/'
API_FILE_SUFFIX = '*.api.json'

def load_json_api_files(json_dir=VPP_JSON_DIR, suffix=API_FILE_SUFFIX):
    jsonfiles = []
    for root, dirnames, filenames in os.walk(json_dir):
        # print(root, dirnames, filenames)
        for filename in fnmatch.filter(filenames, suffix):
            jsonfiles.append(os.path.join(root, filename))

    if not jsonfiles:
        print('Error: no json api files found')
        exit(-1)

    # print(jsonfiles)

    return jsonfiles


def connect_vpp(jsonfiles):
    vpp = VPPApiClient(apifiles=jsonfiles)
    r = vpp.connect(CLIENT_ID)
    print("VPPApiClient opened with code: %s" % r)
    return vpp


def dump_interfaces():
    print("Sending dump interfaces. Msg id: sw_interface_dump")
    for intf in vpp.api.sw_interface_dump():
        print("\tInterface, message id: sw_interface_details, interface index: %s" % intf.interface_name)


def dump_bds():
    print("Sending dump bridge domains. Msg id: bridge_domain_dump")
    for intf in vpp.api.bridge_domain_dump(bd_id = int("ffffffff", 16)):
        print("\tBridge domain, message id: bridge_domain_details, bd index: %s" % intf.bd_id)


def create_loopback():
    print("Sending create loopback. Msg id: create_loopback_interface")
    vpp.api.create_loopback()


def create_bd():
    print("Sending create loopback. Msg id: create_loopback_interface")
    vpp.api.bridge_domain_add_del(is_add = 1, bd_id = 99)


# Python apis need json definitions to interpret messages
vpp = connect_vpp(load_json_api_files())
# Dump interfaces
dump_interfaces()
# Create loopback
create_loopback()
# Dump interfaces
dump_interfaces()
# Dump bridge-domains
dump_bds()
# Create bridge domain
create_bd()
# Dump bridge-domains
dump_bds()

exit(vpp.disconnect())
```

### cli简介

cli一般适用于人工操作，不适合自动化管理。

```shell
# 默认配置vpp可以直接连接
sudo vppctl <cli-command>
```

cli支持网络telnet连接或者本机socket连接，telnet连接需要配置文件中在unix结构下添加 **cli-listen localhost:5002** ；socket连接需要添加 **cli-listen /run/vpp/cli.sock**

> **warning**：telnet通信不加密，注意安全风险

```shell
# 通过socket连接vpp
sudo vppctl -s /run/vpp/cli.sock
# 通过网络连接vpp
telnet localhost 5002
```

连接配置：

- 横幅可以通过配置文件unix结构添加 **cli-no-banner** 去除

- 命令行提示符可以通过unix结构添加 **cli-prompt <string>** 设置

- 输出分页可以通过unix结构添加 **cli-no-pager** 去除，或者通过 **cli-pager-buffer-limit 5000** 设置缓存上限

### 容器简介

container

## 4 编写

### 插入一个插件

从零开始编写全部插件内容比较困难，源码 **./extras/emacs** 中提供了构建插件的脚本，在插件文件夹 **./src/plugins** 下运行

```shell
cd ./src/plugins
../../extras/emacs/make-plugin.sh
```

脚本需要输入插件名和插件运行类型，完成后生成相应目录与文件。

#### vpp plugin文件结构与内容

CMakeLists.txt

- SOURCES: 一系列c语言源文件
- API_FILES: 一系列API接口定义文件
- MULTIARCH_SOURCES: 主要影响性能的图节点文件
- API_TEST_SOURCES: api接口测试文件

按照需要修改CMakeList配置

```cmake
add_vpp_plugin (myplugin
SOURCES
myplugin.c
node.c
myplugin_periodic.c
myplugin.h

MULTIARCH_SOURCES
node.c

API_FILES
myplugin.api

API_TEST_SOURCES
myplugin_test.c
)
```

myplugin.api

- 约定API消息接口。消息可以是阻塞或非阻塞模式。消息用于与VPP引擎沟通，配置修改数据处理路径。

具体语言格式参见[VPP API 语言](#api-language)

```c
option version = "0.1.0";
import "vnet/interface_types.api";

autoreply define sample_macswap_enable_disable {
  /* Client identifier, set from api_main.my_client_index */
  u32 client_index;

  /* Arbitrary context, so client can match reply to request */
  u32 context;

  /* Enable / disable the feature */
  bool enable_disable;

  /* Interface handle */
  vl_api_interface_index_t sw_if_index;
};
```

myplugin.c

- 插件的定义和初始化

```c
VLIB_PLUGIN_REGISTER () =
{
  .version = VPP_BUILD_VER,
  /*.default_disabled = 1,*/
  .description = "myplugin plugin description goes here",
};
//注册插件名称及描述
/* API definitions */
#include <myplugin/myplugin.api.c>

static clib_error_t * myplugin_init (vlib_main_t * vm)
{
  myplugin_main_t * mmp = &myplugin_main;
  clib_error_t * error = 0;

  mmp->vlib_main = vm;
  mmp->vnet_main = vnet_get_main();

  /* Add our API messages to the global name_crc hash table */
  mmp->msg_id_base = setup_message_id_table ();

  return error;
}
//注册结点初始化1
VNET_FEATURE_INIT (myplugin, static) =
{
  .arc_name = "device-input",
  .node_name = "myplugin",
  .runs_before = VNET_FEATURES ("ethernet-input"),
};
//注册结点初始化2
VLIB_CLI_COMMAND (myplugin_enable_disable_command, static) =
{
  .path = "myplugin enable-disable",
  .short_help =
  "myplugin enable-disable <interface-name> [disable]",
  .function = myplugin_enable_disable_command_fn,
};
//注册结点CLI命令
```

myplugin_periodic.c

- 常驻监听线程

```c
void myplugin_create_periodic_process (myplugin_main_t *mmp)
{
  /* Already created the process node? */
  if (mmp->periodic_node_index > 0)
    return;

  /* No, create it now and make a note of the node index */
  mmp->periodic_node_index = vlib_process_create (mmp->vlib_main,
    "myplugin-periodic-process",
    myplugin_periodic_process, 16 /* log2_n_stack_bytes */);
}
//创建监听线程响应事件
```

node.c

- 实际处理节点

```c
VLIB_NODE_FN (myplugin_node) (vlib_main_t * vm, vlib_node_runtime_t * node,
                             vlib_frame_t * frame);
//结点功能实现

VLIB_REGISTER_NODE (myplugin_node);
//注册结点结构体
```

### api接口定义

<span id="api-language"></span>

采用了vpp自定义的一种类c风格语言，主要有三种类型的消息

- Request/Reply(1-1)：调用端程序发送request消息，vpp引擎返回一条简单reply消息
- Dump/Detail(1-n)：批量消息请求与返回，与前者的差别目测是一条和多条...
- event(1-1-n)：异步消息响应，用于调用端程序监视vpp一些接口状态的改变，首先需要注册，会返回一条简单reply消息，然后等待事件触发，返回多次所需消息

#### define

```c
define show_version
{
  u32 client_index;
  u32 context;
};
define show_version_reply
{
  u32 context;
  i32 retval;
  string program [32];
  string version [32];
  string build_date [32];
  /* The final field can be a variable length argument */
  string build_directory [];
};
```

```bison
define : DEFINE ID '{' block_statements_opt '}' ';'
define : flist DEFINE ID '{' block_statements_opt '}' ';'
flist : flag
      | flist flag
flag : MANUAL_PRINT
     | MANUAL_ENDIAN
     | DONT_TRACE
     | AUTOREPLY

block_statements_opt : block_statements
block_statements : block_statement
                 | block_statements block_statement
block_statement : declaration
                | option
declaration : type_specifier ID ';'
            | type_specifier ID '[' ID '=' assignee ']' ';'
declaration : type_specifier ID '[' NUM ']' ';'
            | type_specifier ID '[' ID ']' ';'
type_specifier : U8
               | U16
               | U32
               | U64
               | I8
               | I16
               | I32
               | I64
               | F64
               | BOOL
               | STRING
type_specifier : ID
```

#### option

```c
option version = "1.0.0";
```

```bison
option : OPTION ID '=' assignee ';'
assignee : NUM
         | TRUE
         | FALSE
         | STRING_LITERAL
```

#### typedef

```c
typedef u8 ip4_address[4];
typedef u8 ip6_address[16];
typedef address {
  vl_api_address_family_t af;
  vl_api_address_union_t un;
};
```

```bison
typedef : TYPEDEF ID '{' block_statements_opt '}' ';'
typedef : TYPEDEF declaration
```

#### import

```bison
import : IMPORT STRING_LITERAL ';'
```

#### comment

```bison
/* */
//
```

#### enum

```c
enum ip_neighbor_flags
{
  IP_API_NEIGHBOR_FLAG_NONE = 0,
  IP_API_NEIGHBOR_FLAG_STATIC = 0x1,
  IP_API_NEIGHBOR_FLAG_NO_FIB_ENTRY = 0x2,
};
```

```bison
enum : ENUM ID '{' enum_statements '}' ';'
enum : ENUM ID ':' enum_size '{' enum_statements '}' ';'
enum_size : U8
          | U16
          | U32
enum_statements : enum_statement
                | enum_statements enum_statement
enum_statement : ID '=' NUM ','
               | ID ','
```

#### services

```c
service {
  rpc want_interface_events returns want_interface_events_reply
    events sw_interface_event;
};
```

```bison
service : SERVICE '{' service_statements '}' ';'
service_statements : service_statement
                | service_statements service_statement
service_statement : RPC ID RETURNS NULL ';'
                     | RPC ID RETURNS ID ';'
                     | RPC ID RETURNS STREAM ID ';'
                     | RPC ID RETURNS ID EVENTS event_list ';'
event_list : events
           | event_list events
events : ID
       | ID ','
```

详细信息参见[文档](https://s3-docs.fd.io/vpp/22.02/interfacing/binapi/vpp_api_language.html)

### 启动配置文件

## 5 实例

#### 如何编写c应用程序调用vpp

实操部分推荐博客[c api使用](https://www.marosmars.com/blog/managing-vpp-c-edition)，目测由于版本不同存在问题，建议使用 **/src/vpp-api/client/** 路径下vac封装。
