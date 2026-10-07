import firebase_admin
from firebase_admin import credentials, db
import os
from dotenv import load_dotenv

load_dotenv()

from src.shared.models import TodoItem, SubtaskItem

if os.path.exists("firebase_key.json") :
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': os.getenv("DATABASE_URL")
    })
else :
    firebase_admin.initialize_app(options={'databaseURL': os.getenv("DATABASE_URL")})
ref = db.reference('/')

def push_task(data: TodoItem) :
    """將資料推送上資料庫

    Args:
        data (TodoItem): 資料本體，以 TodoItem 資料建模處理
    """
    try :
        ref.child("tasks").child(data.id).set({"title": data.title, "deadline": data.deadline, "estimate_data": data.estimate_data.model_dump(), "subtasks": [subtask.__dict__ for subtask in data.subtasks] if data.subtasks else None})
    except Exception as e :
        raise Exception(f"推送上資料庫失敗：{e}")

def get_tasks(task_id: str = None) -> list[TodoItem] :
    """從資料庫獲取資料
    Args:
        task_id (str, optional): 任務 ID，作為資料庫中的識別指標，預設為 None，表示獲取所有資料

    Returns:
        list[TodoItem]: 資料列表，以 TodoItem 資料建模處理
    """
    # TODO: 這裡需要實作從父任務 ID 抓到子任務 ID 的邏輯
    try :
        if task_id is not None :
            data = ref.child("tasks").child(task_id).get()
            if data is None :
                return []
            return [TodoItem(id=task_id, title=data["title"], deadline=data.get("deadline"), estimate_data=data.get("estimate_data"), subtasks=[SubtaskItem(id=subtask_id, title=subtask.get("title"), deadline=subtask.get("deadline")) for subtask_id, subtask in (data.get("subtasks") or {}).items()])]
        else :
            data = ref.child("tasks").get()
            if data is None :
                return []
            return [TodoItem(id=task_id, title=data["title"], deadline=data.get("deadline"), estimate_data=data.get("estimate_data"), subtasks=[SubtaskItem(id=subtask_id, title=subtask.get("title"), deadline=subtask.get("deadline")) for subtask_id, subtask in (data.get("subtasks") or {}).items()]) for task_id, data in data.items()]
    except Exception as e :
        raise Exception(f"從資料庫獲取資料失敗：{e}")

def delete_task(task_id: str, subtask_id: str = None) :
    """從資料庫刪除資料

    Args:
        task_id (str): 任務 ID，作為資料庫中的識別指標
        subtask_id (str, optional): 子任務 ID，作為資料庫中的識別指標
    """
    try :
        if subtask_id is not None :
            ref.child("tasks").child(task_id).child("subtasks").child(subtask_id).delete()
        else :
            ref.child("tasks").child(task_id).delete()
    except Exception as e :
        raise Exception(f"從資料庫刪除資料失敗：{e}")

def push_history(file: str, data: dict) :
    """將資料推送上歷史紀錄檔

    Args:
        file (str): 歷史紀錄檔的路徑
        data (dict): 資料本體，以字典形式處理
    """
    try :
        ref.child("history").child(file).set(data)
    except Exception as e :
        raise Exception(f"推送上資料庫失敗：{e}")

def get_history(file: str) -> dict :
    """從資料庫獲取歷史紀錄

    Args:
        file (str): 歷史紀錄檔的路徑

    Returns:
        dict: 歷史紀錄，以字典形式處理
    """
    try :
        data = ref.child("history").child(file).get()
        if data is None :
            return {}
        return data
    except Exception as e :
        raise Exception(f"從資料庫獲取資料失敗：{e}")

if __name__ == "__main__" :
    print(get_tasks())