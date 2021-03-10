# ProjectCloud

[TOC]

## introduce

这是一个CoLoR网络架构下的简单网盘系统，主要语言是python，前端使用了pyqt库。

文件夹内Icon包含一些图标文件，PageUI包含所有QT的ui文件以及对应编译好的python源码，SourceCode包含代码源文件

## schedule

- 2021.2.24 目前只包含前端几个页面以及一些简单的按钮逻辑。

作为git练手，dev分支可能会出现许多无聊地提交

### 原文件拆分重构

两部分要求：一是做到前后端分离；二是item缺少对应结构。

前后端分离基本结构是对于每个耗时操作编写对应线程类，通过qthread由子线程完成，完成后通过信号返回。

### 界面需求

#### 主界面网盘功能

添加（默认注册一条龙），下载，切换模式。

#### 注册子窗体功能

指定路径等详细操作

## problem

### 1.拆分model/view [nearly solved]

> 问题描述：如果使用qfilesystemmodel将没法添加文件自定义属性（没找到相关修改方法）；如果使用qstandarditemmodel暂时无法和三种view联动；如果使用自己实现model与前者类似，不法重载data函数以应对三种view调用

解决方法（暂时）：一个data多个model、一个model一个view的方式实现。