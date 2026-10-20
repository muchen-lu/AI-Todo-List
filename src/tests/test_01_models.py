import datetime
import json
import uuid
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.shared.models import (
    ActualData,
    CalendarEvent,
    CompleteItem,
    EstimateData,
    GCItem,
    ONOItem,
    ReminderItem,
    SubtaskItem,
    TodoItem,
)


# *Load mock data
@pytest.fixture
def read_mock_data():
    json_path = Path(__file__).parent / "mock_data.json"
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)


# NOTE: test SubtaskItem
# Case1: test uuid generate function
def test_subtask_item_uuid_generation(read_mock_data):
    task_1 = read_mock_data["task_1"]
    task_2 = read_mock_data["task_2"]
    subtask_1 = SubtaskItem(
        parent=uuid.uuid4(),
        title=task_1["title"],
        deadline=datetime.datetime.strptime(task_1["deadline"], "%Y-%m-%d %H:%M"),
        estimate_data=EstimateData(
            task_category=task_1["estimate_data"]["task_category"],
            congnitive_load=task_1["estimate_data"]["congnitive_load"],
            estimated_time=task_1["estimate_data"]["estimated_time"],
            suggest_work_mode=task_1["estimate_data"]["suggest_work_mode"],
            confidence=task_1["estimate_data"]["confidence"],
        ),
    )
    subtask_2 = SubtaskItem(
        parent=uuid.uuid4(),
        title=task_2["title"],
        deadline=datetime.datetime.strptime(task_2["deadline"], "%Y-%m-%d %H:%M"),
        estimate_data=EstimateData(
            task_category=task_2["estimate_data"]["task_category"],
            congnitive_load=task_2["estimate_data"]["congnitive_load"],
            estimated_time=task_2["estimate_data"]["estimated_time"],
            suggest_work_mode=task_2["estimate_data"]["suggest_work_mode"],
            confidence=task_2["estimate_data"]["confidence"],
        ),
    )

    assert subtask_1.id != subtask_2.id


# Case2: test export deadline content format
def test_subtask_item_deadline_export(read_mock_data):
    task_1 = read_mock_data["task_1"]
    subtask_1 = SubtaskItem(
        parent=uuid.uuid4(),
        title=task_1["title"],
        deadline=datetime.datetime.strptime(task_1["deadline"], "%Y-%m-%d %H:%M"),
        estimate_data=EstimateData(
            task_category=task_1["estimate_data"]["task_category"],
            congnitive_load=task_1["estimate_data"]["congnitive_load"],
            estimated_time=task_1["estimate_data"]["estimated_time"],
            suggest_work_mode=task_1["estimate_data"]["suggest_work_mode"],
            confidence=task_1["estimate_data"]["confidence"],
        ),
    )

    assert isinstance(subtask_1.deadline, datetime.datetime)
    assert isinstance(subtask_1.model_dump()["deadline"], str)


# Case3: test wrong deadline input data type
def test_subtask_item_wrong_deadline_input(read_mock_data):
    task_1 = read_mock_data["task_1"]
    with pytest.raises(ValidationError):
        SubtaskItem(
            parent=uuid.uuid4(),
            title=task_1["title"],
            deadline="tomorrow",
            estimate_data=EstimateData(
                task_category=task_1["estimate_data"]["task_category"],
                congnitive_load=task_1["estimate_data"]["congnitive_load"],
                estimated_time=task_1["estimate_data"]["estimated_time"],
                suggest_work_mode=task_1["estimate_data"]["suggest_work_mode"],
                confidence=task_1["estimate_data"]["confidence"],
            ),
        )


