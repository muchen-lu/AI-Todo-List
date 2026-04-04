import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
from datetime import datetime
from models import TodoItem, SubtaskItem

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

def get_5_tasks(datas: list[TodoItem]) -> list[TodoItem] :
    """從現有任務中，篩選代辦 5 件事情

    Args:
        datas (list[TodoItem]): 現有任務

    Returns:
        list[TodoItem]: 今日代辦五件事
    """
    
    datas = [{"id": data.id, "title": data.title, "deadline": data.deadline} for data in datas]
    
    prompt = f"""
    <角色>
    你是一名擁有 10 年經驗、專精於「高效率學習與專案管理」的高階行政特助。你擅長透過預判風險來安排日程，確保使用者永遠不會在截止日前感到焦慮。
    </角色>

    <背景資訊>
    現在時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}
    請以此時間為基準點，計算所有任務的緊急程度與剩餘時間。
    </背景資訊>

    <任務目標>
    請從 <現有任務集> 中篩選出「今天最重要的 5 件事」。
    篩選邏輯優先順序如下：
    1. **即刻執行**：今天或明天即將到期（Deadline）的任務或子任務。
    2. **戰略防禦**：截止日期在未來 3-7 天內，但性質複雜、需要多個工作天的「大任務」，今天必須安排部分進度以防崩潰。
    3. **子任務優先**：若主任務即將到期，優先選取其關聯的子任務。
    </任務目標>

    <現有任務>
    {datas}
    </現有任務>

    <回覆格式限制>
    1. **僅回傳 JSON**：不要包含任何解釋文字、代碼塊標籤 (如 ```json) 或開場白。
    2. **日期格式**：必須嚴格遵守 `YYYY-MM-DD HH:mm`（24小時制）。若原始任務無時間，請預設為 `23:59`。
    3. **回傳結構**：
    [
        {{"id": "任務 ID", "title": "任務標題", "deadline": "YYYY-MM-DD HH:mm"}},
        ...
    ]
    </回覆格式限制>
    """
    response = model.generate_content(prompt).text.replace("```json", "").replace("```", "").strip()
    print(response)
    try :
        tasks = json.loads(response)
        return [TodoItem(id = task["id"], title = task["title"], deadline = task["deadline"]) for task in tasks]
    except Exception as e :
        raise Exception(f"解析模型回覆失敗：{e}")

def generate_subtasks(task: TodoItem) -> list[SubtaskItem] :
    """為任務生成合適的子任務

    Args:
        task (TodoItem): 目標任務

    Returns:
        list[SubtaskItem]: 子任務清單
    """
    
    prompt = f"""
    <角色>
    你是一名擁有 10 年經驗、專注於「成果導向」的高階專案經理。你擅長將複雜的專案轉化為 3 到 5 個關鍵的「戰略里程碑 (Milestones)」，讓執行者能掌握節奏，避免在最後一刻才趕工。
    </角色>

    <任務目標>
    請針對下方的「目標任務」，規劃出 3 至 5 個關鍵子任務。
    這些子任務必須符合「階段性成果」的原則，確保專案能穩步推進。
    </任務目標>

    <目標任務>
    {task.title}
    </目標任務>

    <現在時間>
    {datetime.now().strftime('%Y-%m-%d %H:%M')}
    </現在時間>

    <執行準則>
    1. **里程碑原則**：子任務必須是具體的「階段性目標」（例如：完成資料蒐集、寫出初稿、最終排版校對），嚴禁出現瑣碎的步驟（例如：打開課本、準備文具）。
    2. **時間遞進**：請根據「現在時間」以及任務的合理執行週期，將子任務的截止日期（deadline）進行合理的倒推與分配。
    3. **簡潔有力**：子任務標題應直覺且明確，讓使用者一眼就能知道該階段的「交付物」是什麼。
    </執行准則>

    <回覆格式限制>
    1. **純 JSON 輸出**：不要包含任何解釋文字、前言、或是代碼塊標籤 (如 ```json)。
    2. **數量限制**：最少 3 個，最多 5 個子任務。
    3. **嚴格格式**：
    [
        {{"title": "子任務標題", "deadline": "YYYY-MM-DD HH:mm"}},
        ...
    ]
    </回覆格式限制>
    """
    
    response = model.generate_content(prompt).text.replace("```json", "").replace("```", "")
    print(response)
    
    try :
        subtasks = json.loads(response)
        if subtasks == [] :
            return []
        return [SubtaskItem(parent = task.id, title = subtask["title"], deadline = subtask["deadline"]) for subtask in subtasks]
    except Exception as e :
        raise Exception(f"解析模型回覆失敗：{e}")

if __name__ == "__main__" :
    # 測試用例
    task = TodoItem(title = "製作公民行動期末報告", deadline = "2026-04-15 23:59")
    subtasks = generate_subtasks(task)
    for subtask in subtasks :
        print(subtask.title, subtask.deadline)