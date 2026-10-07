import os
from typing import List, Literal
from random import choice
import json
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, PushMessageRequest, TextMessage, FlexMessage, FlexContainer, ReplyMessageRequest
from src.shared.models import TodoItem, SubtaskItem
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

gold_star = {
                "type": "icon",
                "size": "sm",
                "url": "https://developers-resource.landpress.line.me/fx/img/review_gold_star_28.png"
            }
gray_star = {
                "type": "icon",
                "size": "sm",
                "url": "https://developers-resource.landpress.line.me/fx/img/review_gray_star_28.png"
            }

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
                        "size": "xl"
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                        {
                            "type": "text",
                            "text": "任務負荷",
                            "position": "relative",
                            "align": "start",
                        },
                        *(gold_star if i < task.estimate_data.congnitive_load else gray_star for i in range(5)),
                        {
                            "type": "text",
                            "text": ("淺層" if task.estimate_data.suggest_work_mode == "shallow" else "深層"),
                            "size": "sm",
                            "color": "#999999",
                            "margin": "md",
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": " "
                        }
                        ],
                        "position": "relative",
                        "margin": "md"
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
                                "text": task.deadline,
                                "wrap": True,
                                "color": "#666666",
                                "size": "sm",
                                "flex": 5
                            }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "baseline",
                            "spacing": "sm",
                            "contents": [
                            {
                                "type": "text",
                                "text": "Duration",
                                "color": "#aaaaaa",
                                "size": "sm",
                                "flex": 2
                            },
                            {
                                "type": "text",
                                "text": str(task.estimate_data.estimated_time) + " min(s)",
                                "wrap": True,
                                "color": "#666666",
                                "size": "sm",
                                "flex": 5
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
                        "style": "primary",
                        "height": "sm",
                        "action": {
                        "type": "postback",
                        "label": "Complete",
                        "data": f"action=complete&task={task.id if isinstance(task, TodoItem) else task.parent + '&subtask=' + task.id}",
                        "displayText": f"完成「{task.title}」了！"
                        },
                        "color": "#06C755"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [],
                        "margin": "sm"
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
    if mode == "task" and ("title" not in kargs) :
        raise ValueError("回覆任務訊息時必須提供 title 或 subtask_id")
    title = kargs.get("title")
    message = kargs.get("message")
    if mode == "task" :
        message = TextMessage(text = f"收到啦～恭喜完成「{title}」任務！")
    elif mode == "notification" :
        message = TextMessage(text = message)
    request = ReplyMessageRequest(reply_token=reply_token, messages=[message])
    line_bot.reply_message(request)

async def send_reminder(task_title: str):
    """寄送提醒訊息給使用者

    Args:
        task_title (str): 任務標題
    """
    message = TextMessage(text = f"提醒你：{task_title}")
    request = PushMessageRequest(to=LINE_USER_ID, messages=[message])
    
    try :
        line_bot.push_message(request)
    except Exception as e:
        raise Exception(f"寄送 Line Message 失敗：{e}")

if __name__ == "__main__" :
    # 測試用
    from src.shared.models import TodoItem, EstimateData
    test_task = TodoItem(title="測試任務", deadline="2024-06-30 23:59", estimate_data=EstimateData(confidence = 0.9, congnitive_load = 3, estimated_time = 30, suggest_work_mode = "shallow", task_category = "learning"))
    send_line_notification([test_task], "night")
    send_line_notification([test_task], "morning")