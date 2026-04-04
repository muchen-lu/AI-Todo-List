import sys
from dotenv import load_dotenv
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction

load_dotenv()

from ui import ModernTaskUI, HotkeySignal, TaskCatchConfirmationUI
from models import TodoItem
from line_notifier import send_line_notification
from task_catcher import get_classroom, get_ono
from database_manager import push_data, get_data
import keyboard
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from ai_client import generate_subtasks


def create_tray(app, window):
    # 1. 初始化託盤圖示
    # 讀取你指定的 ./icon.ico
    icon = QIcon("./icon.png")
    tray = QSystemTrayIcon(icon, app)
    tray.setToolTip("今日 5 件事 - 任務助理")

    # 2. 建立右鍵選單
    menu = QMenu()

    # 喚醒動作
    wake_action = QAction("喚醒介面 (Alt+T)", menu)
    wake_action.triggered.connect(lambda: (window.showNormal(), window.activateWindow()))
    
    # 退出動作
    exit_action = QAction("完全退出程式", menu)
    exit_action.triggered.connect(app.quit)

    menu.addAction(wake_action)
    menu.addSeparator() # 分隔線
    menu.addAction(exit_action)

    # 3. 將選單設定給託盤並顯示
    tray.setContextMenu(menu)
    tray.show()

    # 4. 監聽圖示點擊事件 (例如左鍵點擊直接喚醒)
    def on_tray_icon_activated(reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger: # 左鍵點擊
            window.showNormal()
            window.activateWindow()

    tray.activated.connect(on_tray_icon_activated)
    
    return tray

confirme_window = None

def main() :
    global confirme_window
    existing_tasks = get_data()
    
    existing_titles = {task.title for task in existing_tasks}
    
    catched_tasks = get_classroom() + get_ono()
    new_tasks = [task for task in catched_tasks if task.title not in existing_titles]
    
    confirm_window = TaskCatchConfirmationUI(new_tasks)
    confirm_window.show()
    
    def process_task(tasks: list[TodoItem]) :
        for task in tasks :
            if task["should_split"] :
                subtasks = generate_subtasks(task["task"])
                task["task"].subtasks = subtasks
            push_data(task["task"])
    
    confirm_window.confirmed_tasks.connect(lambda tasks: process_task(tasks))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 確保關閉視窗時程式不會真的退出，而是留在託盤
    app.setQuitOnLastWindowClosed(False)

    window = ModernTaskUI()
    
    # 初始化系統託盤
    tray_icon = create_tray(app, window)
    
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: main(), trigger="cron", hour=7, minute=0)
    scheduler.add_job(lambda: main(), trigger="cron", hour=20, minute=0)
    scheduler.start()

    # 快捷鍵邏輯 (Alt+T)
    hotkey_signal = HotkeySignal()
    hotkey_signal.triggered.connect(lambda: (window.showNormal(), window.activateWindow()))
    keyboard.add_hotkey("alt+t", lambda: hotkey_signal.triggered.emit())

    # main()
    sys.exit(app.exec())