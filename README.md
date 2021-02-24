# ProjectCloud

## introduce

这是一个color网络架构下的简单网盘系统。

## schedule

- 2021.2.24 目前只包含前端几个页面以及一些简单的按钮逻辑。

dev分支修改了文件目录结构，PageUI将作为一个python包，SourceCode将包含源文件，其中color文件还需要进一步拆分（作为git练手，现阶段版本会多次提交）。

### 原color文件拆分

两部分，一是前后端分离，二是item缺少对应结构

#### 耗时操作

- 撤销通告包 selectItem
- 撤销本地缓存 selectItem
- 删除item window.ui.treeWidget
- 双击items显示信息 
- 添加文件 window.ui.treeWidget
- 注册单个文件
- 注册多个文件
- 注册过程本体
- 获取单个文件数据
- 获取多个文件数据
- 获取数据本体
- 导入其他配置文件
- 保存配置文件
- 读取配置文件

基本思路是建立子线程处理耗时操作，最后处理完用信号机制回传信息。

#### 不耗时操作

- 打开仓库
- 打开命令行
- 打开视频页面
- 显示右键菜单栏
- 单击items选中
- 主窗体关闭事件