# NOTE: test TodoItem
# Case1: test uuid generate function
def test_todo_item_uuid_generation(read_mock_data):
    task_1 = read_mock_data["task_1"]
    task_2 = read_mock_data["task_2"]
    todo_1 = TodoItem(
        title=task_1["title"],
        deadline=datetime.datetime.strptime(task_1["deadline"], "%Y-%m-%d %H:%M"),
        estimate_data=EstimateData(
            task_category=task_1["estimate_data"]["task_category"],
            congnitive_load=task_1["estimate_data"]["congnitive_load"],
            estimated_time=task_1["estimate_data"]["estimated_time"],
            suggest_work_mode=task_1["estimate_data"]["suggest_work_mode"],
            confidence=task_1["estimate_data"]["confidence"],
        ),
    )
    todo_2 = TodoItem(
        title=task_2["title"],
        deadline=datetime.datetime.strptime(task_2["deadline"], "%Y-%m-%d %H:%M"),
        estimate_data=EstimateData(
            task_category=task_2["estimate_data"]["task_category"],
            congnitive_load=task_2["estimate_data"]["congnitive_load"],
            estimated_time=task_2["estimate_data"]["estimated_time"],
            suggest_work_mode=task_2["estimate_data"]["suggest_work_mode"],
            confidence=task_2["estimate_data"]["confidence"],
        ),
    )

    assert todo_1.id != todo_2.id


# Case2: test export deadline content format
def test_todo_item_deadline_export(read_mock_data):
    task_1 = read_mock_data["task_1"]
    todo_1 = TodoItem(
        title=task_1["title"],
        deadline=datetime.datetime.strptime(task_1["deadline"], "%Y-%m-%d %H:%M"),
        estimate_data=EstimateData(
            task_category=task_1["estimate_data"]["task_category"],
            congnitive_load=task_1["estimate_data"]["congnitive_load"],
            estimated_time=task_1["estimate_data"]["estimated_time"],
            suggest_work_mode=task_1["estimate_data"]["suggest_work_mode"],
            confidence=task_1["estimate_data"]["confidence"],
        ),
    )

    assert isinstance(todo_1.deadline, datetime.datetime)
    assert isinstance(todo_1.model_dump()["deadline"], str)


# Case3: test wrong deadline input data type
def test_todo_item_wrong_deadline_input(read_mock_data):
    task_1 = read_mock_data["task_1"]
    with pytest.raises(ValidationError):
        TodoItem(
            title=task_1["title"],
            deadline="tomorrow",
            estimate_data=EstimateData(
                task_category=task_1["estimate_data"]["task_category"],
                congnitive_load=task_1["estimate_data"]["congnitive_load"],
                estimated_time=task_1["estimate_data"]["estimated_time"],
                suggest_work_mode=task_1["estimate_data"]["suggest_work_mode"],
                confidence=task_1["estimate_data"]["confidence"],
            ),
        )


# NOTE: test CompleteItem
# Case1: test uuid generate function
def test_complete_item_uuid_generation(read_mock_data):
    task_1 = read_mock_data["completed_task_1"]
    task_2 = read_mock_data["completed_task_2"]
    complete_1 = CompleteItem(
        title=task_1["title"],
        actual_data=ActualData(
            task_category=task_1["actual_data"]["task_category"],
            congnitive_load=task_1["actual_data"]["congnitive_load"],
            actual_time=task_1["actual_data"]["actual_time"],
            work_mode=task_1["actual_data"]["work_mode"],
        ),
    )
    complete_2 = CompleteItem(
        title=task_2["title"],
        actual_data=ActualData(
            task_category=task_2["actual_data"]["task_category"],
            congnitive_load=task_2["actual_data"]["congnitive_load"],
            actual_time=task_2["actual_data"]["actual_time"],
            work_mode=task_2["actual_data"]["work_mode"],
        ),
    )

    assert complete_1.id != complete_2.id


# Case2: test complete time stamp generation function
def test_complete_item_completed_at_generation(read_mock_data):
    task_1 = read_mock_data["completed_task_1"]
    complete_1 = CompleteItem(
        title=task_1["title"],
        actual_data=ActualData(
            task_category=task_1["actual_data"]["task_category"],
            congnitive_load=task_1["actual_data"]["congnitive_load"],
            actual_time=task_1["actual_data"]["actual_time"],
            work_mode=task_1["actual_data"]["work_mode"],
        ),
    )

    assert complete_1.completed_at is not None


