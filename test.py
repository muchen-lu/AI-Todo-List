import os
import firebase_admin
from firebase_admin import credentials, db
from dotenv import load_dotenv

# 1. 初始化與讀取環境變數
load_dotenv()
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': os.getenv("DATABASE_URL")
    })

def migrate_data_to_tasks():
    root_ref = db.reference('/')
    all_data = root_ref.get()

    if not all_data:
        print("❌ 資料庫是空的，無需遷移。")
        return

    updates = {}
    items_to_move = 0

    # 2. 準備更新字典
    for key, value in all_data.items():
        # 跳過已經在 tasks 節點下的資料，以及其他非任務的保留節點 (如 feedback)
        if key in ["tasks", "feedback"]:
            continue
        
        # 將舊路徑設為 None (代表刪除)，將新路徑設為原本的資料
        updates[f"tasks/{key}"] = value
        updates[key] = None
        items_to_move += 1

    # 3. 執行批次更新
    if updates:
        print(f"🔄 正在遷移 {items_to_move} 個項目至 /tasks ...")
        root_ref.update(updates)
        print("✅ 遷移完成！")
    else:
        print("ℹ️ 沒有需要移動的根目錄項目。")

if __name__ == "__main__":
    migrate_data_to_tasks()