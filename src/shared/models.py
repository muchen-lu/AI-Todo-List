import datetime
import uuid
from typing import Literal

from pydantic import BaseModel, Field, field_serializer, model_validator


# User Data
class User(BaseModel):
    user_id: str = Field(..., description="Line User ID")
    username: str = Field("user", description="User nickname")
    plan: Literal["free", "pro"] = Field("free", description="Current plan level")
    plan_exp: datetime.datetime | None = Field(None, description="Current plan expire time")
    remain_ai_requesrt: int | None = Field(5, description="Left AI Request / per day")


# AI estimate infomations
class EstimateData(BaseModel):
    task_category: Literal[
        "writing",
        "design",
        "development",
        "communication",
        "meeting",
        "research",
        "planning",
        "admin",
        "review",
        "learning",
        "other",
    ] = Field(..., description="Task category")
    congnitive_load: int = Field(..., ge=1, le=5, description="Cognitive load level (1-5)")
    estimated_time: int = Field(..., description="Estimated time in minutes")
    suggest_work_mode: Literal["deep", "shallow"] = Field(..., description="Suggested work mode")
    confidence: float = Field(..., ge=0.0, le=1.0, description="AI Confidence level (0.0-1.0)")


# User execute infomations
class ActualData(BaseModel):
    task_category: Literal[
        "writing",
        "design",
        "development",
        "communication",
        "meeting",
        "research",
        "planning",
        "admin",
        "review",
        "learning",
        "other",
    ] = Field(..., description="Task category")
    congnitive_load: int = Field(..., ge=1, le=5, description="Cognitive load level (1-5)")
    actual_time: int = Field(..., description="Actual time in minutes")
    work_mode: Literal["deep", "shallow"] = Field(..., description="Actual work mode")


# Subtask infomations
class SubtaskItem(BaseModel):
    parent: uuid.UUID = Field(..., description="Parent task ID")
    id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Subtask ID")
    title: str = Field(..., description="Subtask title")
    deadline: datetime.datetime | None = Field(None, description="Subtask deadline")
    estimate_data: EstimateData = Field(..., description="AI estimate data for the subtask")

    @field_serializer("deadline")
    def format_deadline(self, dt: datetime.datetime | None) -> str | None:
        if dt:
            return datetime.datetime.strftime(dt, "%Y-%m-%d %H:%M")
        return None


# Task infomations
class TodoItem(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Task ID")
    title: str = Field(..., description="Task title")
    deadline: datetime.datetime | None = Field(None, description="Task deadline")
    estimate_data: EstimateData = Field(..., description="AI estimate data for the task")
    subtasks: list[SubtaskItem] | None = Field(None, description="List of subtasks")

    @field_serializer("deadline")
    def format_deadline(self, dt: datetime.datetime | None) -> str | None:
        if dt:
            return datetime.datetime.strftime(dt, "%Y-%m-%d %H:%M")
        return None


# History infomations
class CompleteItem(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, description="History ID")
    title: str = Field(..., description="Task title")
    completed_at: datetime.datetime = Field(default_factory=datetime.datetime.now, description="Completion timestamp")
    actual_data: ActualData = Field(..., description="User actual data for the task")

    @field_serializer("completed_at")
    def format_deadline(self, dt: datetime.datetime) -> str:
        return datetime.datetime.strftime(dt, "%Y-%m-%d %H:%M")


# ONO task infomations
class ONOItem(BaseModel):
    title: str = Field(..., description="Task title")
    deadline: datetime.datetime = Field(..., description="Task deadline")

    @field_serializer("deadline")
    def format_deadline(self, dt: datetime.datetime) -> str:
        return datetime.datetime.strftime(dt, "%Y-%m-%d %H:%M")


# Google Classroom task infomations
class GCItem(BaseModel):
    title: str = Field(alias="title", description="Homework name")
    deadline: datetime.datetime | None = Field(..., description="Homework deadline")

    @model_validator(mode="before")
    @classmethod
    def validate_deadline(cls, values):
        if "dueDate" in values:
            year = values["dueDate"]["year"]
            month = values["dueDate"]["month"]
            day = values["dueDate"]["day"]
            hour = values.get("dueTime", {}).get("hour", 23)
            minute = values.get("dueTime", {}).get("minute", 59)
            values["deadline"] = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute)
        else:
            values["deadline"] = (datetime.datetime.now() + datetime.timedelta(days=7)).replace(
                hour=23, minute=59, second=0, microsecond=0
            )
        return values

    @field_serializer("deadline")
    def format_deadline(self, dt: datetime.datetime) -> str | None:
        if dt:
            return datetime.datetime.strftime(dt, "%Y-%m-%d %H:%M")
        return None


# Google Calendar event infomations
class CalendarEvent(BaseModel):
    title: str = Field(alias="summary", description="Event title")
    start: datetime.datetime = Field(alias="start", description="Event start time")
    end: datetime.datetime = Field(alias="end", description="Event end time")

    @model_validator(mode="before")
    @classmethod
    def validate_time(cls, values):
        values["start"] = values["start"].get("dateTime", values["start"].get("date"))
        values["end"] = values["end"].get("dateTime", values["end"].get("date"))
        return values

    @field_serializer("start", "end")
    def format_reminder_time(self, dt: datetime.datetime) -> str:
        return datetime.datetime.strftime(dt, "%Y-%m-%d %H:%M")


# reminder infomations
class ReminderItem(BaseModel):
    title: str = Field(..., description="Reminder content")
    reminder_time: datetime.datetime = Field(..., description="Reminder time")
    location: str | None = Field(None, description="Place name, default as None")
    relativity: bool | None = Field(None, description="Relativity between reminder and place")

    @field_serializer("reminder_time")
    def format_reminder_time(self, dt: datetime.datetime) -> str:
        return datetime.datetime.strftime(dt, "%Y-%m-%d %H:%M")