# Case3: test export complete_at content format
def test_complete_item_completed_at_export(read_mock_data):
    task_1 = read_mock_data["completed_task_1"]
    complete_1 = CompleteItem(
        title=task_1["title"],
        actual_data=ActualData(
            task_category=task_1["actual_data"]["task_category"],
            congnitive_load=task_1["actual_data"]["congnitive_load"],
            actual_time=task_1["actual_data"]["actual_time"],
            work_mode=task_1["actual_data"]["work_mode"],
        ),
    )

    assert isinstance(complete_1.completed_at, datetime.datetime)
    assert isinstance(complete_1.model_dump()["completed_at"], str)


# NOTE: test ONOItem
# Case1: test export deadline content format
def test_ono_item_deadline_export(read_mock_data):
    task_1 = read_mock_data["task_1"]
    ono_1 = ONOItem(
        title=task_1["title"],
        deadline=datetime.datetime.strptime(task_1["deadline"], "%Y-%m-%d %H:%M"),
    )

    assert isinstance(ono_1.deadline, datetime.datetime)
    assert isinstance(ono_1.model_dump()["deadline"], str)


# Case2: test wrong deadline input data type


# NOTE: test GCItem
# Case1: test title alias
def test_gc_item_title_autofill(read_mock_data):
    task_1 = read_mock_data["google_classroom_api_response"]
    gc_1 = GCItem(**task_1)

    assert gc_1.title == task_1["title"]


# Case2: test export deadline content format
def test_gc_item_deadline_export(read_mock_data):
    task_1 = read_mock_data["google_classroom_api_response"]
    gc_1 = GCItem(**task_1)

    assert isinstance(gc_1.deadline, datetime.datetime)
    assert isinstance(gc_1.model_dump()["deadline"], str)


# NOTE: test CalendarEvent
# Case1: test summary alias
def test_calendar_event_title_autofill(read_mock_data):
    event_1 = read_mock_data["google_calendar_event_time"]
    calendar_1 = CalendarEvent(**event_1)

    assert calendar_1.title == event_1["summary"]


# Case2: test start and end alias
def test_calendar_event_start_and_end_autofill(read_mock_data):
    event_1 = read_mock_data["google_calendar_event_time"]
    event_2 = read_mock_data["google_calendar_event_day"]
    calendar_1 = CalendarEvent(**event_1)
    calendar_2 = CalendarEvent(**event_2)

    assert calendar_1.start is not None
    assert calendar_1.end is not None
    assert calendar_2.start is not None
    assert calendar_2.end is not None


# Case3: test export start and end content format
def test_calendar_ebvent_start_and_end_export(read_mock_data):
    event_1 = read_mock_data["google_calendar_event_time"]
    event_2 = read_mock_data["google_calendar_event_day"]
    calendar_1 = CalendarEvent(**event_1)
    calendar_2 = CalendarEvent(**event_2)

    assert isinstance(calendar_1.start, datetime.datetime)
    assert isinstance(calendar_1.model_dump()["start"], str)
    assert isinstance(calendar_1.end, datetime.datetime)
    assert isinstance(calendar_1.model_dump()["end"], str)

    assert isinstance(calendar_2.start, datetime.datetime)
    assert isinstance(calendar_2.model_dump()["start"], str)
    assert isinstance(calendar_2.end, datetime.datetime)
    assert isinstance(calendar_2.model_dump()["end"], str)


# NOTE: test ReminderItem
# Case1: test reminder_time export content format
def test_reminder_item_reminder_time_export(read_mock_data):
    item_1 = read_mock_data["reminder_1"]
    reminder_1 = ReminderItem(title=item_1["title"], reminder_time=item_1["reminder_time"])

    assert isinstance(reminder_1.reminder_time, datetime.datetime)
    assert isinstance(reminder_1.model_dump()["reminder_time"], str)
