import firebase_admin
from firebase_admin import credentials, db
import os
from models import TodoItem

cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': os.getenv("DATABASE_URL")
})
ref = db.reference('/')

def push_data(data: TodoItem) :
    """將資料推送上資料庫

    Args:
        data (TodoItem): 資料本體，以 TodoItem 資料建模處理
    """
    try :
        ref.child(data.id).set({"title": data.title, "deadline": data.deadline, "subtasks": [subtask.__dict__ for subtask in data.subtasks] if data.subtasks else None})
    except Exception as e :
        raise Exception(f"推送上資料庫失敗：{e}")

def get_data() -> list[TodoItem] :
    """從資料庫獲取資料

    Returns:
        list[TodoItem]: 資料列表，以 TodoItem 資料建模處理
    """
    try :
        data = ref.get()
        if data is None :
            return []
        return [TodoItem(id=key, title=value["title"], deadline=value["deadline"]) for key, value in data.items()]
    except Exception as e :
        raise Exception(f"從資料庫獲取資料失敗：{e}")