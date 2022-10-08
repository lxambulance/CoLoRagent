# libuv

## 0. 简介

> 为什么后端一定需要一个并发库？路由器和后端编程的区别在哪里？
> 
> 以上是项目中最大的问题，个人的理解是区别在于文件IO（非网络套接字），即是否连接硬盘。后端单纯在内存中处理完全可以做到与路由器一致，只有增加硬盘后，硬盘IO大大制约了后端效率。因此需要一个并发库，libuv的具体实现方式也证实了这点。

libuv是一个后端并发库，用于处理网络IO、文件IO、定时器等事件并发。基本原理是线程维护一个事件队列，每次循环检测事件发生并调用相应回调。

库本体采用c语言编写，使用统一API封装支持多平台。实际开发中使用libuvw辅助库，该库是对libuv的一个现代c++封装，仅包含封装必要的头文件。非常适合用于练习c++11相关特性的编程。

## 1. 安装

github下载[libuvw](https://github.com/skypjack/uvw/tags)，本次项目中使用uvw-2.8.0，与之关联的libuv库版本是v1.40。

github下载[libuv](https://github.com/libuv/libuv/tags)对应版本v1.40.0，小版本号无所谓。

下载后按照readme提示安装即可。

## 2. 编译、链接

本次项目编译、链接均在ubuntu环境完成

uv安装完成后与libmemif一样，头文件和链接库均已加入系统目录。只需要在编译时加-l参数指定动态链接库名称即可，头文件正常使用。

uvw安装完成后头文件将导入标准库目录，直接使用即可。**注意需要加-std=c++17**。

编译示例如下

```shell
gcc main.c icmp_proto.c -o main -I. -lmemif -lpthread
g++ main.c -o main -lmemif -luv -std=c++17
```

## 3. 实现原理

> libuv uses a thread pool to make asynchronous file I/O operations possible, but network I/O is always performed in a single thread, each loop’s thread. 

libuv实现中区分了

## 4. 关联库libmemif说明

libmemif用于后端与vpp协议栈通过共享内存方式连接。

> 直接的进程间共享内存通信缺少交互协议，libmemif就是封装了一个交互协议。

1. libmemif在vpp项目extras文件夹下，需要单独编译，编译后头文件libmemif.h将放到标准目录下，可直接使用，但是链接文件需要单独提供目录，在编译目录下lib文件夹中。
2. 链接动态文件g++需要给出-L目录，-l库名称
3. libmemif.h是c文件，与c++混合编程的时候需要注意加extern "C"。
4. UDS当做一个tcp socket处理，default socketfile = /run/vpp/memif.sock
