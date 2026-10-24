from typing import Literal

from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.messaging.rest import ApiException

from src.shared.config import get_settings
from src.shared.logger import logger

settings = get_settings()

LINE_CHANNEL_ACCESS_TOKEN = settings.line_channel_access_token
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
line_bot = MessagingApi(ApiClient(configuration))


def reply_user(user_id: str, mode: Literal["task", "reminder", "pair"], reply_token: str, **kargs):
    match mode:
        case "pairing":
            message: str = kargs.get("message")
            if message == "" or message is None:
                logger.error("In pair mode, must give message valuable.")
                raise ValueError("No require valuable.")
            text_message: TextMessage = TextMessage(text=message)

    try:
        request = ReplyMessageRequest(reply_token=reply_token, messages=[text_message])
        line_bot.reply_message(request)
    except ApiException as e:
        match e.status:
            case 400:
                logger.error("Wrong Line message format or invalid replyToken")
            case 429:
                logger.warning("Reach Line API Limit")
            case _:
                logger.error(f"Unknown Line API Error {e.status}: {e.body}")
    except Exception:
        logger.opt(exception=True).error("Unknown Error")
