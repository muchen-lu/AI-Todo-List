from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from src.cloud.authentication import pairing_code
from src.cloud.line_notifier import reply_user
from src.shared.config import get_settings

settings = get_settings()

app = FastAPI()

handler = WebhookHandler(settings.line_channel_secret)


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "alive"}


@app.post("/linebot/callback")
async def callback(request: Request, background_tasks: BackgroundTasks, x_line_signature: str = Header(None)):
    if not x_line_signature:
        raise HTTPException(400, "Miss X-Line-Signature header")

    body = await request.body()
    str_body = body.decode("utf-8")

    try:
        background_tasks.add_task(handler.handle, str_body, x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(400, "Invalid signature")

    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_id = event.source.user_id
    message_text = event.message.text
    reply_token = event.reply_token

    if len(message_text.strip()) == 6:
        result = pairing_code(message_text.strip(), user_id)
        if result:
            reply_user(user_id, "pair", reply_token, message="恭喜綁定成功！請回到電腦進行其餘設定")
        else:
            reply_token(
                user_id, "pair", reply_token, message="綁定失敗，驗證碼可能已過期或不存在，請回電腦重新生成驗證碼"
            )
