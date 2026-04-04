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

def delete_data(task_id: str, subtask_id: str = None) :
    """從資料庫刪除資料

    Args:
        task_id (str): 任務 ID，作為資料庫中的識別指標
        subtask_id (str, optional): 子任務 ID，作為資料庫中的識別指標
    """
    try :
        if subtask_id is not None :
            ref.child(task_id).child("subtasks").child(subtask_id).delete()
        else :
            ref.child(task_id).delete()
    except Exception as e :
        raise Exception(f"從資料庫刪除資料失敗：{e}")