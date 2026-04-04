import os
from typing import List, Literal
from random import choice
import json
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, PushMessageRequest, TextMessage, FlexMessage, FlexContainer
from models import TodoItem, SubtaskItem
from dotenv import load_dotenv

load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
morning_greetings = ["早安！新的一天開始了，今天的 5 件核心任務已經為你準備好囉。",
                     "迎接陽光，也迎接今天的挑戰！這 5 件事是今天的進步關鍵。",
                     "醒了嗎？今天有 5 個目標等著你達成，讓我們一起開始吧！",
                     "早安，今天又是充滿機會的一天！這是你今天的優先任務清單。",
                     "早！今天最重要的 5 件事就在這裡，專注在當下，你一定做得到。",
                     "用清爽的心情開啟今天，這是你今天的行動指南，加油！",
                     "早安！今天的 5 個任務已經整理完畢，準備好就出發吧。",
                     "美好的一天從達成小目標開始，這 5 件事是今天的首要挑戰。",
                     "早安！今天不用煩惱要做什麼，跟著這 5 件事走，效率會更高。",
                     "太陽升起了，今天的任務也準備好了！準備好迎接今日的冒險了嗎？"]
night_greetings = ["晚安！先幫你整理好明天的 5 件事，看完就能安心睡好覺囉。",
                   "在睡前瞄一眼明天的計畫，讓腦袋先有個底，明天起床不慌張。",
                   "明天的挑戰清單已經準備好了，先傳給你參考，今晚早點休息！",
                   "給明天的自己一個小提醒：這 5 件事是明天的重點喔。",
                   "晚安！明天的行程看起來很充實，準備好迎接它了嗎？",
                   "睡前先確認一下明天的目標，這樣明天一睜眼就知道要做什麼了。",
                   "晚安，明天的 5 件事已經排好隊了。先知道，明天就不會手忙腳亂。",
                   "明天的清單在這裡，現在先別想太多，好好充電，明天加油！",
                   "預告一下明天的重要任務，現在，先祝你有個好夢！"]

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
line_bot = MessagingApi(ApiClient(configuration))

def send_line_notification(tasks: List[TodoItem | SubtaskItem], timing: Literal["morning", "night"]) -> None:
    """將任務藉由 Line 傳送給使用者

    Args:
        tasks (List[TodoItem | SubtaskItem]): 任務清單
        timing (Literal["morning", "night"]): 通知時機
    """
    message = choice(morning_greetings) if timing == "morning" else choice(night_greetings)
    task_message = {"type": "carousel", "contents": []}
    messages = []
    if timing == "night" :
        for task in tasks :
            message += f"\n• {task.title}"
    elif timing == "morning" :
        for task in tasks :
            template = {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": task.title,
                            "weight": "bold",
                            "size": "xl",
                            "wrap": True
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "margin": "lg",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "box",
                                    "layout": "baseline",
                                    "spacing": "sm",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "Deadline",
                                            "color": "#aaaaaa",
                                            "size": "sm",
                                            "flex": 2
                                        },
                                        {
                                            "type": "text",
                                            "text": task.deadline if task.deadline else "無",
                                            "wrap": True,
                                            "color": "#666666",
                                            "size": "sm",
                                            "flex": 4
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "button",
                            "style": "primary", # 改為 primary 比較顯眼，你也可以用 link
                            "height": "sm",
                            "action": {
                                "type": "postback", # 修正：要傳 data 必須用 postback，不能用 uri
                                "label": "Complete",
                                "data": f"action=complete&task={task.id if isinstance(task, TodoItem) else task.parent + '&subtask=' + task.id}",
                                "displayText": f"完成「{task.title}」了！"
                            },
                            "color": "#06C755"
                        }
                    ],
                    "flex": 0
                }
            }
            task_message["contents"].append(template)
        task_message = FlexMessage(alt_text="你的任務清單", contents=FlexContainer.from_dict(task_message))
        messages.append(task_message)
    
    message = TextMessage(text=message)
    messages.insert(0, message)
    push_message_request = PushMessageRequest(to=LINE_USER_ID, messages=messages)
    
    try :
        line_bot.push_message(push_message_request)
    except Exception as e:
        raise Exception(f"寄送 Line Message 失敗：{e}")

if __name__ == "__main__" :
    send_line_notification([TodoItem(title="測試任務", deadline="2026-12-31 23:59"), TodoItem(title="測試任務2", deadline="2026-12-31 23:59"), TodoItem(title="測試任務3", deadline="2026-12-31 23:59")], "morning")