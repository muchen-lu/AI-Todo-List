import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
from datetime import datetime
from src.shared.models import TodoItem, SubtaskItem, ONOItem, GCItem, EstimateData, CalendarEvent
from src.cloud.calendar_catcher import get_calendar_events
from src.shared.database_manager import get_history

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-3-flash-preview")

def eliminate_data(task: ONOItem | GCItem) -> EstimateData:
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
    # calendar_context = get_calendar_events()

    prompt = f"""
        # 角色與目標
        你是一位專業的時間管理與工作排程分析師，擅長拆解工作本質、評估注意力成本，並為任務安排最佳執行模式。請依據輸入的「任務名稱」與「截止時間」，完成多維度分析並回傳結構化評估。

        ---

        # 輸入參數
        - **任務名稱**：{task.title}
        - **截止時間**：{task.deadline}

        ---

        # 評估維度與準則

        1. **任務類型（Task Type）**：請從下列選項中精確比對最符合的一項：
        - writing(撰寫報告、文案發想、企劃書撰寫)
        - design(Logo 設計、UI 排版、簡報視覺設計)
        - development(程式開發、修復問題、重構程式碼)
        - communication(回覆信件、即時訊息溝通、電話聯繫)
        - meeting(內部同步會議、客戶提案會議、跨部門討論)
        - research(市場調查、資料蒐集、數據分析)
        - planning(專案時程規劃、策略制定、架構設計)
        - admin(表單申請、單據報銷、例行文件歸檔)
        - review(校對文件、程式碼審查、QA 測試)
        - learning(閱讀書籍、線上課程學習、新技術研究)
        - other(無法歸類的任務,保底選項)

        2. **認知負載度（Cognitive Load）**：
        - 評級：1~5（1=低，5=高）
        - 判斷依據：評估該任務所需的心智專注力、決策複雜度、邏輯抽象度以及上下文切換成本。

        3. **預計耗時（Estimated Duration）**：
        - 單位為**分鐘**（整數數值，如 30、45、90，且最低可到 1）。
        - 請基於常規專業人員標準產出速度進行預估，若任務過大，請估算完成最小可行階段所需的分鐘數。

        4. **執行模式（Execution Mode）**：
        - **深度工作**：認知負載為「中」或「高」，且預計耗時通常 $\ge$ 45 分鐘，需連貫專注、抗干擾的狀態。
        - **零碎時間**：認知負載為「低」，或耗時 $\le$ 30 分鐘，中斷重啟成本低，可利用零散空檔處理。

        5. **評估信心度（Confidence Level）**：
        - 評級：0~1（0=完全不確定，1=非常確定）
        - 判定標準：依據「任務名稱的明確度」與「潛在不確定性」進行評估。

        ---

        # 輸出格式
        請統一以 JSON 格式輸出，無須包含多餘前言或結尾廢話：

        {{
        "task_name": "任務名稱",
        "deadline": "截止時間",
        "task_category": "任務類別",
        "cognitive_load": 1~5,
        "estimated_duration_minutes": 60,
        "execution_mode": "deep" | "shallow",
        "confidence": 0.85
        }}
    """
    response = model.generate_content(prompt).text.replace("```json", "").replace("```", "").strip()
    print(response)
    try :
        task = json.loads(response)
        return EstimateData(
            task_category = task["task_category"],
            congnitive_load = task["cognitive_load"],
            estimated_time = task["estimated_duration_minutes"],
            suggest_work_mode = task["execution_mode"],
            confidence = task["confidence"]
        )
    except Exception as e :
        raise Exception(f"解析模型回覆失敗：{e}")

def suggest_tasks(datas: list[TodoItem], calendar: list[CalendarEvent]) -> list[TodoItem] :
    """從現有任務中，篩選代辦 5 件事情

    Args:
        datas (list[TodoItem]): 現有任務
        calendar (list[CalendarEvent]): 今日行程安排

    Returns:
        list[TodoItem]: 今日代辦五件事
    """
    # datas = [{"id": data.id, "title": data.title, "deadline": data.deadline} for data in datas]
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    # calendar_context = get_calendar_events()
    # calendar_context = [{"title": event.title, "today": event.today, "start": event.start, "end": event.end} for event in calendar_context]
    ai_datas = [data.model_dump_json() for data in datas]
    calendar = [event.model_dump_json() for event in calendar]
    prompt = f"""
    # 角色定位
    你是一位「高階動態排程架構師與個人生產力教練」，專精於容量規劃（Capacity Planning）、認知精力分配與平準化工作流（Workload Leveling）。你的目標是協助使用者在高產能、平穩步調與健康休息之間取得最佳平衡。

    ---

    # 輸入參數

    ### 1. 現有任務清單（Task Pool）
    請列出所有待辦事項（包含任務名稱、截止日、預估耗時、認知負荷等）：
    {ai_datas}

    ### 2. 今日行程安排（Today's Context）
    - **排程時間基準窗口**：固定為每日 **08:00 ~ 12:00**、**13:30~18:00** 與 **20:00~22:00**（此範圍外為睡眠與個人生活防護時段，一律不排工作）。
    {calendar}

    ---

    # 排程核心原則與硬性限制

    1. **零工週日守則（Sunday Rest Rule - 絕對硬性限制）**：
    - 週日一律不准安排任何工作或任務。
    - 所有截止日臨近週末的任務，必須強制提前至週五或週六前消化完畢，絕不延後至週日。

    2. **工作量平準化（Workload Leveling）**：
    - 拒絕「前幾天閒散、壓線當天通宵爆肝」的現象。
    - 以長線眼光拆解遠期任務，平均攤提至每日日常，單日任務總預估工時嚴禁超過「可用專注工時」的 65%（保留 35% 緩衝應對突發狀況）。

    3. **精力與時段匹配（Energy Matching）**：
    - 「深度工作」排入今日未被打斷的連續大時段；「零碎任務」填入會議間隙或精神較疲乏的時段。

    4. **餘力前置拉動（Proactive Pull-Forward）**：
    - 若評估今日固定行程少、專注餘裕充足，**主動從未來清單挑選 1–2 項高價值或高阻力的中長線任務進行提前推進**（哪怕只是完成前置調研或草稿），建立心理安全感。

    ---

    # 輸出格式規範
    必須一律以標準 **JSON** 格式輸出，不得包含任何 Markdown 前言或後記廢話。JSON 結構如下：

    {{
    "capacity_minutes": 300 # 今日可用專注工時，單位為分鐘
    "today_selected_tasks": [0, 2, 5] # 今日代辦任務索引，對應於輸入的現有任務清單（Task Pool）中的索引位置
    }}
    """
    response = model.generate_content(prompt).text.replace("```json", "").replace("```", "").strip()
    print(response)
    try :
        tasks = json.loads(response)
        return [datas[i] for i in tasks["today_selected_tasks"]]
    except Exception as e :
        raise Exception(f"解析模型回覆失敗：{e}")

