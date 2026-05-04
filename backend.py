import os
import re
from dotenv import load_dotenv
import datetime

load_dotenv()

from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, PostbackEvent, TextMessageContent
from urllib.parse import parse_qs
from database_manager import delete_task, get_tasks, push_history
from line_notifier import reply_user

configuration = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
app = Flask(__name__)

COMPLETE_PATTERN = re.compile(r"^完成「(.+)」了！$")

def get_history_file() :
    now = datetime.datetime.now()
    year = now.year
    month = now.month
    match month :
        case month if month in [1, 2, 3] :
            return f"{year}_Q1"
        case month if month in [4, 5, 6] :
            return f"{year}_Q2"
        case month if month in [7, 8, 9] :
            return f"{year}_Q3"
        case month if month in [10, 11, 12] :
            return f"{year}_Q4"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try :
        handler.handle(body, signature)
    except InvalidSignatureError :
        abort(400)
    return "OK"

@handler.add(PostbackEvent)
def handle_postback(event) :
    reply_token = event.reply_token
    data = event.postback.data
    params = {key: value[0] for key, value in parse_qs(data).items()}
    
    action = params.get("action")
    task_id = params.get("task")
    subtask_id = params.get("subtask", None)
    
    task = get_tasks(task_id=task_id)[0]
    
    if action == "complete" :
        print(f"完成任務：{task.title}，預期點數：{task.expect_point}，任務 ID：{task_id}，子任務 ID：{subtask_id}")
        reply_user("task", reply_token, title = task.title, expect_point = task.expect_point, task_id = task_id, subtask_id = subtask_id)
    elif action == "reply" :
        used_point = max(0, min(10, int(task.expect_point) + int(params.get("offset", 0)))) # 確保最終的 used_point 在 0~10 之間
        push_history(get_history_file(), {"task": task.title, "used_point": used_point})
        delete_task(task_id, subtask_id)

# TODO: 未來拿來做使用者的隨手提醒功能
# @handler.add(MessageEvent, message=TextMessageContent)
# def handle_message(event) :

if __name__ == "__main__" :
    app.run(host="0.0.0.0", port=5000)