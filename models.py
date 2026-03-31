from pydantic import BaseModel, Field, model_validator
from typing import List
import uuid

class SubtaskItem(BaseModel) :
    id: str = Field(default = lambda: str(uuid.uuid4()), description = "唯一識別指標，避免子任務重名覆蓋問題")
    title: str = Field(max_length = 15, description = "子任務標題，限制 15 字以內")
    deadline: str = Field(pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", description = "子任務截止日期，格式為 YYYY-MM-DD")
    
class TodoItem(BaseModel) :
    id: str = Field(default = lambda: str(uuid.uuid4()), description = "唯一識別指標，避免任務重名覆蓋問題")
    title: str = Field(max_length = 15, description = "任務標題，限制 15 字以內")
    deadline: str = Field(pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", description = "任務截止日期，格式為 YYYY-MM-DD")
    subtasks: List[SubtaskItem] = Field(default_factory=list, description = "子任務列表，預設為空列表")

class GCItem(BaseModel) :
    title: str = Field(alias = "title", description = "作業名稱")
    deadline: str
    
    @model_validator(mode = "before")
    @classmethod
    def validate_deadline(cls, values) :
        year = values["dueDate"]["year"]
        month = values["dueDate"]["month"]
        day = values["dueDate"]["day"]
        hour = values["dueTime"]["hour"]
        minute = values["dueTime"]["minute"]
        
        values["deadline"] = f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}"
        return values