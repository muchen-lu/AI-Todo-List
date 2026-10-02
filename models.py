from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Literal
import uuid
import datetime

# 儲存 AI 任務評估資訊
class EstimateData(BaseModel) :
    task_category: Literal["writing", "design", "development", "communication", "meeting", "research", "planning", "admin", "review", "learning", "other"] = Field(..., description = "任務類別")
    congnitive_load: int = Field(..., ge = 1, le = 5, description = "認知負荷量")
    estimated_time: int = Field(..., description = "預計消耗分鐘數")
    suggest_work_mode: Literal["deep", "shallow"] = Field(..., description = "建議工作模式")
    confidence: float = Field(..., ge = 0.0, le = 1.0, description = "AI 對於評估結果的信心程度，0~1")

class ActualData(BaseModel) :
    task_category: Literal["writing", "design", "development", "communication", "meeting", "research", "planning", "admin", "review", "learning", "other"] = Field(..., description = "任務類別")
    congnitive_load: int = Field(..., ge = 1, le = 5, description = "認知負荷量")
    actual_time: int = Field(..., description = "實際消耗分鐘數")
    work_mode: Literal["deep", "shallow"] = Field(..., description = "實際工作模式")

class SubtaskItem(BaseModel) :
    parent: str = Field(..., description = "父任務的 id")
    id: str = Field(default_factory = lambda: str(uuid.uuid4()), description = "唯一識別指標，避免子任務重名覆蓋問題")
    title: str = Field(..., description = "子任務標題")
    deadline: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", description = "子任務截止日期，格式為 YYYY-MM-DD")
    estimate_data: EstimateData = Field(..., description = "AI 對於子任務的評估資訊")
    actual_data: Optional[ActualData] = Field(None, description = "使用者對於子任務的實際資訊，預設為 None 代表尚未完成")
    
    @model_validator(mode = "before")
    @classmethod
    def validate_deadline(cls, values) :
        deadline = values.get("deadline").split(" ")
        date = deadline[0]
        if len(deadline) == 1 :
            time = "23:59"
        else :
            time = deadline[1]
        values["deadline"] = f"{date} {time}"
        
        return values

class CompleteData(BaseModel) :
    id: str = Field(..., description = "唯一識別指標，避免任務重名覆蓋問題")
    title: str = Field(..., description = "任務標題")
    deadline: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", description = "任務截止日期，格式為 YYYY-MM-DD")
    actual_data: ActualData = Field(..., description = "使用者對於任務的實際資訊")

class TodoItem(BaseModel) : # TODO: ONO 和正式 TODO 可以分開，用於區別是否有 subtasks、expect_point 與 used_point 等欄位
    id: str = Field(default_factory = lambda: str(uuid.uuid4()), description = "唯一識別指標，避免任務重名覆蓋問題")
    title: str = Field(description = "任務標題")
    deadline: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", description = "任務截止日期，格式為 YYYY-MM-DD")
    subtasks: Optional[List[SubtaskItem]] = Field(None, description = "子任務列表，預設為空列表")
    estimate_data: EstimateData = Field(..., description = "AI 對於任務的評估資訊")
    # actual_data: Optional[ActualData] = Field(None, description = "使用者對於任務的實際資訊，預設為 None 代表尚未完成")

class ONOItem(BaseModel) :
    title: str = Field(..., description = "任務名稱")
    deadline: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", description = "任務截止日期，格式為 YYYY-MM-DD")

class GCItem(BaseModel) :
    title: str = Field(alias = "title", description = "作業名稱")
    deadline: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", description = "作業截止日期，格式為 YYYY-MM-DD")

    @model_validator(mode = "before")
    @classmethod
    def validate_deadline(cls, values) :
        if "dueDate" in values :
            year = values["dueDate"]["year"]
            month = values["dueDate"]["month"]
            day = values["dueDate"]["day"]
            hour = values.get("dueTime", {}).get("hour", 23)
            minute = values.get("dueTime", {}).get("minute", 59)
            values["deadline"] = f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}"
        else :
            values["deadline"] = None
        
        return values
    
class CalendarEvent(BaseModel) :
    title: str = Field(alias = "summary", description = "事件名稱")
    today: bool = Field(default = False, description = "是否為當日事件")
    start: dict = Field(alias = "start", description = "事件開始時間，包含 dateTime 或 date")
    end: dict = Field(alias = "end", description = "事件結束時間，包含 dateTime 或 date")

    @model_validator(mode = "before")
    @classmethod
    def validate_long(cls, values) :
        start = values["start"].get("dateTime", values["start"].get("date"))
        end = values["end"].get("dateTime", values["end"].get("date"))
        if datetime.datetime.fromisoformat(start).date() <= datetime.datetime.now().date() <= datetime.datetime.fromisoformat(end).date() :
            values["today"] = True
        # values["long"] = int((datetime.datetime.fromisoformat(end) - datetime.datetime.fromisoformat(start)).total_seconds() // 60)
        return values