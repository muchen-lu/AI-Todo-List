import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import datetime
from playwright.sync_api import Playwright, sync_playwright, expect
from src.shared.models import TodoItem, ONOItem, GCItem
from src.shared.ai_client import eliminate_data

# 更新權限範圍
SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.me",
    # "https://www.googleapis.com/auth/classroom.coursework.readonly"
]

creds = None
if os.path.exists("local_token.json"):
    creds = Credentials.from_authorized_user_file("local_token.json", SCOPES)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
    with open("local_token.json", "w") as token:
        token.write(creds.to_json())

# 建立 Classroom 工具連線
service = build("classroom", "v1", credentials=creds)

def get_ono() -> list[ONOItem]:
    """使用爬蟲取得 ONO 上現有任務
    Returns:
        list[ONOItem]: 任務列表，每個任務包含標題和截止日期
    """
    tasks = []
    def run(playwright: Playwright) -> None :
        nonlocal tasks
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://cooc.tp.edu.tw/oauth2/oauth/authorize?client_id=2gMSkBmGUSJVkwCrZz2fnMNtMj2Dfasc&response_type=code&redirect_uri=https%3A//ono.tp.edu.tw/login&state=L3VzZXIvaW5kZXg=&scope=User.Info,User.Role,User.RoleDetail,User.IDNumber,User.SSORole,User.EMail#/")
        page.get_by_text("臺北市校園單一身分驗證入口").click()
        page.get_by_role("textbox", name="帳號").click()
        page.get_by_role("textbox", name="帳號").fill(os.getenv("ONO_USERNAME"))
        page.get_by_role("textbox", name="密碼").click()
        page.get_by_role("textbox", name="密碼").fill(os.getenv("ONO_PASSWORD"))
        page.get_by_role("button", name="登入", exact=True).click()
        # page.goto("https://ono.tp.edu.tw/user/index#/", wait_until="domcontentloaded")
        page.wait_for_url("https://ono.tp.edu.tw/user/index#/", timeout = 0)
        page.wait_for_selector(".todo-list")
        
        items = page.locator(".todo-list").all()
        tasks = []
        for item in items :
            title = item.locator(".title-text span").inner_text().strip()
            deadline = item.locator("span:has-text('截止日期')").inner_text().replace("截止日期:", "").replace(".", "-").strip()
            task = ONOItem(title = title, deadline = deadline)
            # task = TodoItem(title = task.title, deadline = task.deadline, estimate_data = eliminate_data(task))
            tasks.append(task)

        # ---------------------
        context.close()
        browser.close()

    with sync_playwright() as playwright:
        run(playwright)
    
    return tasks

def get_classroom() -> list[GCItem] :
    """抓取 Google Classroom 代辦作業

    Returns:
        list[GCItem]: 作業列表，每個作業包含標題和截止日期
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
                    # task = TodoItem(title = homework.title, deadline = homework.deadline, estimate_data = eliminate_data(homework))
                    tasks.append(homework)

    return tasks

# if __name__ == "__main__" :
#     tasks = get_ono()
#     for task in tasks :
#         print(task.title, task.deadline, task.expect_point)