import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QLabel, QDateEdit, QTimeEdit, 
    QCheckBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QDate, QTime, pyqtSignal, QObject, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from models import TodoItem, SubtaskItem

# --- 現代感通用樣式表 ---
MODERN_STYLE = """
    #Container {
        background-color: rgba(25, 25, 25, 230);
        border: 2px solid rgba(80, 120, 255, 150);
        border-radius: 15px;
    }
    QLabel { 
        color: #F0F0F0; 
        font-family: "Microsoft JhengHei"; 
        font-size: 14px; 
        font-weight: bold; 
    }
    QLineEdit, QDateEdit, QTimeEdit {
        background-color: rgba(255, 255, 255, 15);
        border: 1px solid rgba(255, 255, 255, 30);
        border-radius: 6px;
        padding: 6px;
        color: white;
    }
    QCheckBox { 
        color: #90CAF9; 
        font-size: 13px; 
    }
    QCheckBox#AISplit { 
        color: #CE93D8; 
        font-weight: bold;
    }
    QPushButton { 
        background-color: #3F51B5; 
        color: white; 
        border-radius: 8px; 
        padding: 8px; 
        font-weight: bold; 
    }
    QPushButton#CloseBtn { background-color: #D32F2F; }
    QPushButton#ConfirmBtn { background-color: #43A047; }
    
    /* 滾動條樣式 */
    QScrollBar:vertical {
        border: none;
        background: rgba(255, 255, 255, 10);
        width: 8px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical {
        background: rgba(80, 120, 255, 100);
        border-radius: 4px;
    }
"""

class HotkeySignal(QObject):
    triggered = pyqtSignal()

# --- 1. 手動新增任務介面 ---
class ModernTaskUI(QWidget):
    # 訊號：標題, 截止日, 是否啟動 AI 拆解
    task_added = pyqtSignal(str, str, bool) 

    def __init__(self):
        super().__init__()
        self.old_pos = None
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(450, 280) # 稍微調高以容納新勾選框

        self.main_layout = QVBoxLayout(self)
        self.container = QWidget()
        self.container.setObjectName("Container")
        self.container.setStyleSheet(MODERN_STYLE)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 1. 任務名稱
        task_row = QHBoxLayout()
        task_label = QLabel("🚀 任務名稱:")
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("要做什麼呢？")
        task_row.addWidget(task_label)
        task_row.addWidget(self.task_input, 1)
        layout.addLayout(task_row)

        # 2. 設定區 (截止期限 & AI 拆解)
        settings_layout = QVBoxLayout()
        
        self.has_deadline_cb = QCheckBox("設定截止期限")
        self.has_deadline_cb.setChecked(True)
        self.has_deadline_cb.toggled.connect(self.toggle_datetime_inputs)
        
        self.ai_split_cb = QCheckBox("✨ 使用 AI 自動拆解任務 (建議大型專案使用)")
        self.ai_split_cb.setObjectName("AISplit")
        
        settings_layout.addWidget(self.has_deadline_cb)
        settings_layout.addWidget(self.ai_split_cb)
        layout.addLayout(settings_layout)

        # 3. 日期與時間 (24小時制)
        dt_row = QHBoxLayout()
        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.time_input = QTimeEdit(QTime.currentTime())
        self.time_input.setDisplayFormat("HH:mm") 
        dt_row.addWidget(self.date_input)
        dt_row.addWidget(self.time_input)
        layout.addLayout(dt_row)

        # 4. 按鈕區
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

        should_split = self.ai_split_cb.isChecked()

        if self.has_deadline_cb.isChecked():
            date_str = self.date_input.date().toString("yyyy-MM-dd")
            time_str = self.time_input.time().toString("HH:mm")
            deadline = f"{date_str} {time_str}"
        else:
            deadline = None

        self.task_added.emit(title, deadline, should_split)
        self.task_input.clear()
        self.ai_split_cb.setChecked(False) # 重置勾選
        self.hide()

    # 視窗拖動邏輯
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


