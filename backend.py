import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, PostbackEvent, TextMessageContent
from urllib.parse import parse_qs
from database_manager import delete_data

configuration = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
app = Flask(__name__)

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
    data = event.postback.data
    params = {key: value[0] for key, value in parse_qs(data).items()}
    
    action = params.get("action")
    task_id = params.get("task")
    subtask_id = params.get("subtask")
    
    if action == "complete" :
        if subtask_id :
            delete_data(task_id, subtask_id)
        else :
            delete_data(task_id)

if __name__ == "__main__" :
    app.run(host="0.0.0.0", port=5000)