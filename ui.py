import sys
import keyboard
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QLabel, QDateEdit, QTimeEdit, QCheckBox
)
from PyQt6.QtCore import Qt, QDate, QTime, pyqtSignal, QObject

class HotkeySignal(QObject):
    triggered = pyqtSignal()

class ModernTaskUI(QWidget):
    task_added = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.old_pos = None

    def init_ui(self):
        # 視窗屬性設定
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(450, 250) # 寬度稍微增加以利標題併行

        self.main_layout = QVBoxLayout(self)
        self.container = QWidget()
        self.container.setObjectName("Container")
        
        # 現代感 QSS 樣式
        self.setStyleSheet("""
            #Container {
                background-color: rgba(25, 25, 25, 230);
                border: 2px solid rgba(80, 120, 255, 150);
                border-radius: 15px;
            }
            QLabel { color: #F0F0F0; font-family: "Microsoft JhengHei"; font-size: 14px; font-weight: bold; }
            QLineEdit, QDateEdit, QTimeEdit {
                background-color: rgba(255, 255, 255, 15);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 6px;
                padding: 6px;
                color: white;
            }
            QCheckBox { color: #90CAF9; font-size: 12px; }
            QPushButton { background-color: #3F51B5; color: white; border-radius: 8px; padding: 8px; font-weight: bold; }
            QPushButton#CloseBtn { background-color: #D32F2F; }
        """)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 1. 任務名稱與輸入框 (同一行)
        task_row = QHBoxLayout()
        task_label = QLabel("🚀 任務名稱:")
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("要做什麼呢？")
        task_row.addWidget(task_label)
        task_row.addWidget(self.task_input, 1) # 1 代表輸入框會自動拉伸
        layout.addLayout(task_row)

        # 2. 截止期限勾選與日期時間 (整合在同一行或分層)
        time_control_layout = QVBoxLayout()
        
        self.has_deadline_cb = QCheckBox("設定截止期限")
        self.has_deadline_cb.setChecked(True)
        self.has_deadline_cb.toggled.connect(self.toggle_datetime_inputs)
        time_control_layout.addWidget(self.has_deadline_cb)

        # 日期與時間並排 (24小時制)
        dt_row = QHBoxLayout()
        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        
        # 設定為 24 小時制 (HH:mm)
        self.time_input = QTimeEdit(QTime.currentTime())
        self.time_input.setDisplayFormat("HH:mm") 
        
        dt_row.addWidget(self.date_input)
        dt_row.addWidget(self.time_input)
        time_control_layout.addLayout(dt_row)
        
        layout.addLayout(time_control_layout)

        # 3. 按鈕區
        btn_layout = QHBoxLayout()
        self.close_btn = QPushButton("取消")
        self.close_btn.setObjectName("CloseBtn")
        self.close_btn.clicked.connect(self.hide)
        
        self.add_btn = QPushButton("確認新增")
        self.add_btn.clicked.connect(self.submit_task)
        
        btn_layout.addWidget(self.close_btn)
        btn_layout.addWidget(self.add_btn)
        layout.addLayout(btn_layout)

        self.main_layout.addWidget(self.container)

    def toggle_datetime_inputs(self, checked):
        self.date_input.setEnabled(checked)
        self.time_input.setEnabled(checked)

    def submit_task(self):
        title = self.task_input.text().strip()
        if not title: return

        if self.has_deadline_cb.isChecked():
            date_str = self.date_input.date().toString("yyyy-MM-dd")
            time_str = self.time_input.time().toString("HH:mm")
            deadline = f"{date_str} {time_str}"
        else:
            deadline = None

        self.task_added.emit(title, deadline)
        self.task_input.clear()
        self.hide()

    # 滑鼠拖動
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()
    def mouseMoveEvent(self, event):
        if self.old_pos is not None:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()
    def mouseReleaseEvent(self, event):
        self.old_pos = None