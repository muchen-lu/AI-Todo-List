import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler
from typing import Literal
import pytz

load_dotenv()

from src.shared.models import TodoItem
from src.cloud.line_notifier import send_line_notification
from src.shared.database_manager import push_task, get_tasks
from src.shared.ai_client import suggest_tasks
from src.cloud.calendar_catcher import get_calendar_events

temp_task = []

def main(timing: Literal["morning", "night"]) :
    global temp_task
    if timing == "night" :
        existing_tasks = get_tasks()
        todo = suggest_tasks(existing_tasks, get_calendar_events())
        temp_task = todo
        if todo :
            send_line_notification(todo, "night")
    else :
        if temp_task :
            send_line_notification(temp_task, "morning")

if __name__ == "__main__" :
    tw_tz = pytz.timezone('Asia/Taipei')
    scheduler = BlockingScheduler(timezone=tw_tz)
    scheduler.add_job(lambda: main("morning"), trigger="cron", day_of_week="mon-sat", hour=7, minute=0)
    scheduler.add_job(lambda: main("night"), trigger="cron", day_of_week="0-4, 6", hour=22, minute=0)
    scheduler.start()