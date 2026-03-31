import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# 更新權限範圍
SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.me"
]

def main():
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

    print("正在取得你的課程清單...\n")
    # 1. 先抓課程
    courses_result = service.courses().list(pageSize=5).execute()
    courses = courses_result.get("courses", [])

    if not courses:
        print("找不到任何課程。")
        return

    for course in courses:
        course_id = course["id"]
        course_name = course["name"]
        print(f"=== 正在檢查課程：{course_name} (ID: {course_id}) ===")

        # 2. 抓該課程的作業 (CourseWork)
        coursework_result = service.courses().courseWork().list(courseId=course_id, pageSize=3).execute()
        courseworks = coursework_result.get("courseWork", [])

        if not courseworks:
            print("  這門課目前沒有作業。")
        else:
            for work in courseworks:
                print("\n  [ 作業原始資料 ]")
                # 這就是你想看的原始資料內容
                print(work) 
                print(f"  作業標題: {work.get('title')}")
                print("-" * 30)

if __name__ == "__main__":
    main()