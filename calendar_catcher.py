from dotenv import load_dotenv
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pytz
import datetime
from models import CalendarEvent

load_dotenv()

# 更新權限範圍
SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly"
]

creds = None
if os.path.exists("remote_token.json"):
    creds = Credentials.from_authorized_user_file("remote_token.json", SCOPES)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
    with open("remote_token.json", "w") as token:
        token.write(creds.to_json())

# 建立 Calendar 工具連線
service = build("calendar", "v3", credentials=creds)

def get_calendar_events() -> list[CalendarEvent] :
    """抓取從當日到當周六的事件"""
    global service
    tz = pytz.timezone('Asia/Taipei')
    now = datetime.datetime.now(tz)
    
    saturday = (5 - now.weekday()) % 7
    saturday = (now + datetime.timedelta(days=saturday)).replace(hour=23, minute=59, second=59, microsecond=0)
    now = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    events = service.events().list(
        calendarId="primary",
        timeMin=now.isoformat(),
        timeMax=saturday.isoformat(),
        singleEvents=True,
        orderBy="startTime"
    ).execute() | service.events().list(
        calendarId="11330116@tschool.tp.edu.tw",
        timeMin=now.isoformat(),
        timeMax=saturday.isoformat(),
        singleEvents=True,
        orderBy="startTime"
    ).execute()
    events = events.get("items", [])
    events.sort(key=lambda x: x['start'].get('dateTime', x['start'].get('date')))
    
    # print(events[0])
    events = [event for event in events if event.get("transparency", "opaque") == "opaque"] # 只抓取實際佔用時間的事件，排除掉純提醒性質的事件
    events = [
    event for event in events 
    if event.get('organizer', {}).get('self', False) or 
    next((a for a in event.get('attendees', []) if a.get('self') and a.get('responseStatus') == 'accepted'), None)
    ] # 從所有事件中抓取自己的事件或是被邀請且已確認的事件
    
    return [CalendarEvent(**event) for event in events]
    
if __name__ == "__main__" :
    events = get_calendar_events()
    print(f"{events}")