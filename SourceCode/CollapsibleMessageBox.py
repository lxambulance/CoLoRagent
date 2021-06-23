# coding=utf-8


from PyQt5.QtGui import QColor
from PyQt5.QtCore import (
    Qt, QParallelAnimationGroup, QPropertyAnimation, pyqtSlot, QAbstractAnimation)
from PyQt5.QtWidgets import (
    QTextEdit, QToolButton, QWidget, QScrollArea, QSizePolicy, QFrame, QVBoxLayout, QLabel)


class CollapsibleMessageBox(QWidget):
    ''' docstring: 消息显示类，开关触发折叠 '''
    
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
            self.text.setTextFormat(Qt.MarkdownText)
            self.text.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
            self.text.setWordWrap(True)
            if not Message:
                Message = '空'
            self.text.setText(Message)
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


if __name__ == "__main__":
    import sys
    import random
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication, QMainWindow, QDockWidget

    app = QApplication(sys.argv)
    w = QMainWindow()
    w.setCentralWidget(QWidget())

    dock = QDockWidget("Collapsible Demo")
    w.addDockWidget(Qt.LeftDockWidgetArea, dock)

    scroll = QScrollArea()
    dock.setWidget(scroll)

    content = QWidget()
    scroll.setWidget(content)
    scroll.setWidgetResizable(True)
    vlay = QVBoxLayout(content) # 可以直接设置parent，或者最后通过setLayout函数添加

    for i in range(10):
        box = CollapsibleMessageBox(f"Collapsible Box Header-{i}")
        vlay.addWidget(box)

        lay = QVBoxLayout()
        for j in range(8):
            label = QLabel(f"{j}")
            color = QColor(*[random.randint(0, 255) for _ in range(3)])
            label.setStyleSheet(f"background-color: {color.name()}; color : white;")
            label.setAlignment(Qt.AlignCenter)
            lay.addWidget(label)
        box.setContentLayout(lay)
    
    box = CollapsibleMessageBox(
        Title=f"Message Box Header<add>",
        defaultLayout=True,
        Message="Hello World!"*10
    )
    vlay.addWidget(box)

    vlay.addStretch() # 添加松紧条（designer弹簧），便于其他对齐

    w.resize(640, 480)
    w.show()
    sys.exit(app.exec_())
