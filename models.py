from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
import uuid

class SubtaskItem(BaseModel) :
    id: str = Field(default_factory = lambda: str(uuid.uuid4()), description = "唯一識別指標，避免子任務重名覆蓋問題")
    title: str = Field(description = "子任務標題")
    deadline: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", description = "子任務截止日期，格式為 YYYY-MM-DD")
    
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
    
class TodoItem(BaseModel) :
    id: str = Field(default_factory = lambda: str(uuid.uuid4()), description = "唯一識別指標，避免任務重名覆蓋問題")
    title: str = Field(description = "任務標題")
    deadline: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", description = "任務截止日期，格式為 YYYY-MM-DD")
    subtasks: Optional[List[SubtaskItem]] = Field(None, description = "子任務列表，預設為空列表")

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