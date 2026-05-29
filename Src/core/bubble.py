"""
气泡渲染 - 独立窗口模式（左上角，连接线指向角色）
"""
from PySide6.QtWidgets import QLabel, QFrame, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QFont, QPainter, QColor, QPen

class BubbleWindow(QFrame):
    """独立的半透明气泡窗口，带连接线指向桌宠"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 240);
                border: 1px solid #ffb6c1;
                border-radius: 10px;
                padding: 6px;
            }
            QLabel {
                color: #333;
                font-size: 13px;
                background: transparent;
                padding: 2px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setMaximumWidth(180)
        self.label.setFont(QFont('Microsoft YaHei', 11))
        layout.addWidget(self.label)

        self._timer = QTimer()
        self._timer.timeout.connect(self.hide)
        self._parent_pos = QPoint(0, 0)

    def show_text(self, text: str, duration_ms: int = 3000, parent_pos: QPoint = None, lang: str = "auto"):
        """根据语种设置切换字体"""
        import re
        # 根据 lang 参数选择字体
        if lang == "zh":
            self.label.setFont(QFont('Microsoft YaHei', 11))
        elif lang == "ja":
            self.label.setFont(QFont('Yu Gothic UI', 11))
        elif lang == "en":
            self.label.setFont(QFont('Segoe UI', 11))
        else:
            # auto: 根据文本内容检测
            if re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text):
                self.label.setFont(QFont('Yu Gothic UI', 11))
            elif re.search(r'[\u4e00-\u9fff]', text):
                self.label.setFont(QFont('Microsoft YaHei', 11))
            else:
                self.label.setFont(QFont('Segoe UI', 11))

        self.label.setText(text)
        self.adjustSize()

        if parent_pos:
            self._parent_pos = parent_pos
            # 气泡在桌宠左上方
            bw = self.width()
            bh = self.height()
            px, py = parent_pos.x(), parent_pos.y()
            # 气泡定位：(桌宠x - 气泡宽 - 10, 桌宠y - 10)
            bx = px - bw - 10
            by = py - 10
            self.move(bx, by)

        self.show()
        self.raise_()
        self.update()  # 触发paintEvent画连接线

        if duration_ms > 0:
            self._timer.start(duration_ms)

    def paintEvent(self, event):
        super().paintEvent(event)
        # 画连接线：从气泡右下角到桌宠左上角
        if self.isVisible():
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor(255, 182, 193, 180), 2)
            p.setPen(pen)

            # 气泡右下角
            x1 = self.width()
            y1 = self.height()
            # 桌宠左上角（相对气泡坐标）
            px, py = self._parent_pos.x(), self._parent_pos.y()
            x2 = px - self.x()
            y2 = py - self.y()

            p.drawLine(x1, y1, x2, y2)
            # 小圆点装饰在桌宠端
            p.setBrush(QColor(255, 182, 193, 180))
            p.drawEllipse(QPoint(x2, y2), 3, 3)
