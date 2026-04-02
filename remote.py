import os
from dotenv import load_dotenv
from models import TodoItem
from line_notifier import send_line_notification
from task_catcher import get_classroom, get_ono
from database_manager import push_data, get_data

load_dotenv()

def main() :
    existing_tasks = get_data()
    existing_titles = {task.title for task in existing_tasks}
    
    catched_tasks = get_classroom() + get_ono()
    new_tasks = [task for task in catched_tasks if task.title not in existing_titles]
    