# --- 2. 外部任務抓取確認介面 ---
class TaskCatchConfirmationUI(QWidget):
    # 確認後發送：List[dict] 包含 title, deadline, should_split
    confirmed_tasks = pyqtSignal(list)

    def __init__(self, raw_tasks):
        super().__init__()
        self.raw_tasks = raw_tasks # 格式：[{'title': '...', 'deadline': '...'}, ...]
        self.task_rows = []
        self.old_pos = None
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(500)
        self.setMaximumHeight(600) # 防止任務太多超出螢幕

        main_vbox = QVBoxLayout(self)
        self.container = QWidget()
        self.container.setObjectName("Container")
        self.container.setStyleSheet(MODERN_STYLE)
        
        layout = QVBoxLayout(self.container)
        
        header = QLabel("🔍 偵測到新任務，請確認處理方式：")
        header.setStyleSheet("font-size: 16px; color: #81D4FA; margin-bottom: 10px;")
        layout.addWidget(header)

        # 使用滾動區域處理大量任務
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setSpacing(10)

        for task in self.raw_tasks:
            row_frame = QFrame()
            row_frame.setStyleSheet("background: rgba(255, 255, 255, 5); border-radius: 10px; border: 1px solid rgba(255,255,255,10);")
            row_layout = QHBoxLayout(row_frame)
            
            add_cb = QCheckBox("加入")
            add_cb.setChecked(True)
            
            info_vbox = QVBoxLayout()
            t_label = QLabel(task.title)
            t_label.setWordWrap(True)
            t_label.setStyleSheet("font-size: 13px; color: #FFFFFF;")
            
            d_label = QLabel(f"📅 {task.deadline or '無期限'}")
            d_label.setStyleSheet("font-size: 11px; color: #B0BEC5; font-weight: normal;")
            
            info_vbox.addWidget(t_label)
            info_vbox.addWidget(d_label)
            
            split_cb = QCheckBox("AI 拆解")
            split_cb.setObjectName("AISplit")
            
            row_layout.addWidget(add_cb)
            row_layout.addLayout(info_vbox, 1)
            row_layout.addWidget(split_cb)
            
            self.scroll_layout.addWidget(row_frame)
            self.task_rows.append({'add': add_cb, 'split': split_cb, 'data': task})

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        # 底部按鈕
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("略過全部")
        self.cancel_btn.setObjectName("CloseBtn")
        self.cancel_btn.clicked.connect(self.hide)
        
        self.confirm_btn = QPushButton("確認提交選中任務")
        self.confirm_btn.setObjectName("ConfirmBtn")
        self.confirm_btn.clicked.connect(self.submit_all)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.confirm_btn)
        layout.addLayout(btn_layout)

        main_vbox.addWidget(self.container)

    def submit_all(self) :
        self.hide()
        results = []
        for row in self.task_rows:
            if row['add'].isChecked():
                results.append({
                    'task': TodoItem(title=row['data'].title, deadline=row['data'].deadline),
                    'should_split': row['split'].isChecked()
                })
        
        if results:
            self.confirmed_tasks.emit(results)

    # 視窗拖動
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

# --- 3. loading 介面
class LoadingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 設定視窗屬性：無邊框、最上層、不顯示在工作列
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(220, 220)
        
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        
    def update_animation(self):
        # 每次旋轉 15 度
        self.angle = (self.angle + 15) % 360
        self.update() # 觸發 paintEvent 重新繪圖

    def start(self):
        self.timer.start(40) # 約 25 FPS
        self.show()
        self.center_on_screen()

    def stop(self):
        self.timer.stop()
        self.close()

    def center_on_screen(self):
        # 讓 Loading 視窗顯示在螢幕正中央
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2, 
                  (screen.height() - self.height()) // 2)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. 繪製背景外框 (與你現有的 MODERN_STYLE 色調一致)
        painter.setBrush(QColor(25, 25, 25, 240)) # 深色半透明
        painter.setPen(QPen(QColor(80, 120, 255, 150), 2)) # 藍色邊框
        painter.drawRoundedRect(self.rect().adjusted(5, 5, -5, -5), 20, 20)
        
        # 2. 繪製旋轉中的圓弧
        # 設定圓弧範圍
        spinner_rect = QRectF(60, 45, 100, 100)
        pen = QPen(QColor(129, 212, 250)) # 天藍色
        pen.setWidth(6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap) # 讓弧線末端圓潤
        painter.setPen(pen)
        
        # 繪製一段 120 度的弧線，角度隨 self.angle 變化
        # 注意：drawArc 的角度單位是 1/16 度
        painter.drawArc(spinner_rect, -self.angle * 16, 120 * 16)
        
        # 3. 繪製中間文字
        painter.setPen(QColor("#F0F0F0"))
        painter.setFont(QFont("Microsoft JhengHei", 12, QFont.Weight.Bold))
        # 文字稍微往下偏移一點，不要擋到圓弧中心
        painter.drawText(self.rect().adjusted(0, 150, 0, 0), Qt.AlignmentFlag.AlignHCenter, "任務抓取中...")

# --- 測試代碼 ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 測試手動輸入介面
    # window = ModernTaskUI()
    # window.show()
    
    # 測試確認抓取介面
    test_tasks = [
        {'title': '數學 1-1 非同步筆記', 'deadline': '2026-04-03 23:59'},
        {'title': '鹿港乘桴記課文研讀', 'deadline': '2026-04-05 12:00'},
        {'title': '製作期末專案報告 (大型)', 'deadline': '2026-04-20 17:00'}
    ]
    confirm_win = TaskCatchConfirmationUI(test_tasks)
    confirm_win.show()
    
    sys.exit(app.exec())