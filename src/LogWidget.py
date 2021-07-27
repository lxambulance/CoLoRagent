# coding=utf-8


from typing import Tuple
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtCore import (
    Qt, QParallelAnimationGroup, QPropertyAnimation, pyqtSlot, QAbstractAnimation)
from PyQt5.QtWidgets import (
    QToolButton, QWidget, QScrollArea, QSizePolicy, QFrame, QVBoxLayout, QLabel)


class CollapsibleMessageBox(QWidget):
    ''' docstring: 消息显示类，按钮触发折叠 '''
    
    def __init__(self, Title="", parent=None, defaultLayout=False, Message=None):
        super().__init__(parent)

        self.toggle_button = QToolButton(text=Title, checkable=True, checked=False)
        self.toggle_button.setStyleSheet("QToolButton { border: none; }")
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.RightArrow)
        self.toggle_button.pressed.connect(self.on_pressed)

        self.toggle_animation = QParallelAnimationGroup(self)

        self.content_area = QScrollArea(maximumHeight=0, minimumHeight=0)
        self.content_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.content_area.setFrameShape(QFrame.NoFrame)

        lay = QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)

        self.toggle_animation.addAnimation(QPropertyAnimation(self, b"minimumHeight"))
        self.toggle_animation.addAnimation(QPropertyAnimation(self, b"maximumHeight"))
        self.toggle_animation.addAnimation(QPropertyAnimation(self.content_area, b"maximumHeight"))

        if defaultLayout:
            lay = QVBoxLayout()
            self.text = QLabel()
            pa = QPalette()
            pa.setColor(pa.Background, Qt.white)
            pa.setColor(pa.Foreground, Qt.black)
            self.text.setAutoFillBackground(True)
            self.text.setPalette(pa)
            self.text.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.text.setTextFormat(Qt.MarkdownText)
            self.text.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
            self.text.setWordWrap(True)
            if not Message:
                Message = '空'
            self.text.setText(Message+'\n')
            lay.addWidget(self.text)
            self.setContentLayout(lay)

    @pyqtSlot()
    def on_pressed(self):
        ''' docstring: 按钮函数，设置动画参数并触发 '''
        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(Qt.DownArrow if not checked else Qt.RightArrow)
        self.toggle_animation.setDirection(QAbstractAnimation.Forward if not checked else QAbstractAnimation.Backward)
        self.toggle_animation.start()

    def setContentLayout(self, layout):
        ''' docstring: 重新设置布局，并计算按钮动画参数 '''
        lay = self.content_area.layout()
        del lay
        self.content_area.setLayout(layout)
        collapsed_height = (self.sizeHint().height() - self.content_area.maximumHeight())
        content_height = layout.sizeHint().height()
        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(500)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + content_height)
        content_animation = self.toggle_animation.animationAt(self.toggle_animation.animationCount() - 1)
        content_animation.setDuration(500)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)


class LogWidget(QWidget):
    ''' docstring: 统一处理和显示折叠消息盒 '''

    def __init__(self, parent = None):
        super().__init__(parent)
        self.lay = QVBoxLayout(self)
        self.scrollarea = QScrollArea()
        self.lay.addWidget(self.scrollarea)
        self.content = QWidget()
        self.scrollarea.setWidget(self.content)
        self.scrollarea.setWidgetResizable(True)

        self.contentarea = QVBoxLayout(self.content)
        self.contentarea.addStretch()

        # 设置区间范围改变信号
        self.scrollarea.verticalScrollBar().rangeChanged.connect(self.modifyBarValue)

    def modifyBarValue(self, min, max):
        if self.modifytime:
            bar = self.scrollarea.verticalScrollBar()
            bar.setValue(max)
            self.modifytime -= 1
            # print(bar.maximum(), bar.minimum(), bar.value(), self.modifytime)

    def addLog(self, title, message, flag=False):
        ''' docstring: 添加日志消息，默认选项卡关闭 '''
        index = self.contentarea.count()
        box = CollapsibleMessageBox(Title=title, defaultLayout=True, Message=message)
        self.contentarea.insertWidget(index - 1, box)
        if flag:
            box.toggle_button.animateClick()
        self.modifytime=1


if __name__ == "__main__":
    import sys
    import random
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication, QMainWindow, QDockWidget
    import qdarkstyle as qds

    app = QApplication(sys.argv)
    app.setStyleSheet(qds.load_stylesheet_pyqt5())
    w = QMainWindow()
    lx = LogWidget()
    w.setCentralWidget(lx)

    vlay = lx.contentarea
    for i in range(10):
        box = CollapsibleMessageBox(f"Collapsible Box Header-{i}")
        vlay.insertWidget(vlay.count()-1, box)

        lay = QVBoxLayout()
        for j in range(8):
            label = QLabel(f"{j}")
            color = QColor(*[random.randint(0, 255) for _ in range(3)])
            label.setStyleSheet(f"background-color: {color.name()}; color : white;")
            label.setAlignment(Qt.AlignCenter)
            lay.addWidget(label)
        box.setContentLayout(lay)
    
    box = CollapsibleMessageBox(
        Title="Message Box Header<add>",
        defaultLayout=True,
        Message="Hello World!"*10
    )
    vlay.insertWidget(vlay.count()-1, box)
    for i in range(100):
        lx.addLog(f"{i}",f"{i*i}")

    w.resize(640, 480)
    w.show()
    sys.exit(app.exec_())