# TODO: 需要實作這個內容
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

def analyze_intent(message: str) -> list[dict] :
    """分析使用者訊息意圖，並回傳結構化結果

    Args:
        message (str): 使用者訊息

    Returns:
        list[dict]: 結構化意圖分析結果
    """
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    prompt = f"""
    # 角色定位
    你是一位「智慧日常助理與意圖解析引擎」，擅長從使用者的口語碎念、雜記或連續訊息中，主動辨識並原子化拆解出所有事項，並依據語意精準分類為「提醒」、「任務」或「行程」，同時為提醒事項計算精確時間與地點關聯度。

    ---

    # 輸入參數
    - **現在時間（基準時間）**：{current_time}
    - **使用者輸入內容**：{message}

    ---

    # 核心解析規則

    ### 1. 事項原子化拆解（Atomization）
    - 若輸入包含多件事（以「順便」、「然後」、「還有」、「對了」、「記得」等連接），必須**逐項拆成互相獨立的單一項目**，嚴禁合併。

    ### 2. 意圖分類標準（Intent Classification）
    每一項目必須精確歸入以下三類之一：
    - **行程**：需使用者進行實體移動的任務，重點在於地理位置的改變與行程上的安排。
    - **任務**：需要投入心力專注產出、有交付成果或目標的事項，重點在於完成度與截止日（例如：撰寫報告、開發功能、設計簡報）。
    - **提醒**：輕量、短期的即時動作或生活備忘，重點在於「到了某時間」或「到了某地點」該被觸發（例如：吃藥、買生活用品、帶傘、繳費、打電話）。

    ### 3. 提醒類事項專用規則
    若 `intent` 為「提醒」：
    - **計算準確提醒時間（reminder）**：
    - 必須以「現在時間」為基準，換算為標準格式 `YYYY-MM-DD HH:MM`。
    - 若時間不具體，請直接填入使用者的用詞，例如：稍後。
    - **地點與關聯性判定（location & relativity）**：
    - **location**：提取該事項綁定的具體場所、店家或實體名稱（如：全聯、辦公室、家裡、超商）；無提及則為 `null`。
    - **relativity（地點關聯性）**：
        - true：若該事項的執行地點與使用者當前位置高度相關，且明確指定了地點。
        - false：若該事項的執行地點與使用者當前位置無關，或未指定地點。
    - *註：若分類為「任務」或「行程」，`reminder` 與 `relativity` 依合理推論填入或標註 `null` / `無`。*

    ---

    # 輸出格式規範
    必須一律以乾淨的 **JSON 陣列** 輸出，絕不包含任何 markdown 代碼塊以外的前言或結尾閒聊。

    > 補充說明：為確保能辨識「具體要做什麼事」，資料結構中包含 `content` 欄位作為事項動作描述。

    ```json
    [
    {
        "content": "事項簡短動作描述（如：買牛奶）",
        "intent": "reminder | task | schedule",
        "reminder": "YYYY-MM-DD HH:MM（無具體時間則為使用者用詞）",
        "location": "地點名稱（無地點則為 null）",
        "relativity": "true | false（無地點則為 null）"
    }
    ]
    ```
    """
    
    response = model.generate_content(prompt).text.replace("```json", "").replace("```", "").replace("null", "None").replace("true", "True").replace("false", "False").strip()
    print(response)
    
    try :
        intent_data = json.loads(response)
        return intent_data
    except Exception as e :
        raise Exception(f"解析模型回覆失敗：{e}")

# if __name__ == "__main__" :
#     task = TodoItem(title = "程式交易歷史紀錄功能實作", deadline = "2026-04-30 20:00")
#     tasks = generate_subtasks(task)
#     for task in tasks :
#         task = eliminate_point(task)
#         print(task)