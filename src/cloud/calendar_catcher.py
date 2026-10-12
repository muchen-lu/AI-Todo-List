# calendar_catcher.py
import datetime
import pytz
from dotenv import load_dotenv
from googleapiclient.discovery import build
from src.shared.models import CalendarEvent
from src.cloud.cloud_auth import get_cloud_google_creds

load_dotenv()

def get_calendar_service(user_id: str):
    creds = get_cloud_google_creds(user_id)
    return build("calendar", "v3", credentials=creds)

def get_calendar_events(user_id: str, extra_calendar_ids: list[str] | None = None) -> list[CalendarEvent]:
    """抓取從當日到當周六的事件（支援多使用者）"""
    service = get_calendar_service(user_id)
    tz = pytz.timezone("Asia/Taipei")
    now = datetime.datetime.now(tz)
    
    saturday = (5 - now.weekday()) % 7
    saturday = (now + datetime.timedelta(days=saturday)).replace(hour=23, minute=59, second=59, microsecond=0)
    now = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # 預設抓取該使用者的主日曆；若有傳入額外日曆清單則一併抓取
    target_calendars = ["primary"] + (extra_calendar_ids or [])
    all_items = []

    for cal_id in target_calendars:
        res = service.events().list(
            calendarId=cal_id,
            timeMin=now.isoformat(),
            timeMax=saturday.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        # 用 extend 把多個日曆的 items 清單真正合併在一起，不會互相覆蓋！
        all_items.extend(res.get("items", []))

    all_items.sort(key=lambda x: x["start"].get("dateTime", x["start"].get("date")))
    
    # 只抓取實際佔用時間的事件，排除純提醒性質的事件
    events = [event for event in all_items if event.get("transparency", "opaque") == "opaque"]
    # 抓取自己的事件或是被邀請且已確認的事件
    events = [
        event for event in events 
        if event.get("organizer", {}).get("self", False) or 
        next((a for a in event.get("attendees", []) if a.get("self") and a.get("responseStatus") == "accepted"), None)
    ]
    
    return [CalendarEvent(**event) for event in events]
    
if __name__ == "__main__" :
    events = get_calendar_events()
    print(f"{events}")