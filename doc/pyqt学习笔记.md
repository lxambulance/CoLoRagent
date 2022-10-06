# pyqt学习记录

## Widget dialog layout

widget意为小组件，QWidget是一块空白块，一般qtdesignor里使用的都是xxxwidget，有特定功能，比较方便，比如Qmainwindow有菜单栏和状态栏。

dialog是特化的用户交互窗口，一般有yes、no选项，以及一些用户需要填写的信息，调用该窗口一般希望阻塞其他用户操作，逼迫其填写完毕后执行后续操作。

layout是小组件里嵌套组件的基本布局。萌新时期不懂这个作用，直接拖widget写了个窗口发现窗口禁不起拖动，因为组件坐标是绝对值，拉长之后不会重新布局。使用了layout就可以在窗口拖动后实现自动的重新布局，虽然可能效果不理想，需要进一步微调，但起码不至于离谱到找不到了。

## 坐标系

在实现graphics一系列操作时不可避免地涉及到坐标系，pyqt总共有三个坐标系。

- 视图坐标（view coordinates），显示器物理坐标。所有小组件（widget）都使用这个坐标，即坐标原点在窗口左上角，y轴正方向向下。这是一个比较符合计算机书写逻辑的坐标系（参照excel表格），这个时候窗口大小也比较好表示，就是右下角坐标值。
- 场景坐标（scene coordinates），场景逻辑坐标。这是为了方便场景表示而采用的坐标系，即在qgraphicsscene中，坐标原点可以不是左上角（但是y轴还是朝下），程序员可以自定义取景框，取景框大小也不一定需要与视图大小一致，即支持放缩。场景中的顶层物体基于这个坐标系存储位置，与视图坐标之间存在转换矩阵。
- 图元坐标（item coordinates），图元逻辑坐标。为了方便图元之间实现嵌套表示而采用的坐标系，与场景坐标之间存在一个变换。嵌套的图元采用这个坐标系存储位置。

## Model/view模型

[model / view programming](https://doc.qt.io/qt-5/model-view-programming.html)

### 简介

MVC模型分离了数据、视图和操作，在Qt里简化成了M/V模型。具体到项目中遇到了一份数据两种形式显示的问题，虽然使用成熟的widget组件也可以轻松完成，但是数据需要存两份，同步起来不方便，也不利于后续数据库扩展（maybe），另外也是为了练手，采用model/view模型。

这里model/view虽然本意是一个model对应多个view，但是项目中两个view差异过大，不太容易用一个model表示，故写了两个model（数据还是只有一份，model可以看做基本数据操作模型）

![modelview-overview](https://raw.githubusercontent.com/lxambulance/cloudimg/master/img/modelview-overview.png?token=AGF5OL5FNAG3UCNCZGLSOSLAUINEK)

Qt中model都是根据QAbstractItemModel这个抽象类继承而来，该类定义了基本的视图或代理访问数据的接口，数据没有必要直接存在model里（就可以很方便的改写接数据库），而是由数据结构、分离的类、文件、数据库或其他应用组件完成。

Qt提供三种基本的视图，QListView、QTreeView和QTableView，使得用户可以定义少量的函数就直接使用。

### 代理模型

简单来说就是遇到类似选择、排序和过滤等操作时，通过一层叠加的模型可以比较方便实现。（没有具体了解，或许项目中两个视图显示一份数据可以通过代理模型过滤）

### 代表

代表delegate用于处理一些实时的渲染逻辑，比如重写paint()函数实现进度条加载。目前项目中只在进度条这用到了。简单阅读了文档，还可以做一些简单的功能例如编辑等操作。

### 图形视图结构

类似于模型视图结构，不过这次的模型是图元，相对来说比model复杂一点，因为要考虑显示。使用图形视图结构的好处在于

- 提供了快速的接口管理大量的图元
- 可以传递事件到每个具体选择的图元
- 统一管理图元的状态信息，比如选择和关注（focus不知道怎么翻译，具体意思就是获取键盘控制权）
- 提供渲染转换函数，方便输出

题外话：Qt提供了四种类用于处理图像信息：QImage、QPixmap、QBitmap和QPicture。QImage是设计用于优化读写以及直接的像素级访问和操作，QPixmap是设计用于优化屏幕显示，QBitmap是一个继承于QPixmap且每个像素只有0/1的简单图像，QPixture是跟随画图类定义的一个用于执行画图操作的类。

## 扩展数据信号

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

## 多线程与进程

具体参考[PyQt5 tutorial](https://www.mfitzp.com/courses/pyqt/)

本项目参考上述教程，直接将新建线程的操作抽象为新建一个worker类，然后通过信号绑定的操作实现线程之间的内容交互。

## qt中exec_和show的区别

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

## sizePolicy

以下为qt widget基本的大小扩展策略，其余一些为以下的组合，多数时候不需要关心这个，只要正确使用了layout和widget的嵌套，qt会自动排布。只有当自动排布不太合适的时候才应该考虑这个。项目中在qdockwidget中用到了，因为位置太窄了，插入listwidget只能选水平空间ignore，有多少占用多少。

| `QSizePolicy::GrowFlag`   | `1`  | The widget can grow beyond its size hint if necessary.       |
| ------------------------- | ---- | ------------------------------------------------------------ |
| `QSizePolicy::ExpandFlag` | `2`  | The widget should get as much space as possible.             |
| `QSizePolicy::ShrinkFlag` | `4`  | The widget can shrink below its size hint if necessary.      |
| `QSizePolicy::IgnoreFlag` | `8`  | The widget's size hint is ignored. The widget will get as much space as possible. |
