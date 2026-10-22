from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from src.cloud.authentication import pairing_code
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
    # reply_token = event.reply_token

    if len(message_text.strip()) == 6:
        pairing_code(message_text.strip(), user_id)
