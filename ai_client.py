import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
from datetime import datetime
from models import TodoItem, SubtaskItem
from calendar_catcher import get_calendar_events
from database_manager import get_history

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-3-flash-preview")

def eliminate_point(task: TodoItem) -> TodoItem | SubtaskItem :
    """利用 AI 估計任務所需能量，並將其轉化為 0~10 的 expect_point"""
    
    def history_file() -> list[str] :
        now = datetime.now()
        year = now.year
        month = now.month
        match month :
            case month if month in [1, 2, 3] :
                return [f"{year-1}_Q4", f"{year}_Q1"]
            case month if month in [4, 5, 6] :
                return [f"{year}_Q1", f"{year}_Q2"]
            case month if month in [7, 8, 9] :
                return [f"{year}_Q2", f"{year}_Q3"]
            case month if month in [10, 11, 12] :
                return [f"{year}_Q3", f"{year}_Q4"]
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    calendar_context = get_calendar_events()
    prompt = f"""
    你是一名高階行政特助，專長是評估學習負擔。
    請根據以下任務清單及使用者過去的任務耗能記錄，自動估算其 energy_load (1-10 分)。
    
    <使用者特質>
    - 高中生，流行音樂社社長(鼓手)、資研社副社長、學生會學權部部長。
    - 擅長程式。
    </使用者特質>

    <評估準則>
    - [1分] 微量：單純點擊、查看、轉傳，不需思考。
    - [3分] 輕量：熟練的例行公事 (SOP)，不需對照外部資料。
    - [5分] 中量：需專注 45-60 分鐘的產出，邏輯路徑清晰。
    - [7分] 重量：需深度專注 2 小時以上，涉及多模組整合。
    - [9分] 極限：全天候抗戰，身心高度緊繃。
    - 禁止「詞彙溢價」：不要看到『自述、期末、專案』就給高分，必須根據後綴（架構、草稿、練習）進行減分。
    - 禁止「全高分偏誤」：在處理子任務 (Subtasks) 時，必須展現階梯感。讀取類 (Read) 一律比寫入類 (Write) 低 2-3 分。
    </評估準則>
    
    <+1 因子判定>
    - [+1 糾錯因子]：涉及 Debug、重構 (Refactor) 或邏輯除錯。
    - [+1 檢索因子]：需要頻繁翻找文件、對照外部 API 或處理外語。
    - [+1 風險因子]：操作具有不可逆性 (如修改資料庫 Schema、發布正式版)。
    - [+1 弱項因子]：任務標題明確涉及使用者不擅長的學科。
    </+1 因子判定>
    
    <定錨對照組 - 請嚴格參考此標準>
    1. 標題：[數學] 習題 1-1
    - 估分：5 (基準點：需專注 40-60 分鐘)
    2. 標題：學習歷程自述架構-課堂練習
    - 估分：3 (原因：僅為「架構」與「練習」，不具備最終產出壓力)
    3. 標題：英文單字 L4 測驗
    - 估分：6 (原因：例行性小考)
    4. 標題：社團練團通知發送
    - 估分：1 (原因：單純的操作性雜事)
    5. 標題：[自主學習] 程式專案開發 - 登入功能實作
    - 估分：7 (原因：高強度邏輯思考與實作)
    </定錨對照組 - 請嚴格參考此標準>

    <待估算任務>
    {task}
    </待估算任務>
    
    <任務紀錄>
    {"".join(get_history(file) for file in history_file())}
    </任務紀錄>

    <回覆格式限制>
    僅回傳 JSON，結構如下，若待估算任務中含有 parent 鍵與值則附上，否則不用 parent 鍵與值：
    {{"parent": "父任務 ID", "id": "任務 ID", "title": "任務標題", "deadline": "YYYY-MM-DD HH:mm", "expect_point": 數字}},
    </回覆格式限制>
    """
    response = model.generate_content(prompt).text.replace("```json", "").replace("```", "").strip()
    print(response)
    try :
        task = json.loads(response)
        if "parent" in task :
            return SubtaskItem(parent = task["parent"], id = task["id"], title = task["title"], deadline = task["deadline"], expect_point = task["expect_point"])
        else :
            return TodoItem(id = task["id"], title = task["title"], deadline = task["deadline"], expect_point = task["expect_point"])
    except Exception as e :
        raise Exception(f"解析模型回覆失敗：{e}")

def get_5_tasks(datas: list[TodoItem]) -> list[TodoItem] :
    """從現有任務中，篩選代辦 5 件事情

    Args:
        datas (list[TodoItem]): 現有任務

    Returns:
        list[TodoItem]: 今日代辦五件事
    """
    datas = [{"id": data.id, "title": data.title, "deadline": data.deadline} for data in datas]
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    calendar_context = get_calendar_events()
    calendar_context = [{"title": event.title, "today": event.today, "long": event.long} for event in calendar_context]
    prompt = f"""
    <角色>
    你是一名擁有 10 年經驗、專精於「動態負載平衡」的高階行政特助。你擅長結合使用者的生活節奏（日曆）與任務難度（能量）來安排日程，確保使用者在達成目標的同時，能保有完全的休息品質。
    </角色>

    <背景資訊>
    現在時間：{current_time}
    </背景資訊>

    <日曆情境 (即日起至週六)>
    {calendar_context}
    </日曆情境>

    <任務篩選邏輯>
    1. 週六清零原則：若任務之真實截止日 (Deadline) 在「下週三 (含) 以前」，請視其為高優先級，必須安排在週六 23:59 前完成。
    2. 能量負載平衡：
    - 參考 <日曆情境>：若當日已有長時間行程（如練團、上課），請調降今日可分配的 energy_load 總額。
    - 每日天花板：無論日曆多空，今日派發任務的 energy_load 總和嚴格禁止超過 30 點，且任務總數量不得超過 5 個。
    3. 前置化策略：優先將紅區任務往前安排，避免週六出現任務大噴發。
    </任務篩選邏輯>

    <現有任務>
    {datas}
    </現有任務>

    <回覆格式限制>
    1. 僅回傳 JSON：不要包含任何解釋、代碼塊標籤或開場白。
    2. 結構要求：
    {{
        "id": "任務唯一識別碼",
        "title": "任務標題",
        "deadline": "YYYY-MM-DD HH:mm",
        "expect_point": 0~10
    }}
    </回覆格式限制>
    """
    response = model.generate_content(prompt).text.replace("```json", "").replace("```", "").strip()
    print(response)
    try :
        tasks = json.loads(response)
        return [TodoItem(id = task["id"], title = task["title"], deadline = task["deadline"], expect_point = task["expect_point"]) for task in tasks]
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
    task = TodoItem(title = "程式交易歷史紀錄功能實作", deadline = "2026-04-30 20:00")
    tasks = generate_subtasks(task)
    for task in tasks :
        task = eliminate_point(task)
        print(task)