import os
import re
import datetime
from urllib.parse import parse_qs
from dotenv import load_dotenv

from fastapi import FastAPI, Request, Header, HTTPException, BackgroundTasks
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, PostbackEvent, TextMessageContent
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2

# 假設這些是你原本的自訂模組
from src.shared.database_manager import delete_task, get_tasks, push_history
from src.cloud.line_notifier import reply_user, send_reminder
from src.shared.models import CompleteData, ActualData, ReminderItem
from src.shared.ai_client import analyze_intent

load_dotenv()

app = FastAPI()

configuration = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

COMPLETE_PATTERN = re.compile(r"^完成「(.+)」了！$")
SERVER_URL = os.getenv("SERVER_URL")
PROJECT_ID = os.getenv("PROJECT_ID")

def get_history_file():
    now = datetime.datetime.now()
    year = now.year
    month = now.month
    if month in [1, 2, 3]:
        return f"{year}_Q1"
    elif month in [4, 5, 6]:
        return f"{year}_Q2"
    elif month in [7, 8, 9]:
        return f"{year}_Q3"
    elif month in [10, 11, 12]:
        return f"{year}_Q4"

def schedule_reminder(task_title: str, reminder_time: str) :
    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(PROJECT_ID, "us-central1", "line-reminders")
    target_url = f"{SERVER_URL}/reminders"
    
    reminder_time = datetime.datetime.fromisoformat(reminder_time)
    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": target_url,
            "headers": {"Content-Type": "application/json"},
            "body": f'{{"task_title": "{task_title}"}}'.encode(),
        },
        "schedule_time": timestamp_pb2.Timestamp(seconds=int(reminder_time.timestamp())),
    }
    client.create_task(request={"parent": parent, "task": task})

@app.post("/reminders")
async def execute_reminder(request: Request, payload: dict) :
    send_reminder(message = f"提醒你～要記得{payload['task_title']}喔！")

@app.post("/callback")
async def callback(request: Request, background_tasks: BackgroundTasks, x_line_signature: str = Header(None)):
    if not x_line_signature:
        raise HTTPException(status_code=400, detail="Missing X-Line-Signature header")

    body = await request.body()
    body_str = body.decode("utf-8")
    
    try:
        # 將 Line Webhook 處理移至背景執行，確保 API 能在 1 秒內回傳 200 OK
        background_tasks.add_task(handler.handle, body_str, x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
        
    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    message_text = event.message.text
    reply_token = event.reply_token
    
    intent_datas = analyze_intent(message_text)
    for intent in intent_datas :
        match intent["intent"] : #TODO: task 和 schedule 之後再做
            case "reminder" :
                data = ReminderItem(
                    content=intent["content"],
                    reminder=intent["reminder"],
                    location=intent["location"],
                    relativity=intent["relativity"]
                )
                if not re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", data.reminder) :
                    errors = f"{data.reminder} 指的是什麼時候呢？請用 YYYY-MM-DD HH:MM 的格式回覆我喔\n" #TODO: 這裡之後要想怎麼接回 AI 去解決時間解讀的問題
                    reply_user("reminder", reply_token, message=errors)
                    return
                message = f"我已經幫你設定好提醒囉，我會在 {data.reminder} 提醒你 {data.content}"
                reply_user("reminder", reply_token, message=message)
                #TODO: 之後要做如果 relativity 是 true 的話的多重提醒保險機制

@handler.add(PostbackEvent)
def handle_postback(event):
    reply_token = event.reply_token
    data = event.postback.data
    params = {key: value[0] for key, value in parse_qs(data).items()}
    
    action = params.get("action")
    task_id = params.get("task")
    subtask_id = params.get("subtask", None)
    
    # 增加防呆機制：確保任務存在以免觸發 IndexError
    tasks = get_tasks(task_id=task_id)
    if not tasks:
        return
    
    task = tasks[0]
    
    if action == "complete" :
        reply_user("task", reply_token, title=task.title, subtask_id=subtask_id)
        delete_task(task_id, subtask_id)
        
        # 為了提高可讀性與避免 PEP8 警告，將物件建構拆行
        actual_data = ActualData(
            task_category=task.estimate_data.task_category, 
            congnitive_load=task.estimate_data.congnitive_load, 
            actual_time=task.estimate_data.estimated_time, 
            work_mode=task.estimate_data.suggest_work_mode
        )
        
        complete_data = CompleteData(
            id=task_id, 
            title=task.title, 
            deadline=task.deadline, 
            actual_data=actual_data
        )
        
        push_history(get_history_file(), complete_data.model_dump())

if __name__ == "__main__":
    # FastAPI 使用 uvicorn 作為 ASGI 伺服器
    import uvicorn
    uvicorn.run("backend:app", host="0.0.0.0", port=5000, reload=True)