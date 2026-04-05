import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler
from typing import Literal
import pytz

load_dotenv()

from models import TodoItem
from line_notifier import send_line_notification
from database_manager import push_data, get_data
from ai_client import get_5_tasks

temp_task = [TodoItem(id="temp", title="暫存任務", deadline=None)]

def main(timing: Literal["morning", "night"]) :
    global temp_task
    if timing == "night" :
        existing_tasks = get_data()
        todo = get_5_tasks(existing_tasks)
        todo = [TodoItem(id=task.id, title=task.title, deadline=task.deadline) for task in todo]
        temp_task = todo
        send_line_notification(todo, "night")
    else :
        send_line_notification(temp_task, "morning")

if __name__ == "__main__" :
    tw_tz = pytz.timezone('Asia/Taipei')
    scheduler = BlockingScheduler(timezone=tw_tz)
    scheduler.add_job(lambda: main("morning"), trigger="cron", hour=7, minute=0)
    scheduler.add_job(lambda: main("night"), trigger="cron", hour=22, minute=0)
    scheduler.start()