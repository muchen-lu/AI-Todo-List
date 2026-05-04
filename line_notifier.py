import os
from typing import List, Literal
from random import choice
import json
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, PushMessageRequest, TextMessage, FlexMessage, FlexContainer, ReplyMessageRequest
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
l1_feedback = ["順手解決了一件小事！感覺還輕鬆嗎？",
             "完成囉！這項任務處理起來還順利嗎？",
             "輕鬆搞定，特助已經紀錄好了。體感難度是？",
             "辛苦了！這件事對你來說應該不難吧？",
             "沒問題，這項任務的實際耗能感覺如何？"]
l2_feedback = ["任務順利完成，辛苦了！體感難度跟預估的一樣嗎？",
               "穩穩地處理完一項工作了。實際能耗大約是多少呢？",
               "辛苦了！這種難度的任務，處理起來還順手嗎？",
               "完成！特助想確認一下，這件事的難度符合預期嗎？",
               "又跨出一步了。幫我校準一下這項任務的體感："]
l3_feedback = ["這段時間辛苦了，先休息一下吧。這項任務累嗎？",
               "完成了一項有份量的任務！感覺能量消耗了多少呢？",
               "辛苦了！這件事應該花了不少心思，體感難度是？",
               "終於處理完了，喝口水休息吧。你覺得這項任務硬嗎？",
               "專注模式結束。幫特助評估一下這次的真實耗能："]
l4_feedback = ["處理這麼複雜的任務辛苦了！現在感覺體力還好嗎？",
               "完成了這項大工程，真的不簡單。你給體感幾分？",
               "辛苦你了，這件事應該讓你花了不少體力與心神吧？",
               "任務大功告成！這場長時間的挑戰，感覺如何？",
               "特助感覺這件事挺耗能的，你真實的體感分數是？"]
l5_feedback = ["真的辛苦了！完成這項任務一定很累吧，快去休息。",
               "這項任務難度很高，能處理完真的很不容易，還好嗎？",
               "辛苦你了，這應該是今天最硬的一項了，體感是？",
               "終於搞定了！特助很關心你現在的狀態，感覺如何？",
               "耗費這麼多能量辛苦了。這項魔王任務你實際給幾分？"]

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

def reply_user(mode: Literal["task", "notification"], reply_token: str, **kargs) -> None:
    """回覆使用者訊息

    Args:
        mode (Literal["task", "notification"]): 回覆類型
        reply_token (str): Line 的 reply token
    """
    if mode == "task" and ("title" not in kargs or "expect_point" not in kargs or "task_id" not in kargs) :
        raise ValueError("回覆任務訊息時必須提供 title、expect_point 以及 task_id 或 subtask_id")
    title = kargs.get("title")
    expect_point = kargs.get("expect_point")
    task_id = kargs.get("task_id")
    subtask_id = kargs.get("subtask_id")
    
    match expect_point :
        case point if 1 <= point <= 2 :
            feedback = choice(l1_feedback)
        case point if 3 <= point <= 4 :
            feedback = choice(l2_feedback)
        case point if 5 <= point <= 6 :
            feedback = choice(l3_feedback)
        case point if 7 <= point <= 8 :
            feedback = choice(l4_feedback)
        case point if 9 <= point <= 10 :
            feedback = choice(l5_feedback)

    template = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
            {
                "type": "text",
                "text": f"恭喜完成「{title}」任務",
                "weight": "bold",
                "size": "lg",
                "wrap": True
            },
            {
                "type": "box",
                "layout": "vertical",
                "margin": "lg",
                "spacing": "sm",
                "contents": [
                {
                    "type": "text",
                    "text": feedback,
                    "wrap": True
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
                "style": "secondary",
                "height": "sm",
                "action": {
                "type": "postback",
                "label": "🍃 意外地輕鬆",
                "data": f"action=reply&task={task_id if subtask_id is None else task_id + '&subtask=' + subtask_id}&offset=-2",
                "displayText": "這件事比想像中輕鬆很多！🍃"
                },
                "color": "#4CAF50"
            },
            {
                "type": "button",
                "style": "secondary",
                "height": "sm",
                "action": {
                "type": "postback",
                "label": "👌 比預期簡單",
                "data": f"action=reply&task={task_id if subtask_id is None else task_id + '&subtask=' + subtask_id}&offset=-1",
                "displayText": "做起來比預計的還要簡單些。👌"
                },
                "color": "#8BC34A"
            },
            {
                "type": "button",
                "action": {
                "type": "postback",
                "label": "🎯 估得很準！",
                "data": f"action=reply&task={task_id if subtask_id is None else task_id + '&subtask=' + subtask_id}&offset=0",
                "displayText": "特助估計得很準確喔，辛苦了！🎯"
                },
                "style": "primary",
                "height": "sm",
                "color": "#9E9E9E"
            },
            {
                "type": "button",
                "action": {
                "type": "postback",
                "label": "💦 稍微有點累",
                "data": f"action=reply&task={task_id if subtask_id is None else task_id + '&subtask=' + subtask_id}&offset=+1",
                "displayText": "呼，實際做起來稍微有點累人。💦"
                },
                "style": "secondary",
                "color": "#FF9800",
                "height": "sm"
            },
            {
                "type": "button",
                "action": {
                "type": "postback",
                "label": "😵‍💫 比想像中硬",
                "data": f"action=reply&task={task_id if subtask_id is None else task_id + '&subtask=' + subtask_id}&offset=+2",
                "displayText": "這項任務比預期中還要硬很多... 😵‍💫"
                },
                "style": "secondary",
                "height": "sm",
                "color": "#F44336"
            }
            ],
            "flex": 0
        }
    }
    if mode == "task" :
        message = FlexMessage(alt_text="任務完成回饋", contents=FlexContainer.from_dict(template))
    request = ReplyMessageRequest(reply_token=reply_token, messages=[message])
    line_bot.reply_message(request)