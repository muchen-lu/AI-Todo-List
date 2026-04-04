import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import datetime
from playwright.sync_api import Playwright, sync_playwright, expect
from models import TodoItem, GCItem

# 更新權限範圍
SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.me",
    # "https://www.googleapis.com/auth/classroom.coursework.readonly"
]

creds = None
if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
    with open("token.json", "w") as token:
        token.write(creds.to_json())

# 建立 Classroom 工具連線
service = build("classroom", "v1", credentials=creds)

def get_ono() -> list[TodoItem]:
    """使用爬蟲取得 ONO 上現有任務
    Returns:
        list[TodoItem]: 任務列表，每個任務包含標題和截止日期
    """
    tasks = []
    def run(playwright: Playwright) -> None :
        nonlocal tasks
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://cooc.tp.edu.tw/oauth2/oauth/authorize?client_id=2gMSkBmGUSJVkwCrZz2fnMNtMj2Dfasc&response_type=code&redirect_uri=https%3A//ono.tp.edu.tw/login&state=L3VzZXIvaW5kZXg=&scope=User.Info,User.Role,User.RoleDetail,User.IDNumber,User.SSORole,User.EMail#/")
        page.get_by_text("臺北市校園單一身分驗證入口").click()
        page.get_by_role("textbox", name="帳號").click()
        page.get_by_role("textbox", name="帳號").fill("RyanLai")
        page.get_by_role("textbox", name="密碼").click()
        page.get_by_role("textbox", name="密碼").fill("R0612B0811")
        page.get_by_role("button", name="登入", exact=True).click()
        # page.goto("https://ono.tp.edu.tw/user/index#/", wait_until="domcontentloaded")
        page.wait_for_url("https://ono.tp.edu.tw/user/index#/")
        page.wait_for_selector(".todo-list")
        
        items = page.locator(".todo-list").all()
        tasks = []
        for item in items :
            title = item.locator(".title-text span").inner_text().strip()
            deadline = item.locator("span:has-text('截止日期')").inner_text().replace("截止日期:", "").replace(".", "-").strip()
            tasks.append(TodoItem(title = title, deadline = deadline))

        # ---------------------
        context.close()
        browser.close()

    with sync_playwright() as playwright:
        run(playwright)
    
    return tasks

def get_classroom() -> list[TodoItem] :
    """抓取 Google Classroom 代辦作業

    Returns:
        list[TodoItem]: 作業列表，每個作業包含標題和截止日期
    """
    tasks = []
    courses = service.courses().list(courseStates='ACTIVE').execute()
    courses = courses.get("courses", [])
    
    for course in courses :
        course_id = course["id"]
        homeworks = service.courses().courseWork().list(courseId=course_id).execute()
        homeworks = homeworks.get("courseWork", [])
        submissions = service.courses().courseWork().studentSubmissions().list(courseId=course_id, courseWorkId="-", userId="me").execute()
        submissions = submissions.get("studentSubmissions", [])

        for i in range(len(homeworks)) :
            if not (submissions[i]["state"] in ("TURNED_IN", "RETURNED")) :
                if ("dueDate" not in homeworks[i]) or (datetime.datetime.strptime(str(homeworks[i]["dueDate"]["year"])+"-"+str(homeworks[i]["dueDate"]["month"])+"-"+str(homeworks[i]["dueDate"]["day"]), "%Y-%m-%d") >= datetime.datetime.now() - datetime.timedelta(days = 30)) :
                    homework = homeworks[i]
                    # print(homework)
                    homework = GCItem(**homework)
                    tasks.append(TodoItem(title = homework.title, deadline = homework.deadline))

    return tasks