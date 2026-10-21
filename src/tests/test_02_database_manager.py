import datetime
import json
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from src.shared.database_manager import (
    change_user_plan,
    delete_task,
    get_history,
    get_tasks,
    get_user,
    get_verify_code,
    init_user,
    push_history,
    push_task,
    push_verify_code,
)
from src.shared.models import ActualData, CompleteItem, EstimateData, TodoItem, User


# *Load mock data
@pytest.fixture
def read_mock_data():
    json_path = Path(__file__).parent / "mock_data.json"
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(autouse=True)
def mock_db():
    with patch("src.shared.database_manager.db.reference") as mock_db_reference:
        mock_ref = MagicMock()
        mock_db_reference.return_value = mock_ref

        yield mock_db_reference


@pytest.fixture
def mock_verify_env():
    with (
        patch("src.shared.database_manager.datetime") as mock_dt,
        patch("src.shared.database_manager.secrets") as mock_secrets,
    ):
        mock_dt.datetime.now.return_value.timestamp.return_value = 1000.0

        yield {"datetime": mock_dt, "secrets": mock_secrets}


# NOTE: test init_user
# Case1: normal user
def test_init_user(mock_db):
    user = User(user_id="test_user")

    init_user("test_user")

    mock_db.assert_called_once_with("test_user/profile")
    mock_db.return_value.set.assert_called_once_with(user.model_dump(mode="json", exclude={"user_id"}))


# Case2: wrong user_id
def test_init_user_with_wrong_user_id():
    with pytest.raises(ValueError):
        init_user(123)


# NOTE: test get_user
# Case1: normal use
def test_get_user(mock_db):
    user = User(user_id="test_user")
    mock_db.return_value.get.return_value = {"username": "user", "plan": "free"}

    result = get_user("test_user")

    mock_db.assert_called_once_with("test_user/profile")

    assert result.user_id == user.user_id


# Case2: wrong user_id
def test_get_user_with_wrong_user_id():
    with pytest.raises(ValueError):
        get_user(123)


# NOTE: test change_user_plan
# Case1: normal use change to free
def test_change_user_plan_to_free(mock_db):
    user_1 = User(user_id="test_user")
    change_user_plan("test_user", "free", None)
    mock_db.assert_called_with("test_user/profile")
    mock_db.return_value.set.assert_called_once_with(user_1.model_dump(mode="json", exclude={"user_id"}))


# Case2: normal use change to pro
def test_change_user_plan_to_pro(mock_db):
    user_2 = User(
        user_id="test_user", plan="pro", plan_exp=datetime.datetime(2020, 1, 1, 23, 59, 59), remain_ai_requesrt=None
    )
    change_user_plan("test_user", "pro", datetime.datetime(2020, 1, 1, 23, 59, 59))
    mock_db.assert_called_with("test_user/profile")
    mock_db.return_value.set.assert_called_once_with(user_2.model_dump(mode="json", exclude={"user_id"}))


# Case3: wrong user_id
def test_change_user_plan_with_wrong_user_id():
    with pytest.raises(ValueError):
        change_user_plan(123, "free", None)


# Case4: wrong plan
def test_change_user_plan_with_wrong_plan():
    with pytest.raises(ValueError):
        change_user_plan("test_user", "unknown", None)


# Case5: wrong exp_time
def test_change_user_plan_with_wrong_exp_time():
    with pytest.raises(TypeError):
        change_user_plan("test_user", "free", 1)

    with pytest.raises(TypeError):
        change_user_plan("test_user", "free")


# NOTE: test push_task
# Case1: push task
def test_push_task_task(read_mock_data, mock_db):

    task = read_mock_data["task_1"]
    task_estimate_data = task.pop("estimate_data")
    todo = TodoItem(estimate_data=EstimateData(**task_estimate_data), **task)

    push_task("test_user", todo)

    mock_db.assert_called_once_with(f"test_user/tasks/{todo.id}")
    mock_db.return_value.set.assert_called_once_with(todo.model_dump(mode="json", exclude={"id"}))


# Case2: wrong user_id
def test_push_task_with_wrong_id(read_mock_data):
    task = read_mock_data["task_1"]
    task_estimate_data = task.pop("estimate_data")
    todo = TodoItem(estimate_data=EstimateData(**task_estimate_data), **task)

    with pytest.raises(ValueError):
        push_task(123, todo)


# Case3: wrong data
def test_push_task_with_wrong_data(read_mock_data):
    task = read_mock_data["task_1"]

    with pytest.raises(TypeError):
        push_task("test_user", task)


# NOTE: test get_task
# Case1: normal use and all task
def test_get_task_all_task(read_mock_data, mock_db):
    task_1 = read_mock_data["task_1"]
    task_1_estimate_data = task_1.pop("estimate_data")
    todo_1 = TodoItem(estimate_data=EstimateData(**task_1_estimate_data), **task_1)

    task_2 = read_mock_data["task_2"]
    task_2_estimate_data = task_2.pop("estimate_data")
    todo_2 = TodoItem(estimate_data=EstimateData(**task_2_estimate_data), **task_2)

    mock_db.return_value.get.return_value = {
        str(todo_1.id): todo_1.model_dump(mode="json", exclude={"id"}, exclude_none=True),
        str(todo_2.id): todo_2.model_dump(mode="json", exclude={"id"}, exclude_none=True),
    }

    results = get_tasks("test_user")

    mock_db.assert_called_once_with("test_user/tasks")

    assert len(results) == 2
    assert results[0].title == todo_1.title
    assert results[1].title == todo_2.title


# Case2: normal use and exist task_id
def test_get_task_exist_task_id(read_mock_data, mock_db):
    task = read_mock_data["task_1"]
    task_estimate_data = task.pop("estimate_data")
    todo = TodoItem(estimate_data=EstimateData(**task_estimate_data), **task)
    mock_db.return_value.get.return_value = todo.model_dump(mode="json", exclude={"id"}, exclude_none=True)

    result = get_tasks("test_user", [str(todo.id)])

    mock_db.assert_called_once_with(f"test_user/tasks/{todo.id}")

    assert isinstance(result, list)
    assert isinstance(result[0], TodoItem)
    assert result[0].title == todo.title


# Case3: normal use and does not exist task_id
def test_get_task_does_not_exist_task_id(mock_db):
    mock_db.return_value.get.return_value = None

    result = get_tasks("test_user", ["none_task"])

    mock_db.assert_called_once_with("test_user/tasks/none_task")

    assert result == []


# Case4: wrong user_id
def test_get_task_with_wrong_user_id():
    with pytest.raises(ValueError):
        get_tasks(123, "task_1")


# Case5: wrong task_id
def test_get_task_with_wrong_task_id():
    with pytest.raises(TypeError):
        get_tasks("test_user", [123])

    with pytest.raises(TypeError):
        get_tasks("test_user", 123)


# NOTE: test delete_task
# Case1: delete task
def test_delete_task(mock_db, read_mock_data):
    task = read_mock_data["task_1"]
    task_estimate_data = task.pop("estimate_data")
    todo = TodoItem(estimate_data=EstimateData(**task_estimate_data), **task)
    delete_task("test_user", [{"task": str(todo.id)}])

    mock_db.assert_called_once_with(f"test_user/tasks/{todo.id}")
    mock_db.return_value.delete.assert_called_once()


# Case2: delete subtask (TODO)


# Case3: wrong user_id
def test_delete_task_with_wrong_user_id():
    with pytest.raises(ValueError):
        delete_task(123, [{"task": "test_task"}])


# Case4: wrong task_and_subtask_id while deleting task
def test_delete_task_with_wrong_task_and_subtask_id():
    with pytest.raises(TypeError):
        delete_task("test_user", {"task": "test_task"})

    with pytest.raises(TypeError):
        delete_task("test_user", [{"task": {"subtask": "test_task"}}])

    with pytest.raises(KeyError):
        delete_task("test_user", [{"unknown": "test_task"}])


# Case5: wrong task_and_subtask_id while deleting subtask (TODO)


# NOTE: test push_history
# Case1: normal use
def test_push_history(mock_db, read_mock_data):
    task = read_mock_data["completed_task_1"]
    actual_data = task.pop("actual_data")
    item = CompleteItem(actual_data=ActualData(**actual_data), **task)

    push_history("test_user", "2020_Q1", item)

    mock_db.assert_called_once_with(f"test_user/history/2020_Q1/{item.id}")
    mock_db.return_value.set.assert_called_once_with(item.model_dump(mode="json", exclude={"id"}))


# Case2: wrong user_id
def test_push_history_with_wrong_user_id(read_mock_data):
    task = read_mock_data["completed_task_1"]
    actual_data = task.pop("actual_data")
    item = CompleteItem(actual_data=ActualData(**actual_data), **task)

    with pytest.raises(ValueError):
        push_history(123, "2020_Q1", item)


# Case3: wrong file format
def test_push_history_with_wrong_file_format(read_mock_data):
    task = read_mock_data["completed_task_1"]
    actual_data = task.pop("actual_data")
    item = CompleteItem(actual_data=ActualData(**actual_data), **task)

    with pytest.raises(ValueError):
        push_history("test_user", "2020_Q0", item)


# Case4: wrong data
def test_push_history_with_wrong_data(read_mock_data):
    task = read_mock_data["completed_task_1"]

    with pytest.raises(TypeError):
        push_history("test_user", "2020_Q1", task)


# NOTE: test get_histiry
# Case1: normal use
def test_get_history(mock_db, read_mock_data):
    task_1 = read_mock_data["completed_task_1"]
    actual_data_1 = task_1.pop("actual_data")
    item_1 = CompleteItem(actual_data=ActualData(**actual_data_1), **task_1)
    task_2 = read_mock_data["completed_task_2"]
    actual_data_2 = task_2.pop("actual_data")
    item_2 = CompleteItem(actual_data=ActualData(**actual_data_2), **task_2)

    mock_db.return_value.get.side_effect = [
        {str(item_1.id): item_1.model_dump(mode="json", exclude={"id"})},
        {str(item_2.id): item_2.model_dump(mode="json", exclude={"id"})},
        None,
    ]

    results = get_history("test_user", "2020_Q4", 2)

    assert len(results) == 2
    assert results[0].id == item_1.id
    assert results[1].id == item_2.id

    mock_db.assert_has_calls(
        [call("test_user/history/2020_Q4"), call().get(), call("test_user/history/2020_Q3"), call().get()],
        any_order=False,
    )


# Case2: no enough file
def test_test_history_wihout_enoguh_file(mock_db, read_mock_data):
    task_1 = read_mock_data["completed_task_1"]
    actual_data_1 = task_1.pop("actual_data")
    item_1 = CompleteItem(actual_data=ActualData(**actual_data_1), **task_1)

    mock_db.return_value.get.side_effect = [{str(item_1.id): item_1.model_dump(mode="json", exclude={"id"})}, None]

    results = get_history("test_user", "2020_Q1", 2)

    assert len(results) == 1
    assert results[0].id == item_1.id

    mock_db.assert_has_calls(
        [call("test_user/history/2020_Q1"), call().get(), call("test_user/history/2019_Q4"), call().get()],
        any_order=False,
    )


# Case3 enough amout
def test_get_history_with_enough_amount(mock_db, read_mock_data):
    task_1 = read_mock_data["completed_task_1"]
    actual_data_1 = task_1.pop("actual_data")
    item_1 = CompleteItem(actual_data=ActualData(**actual_data_1), **task_1)
    task_2 = read_mock_data["completed_task_2"]
    actual_data_2 = task_2.pop("actual_data")
    item_2 = CompleteItem(actual_data=ActualData(**actual_data_2), **task_2)

    mock_db.return_value.get.side_effect = [
        {str(item_1.id): item_1.model_dump(mode="json", exclude={"id"})},
        {str(item_2.id): item_2.model_dump(mode="json", exclude={"id"})},
        None,
    ]

    results = get_history("test_user", "2020_Q1", 1)

    assert len(results) == 1
    assert results[0].id == item_1.id

    mock_db.assert_has_calls([call("test_user/history/2020_Q1"), call().get()], any_order=False)


# Case4: wrong user_id
def test_get_history_with_wrong_user_id():
    with pytest.raises(ValueError):
        get_history(123, "2020_Q4", 2)


# Case5: wrong start_file
def test_get_history_with_wrong_start_file():
    with pytest.raises(ValueError):
        get_history("test_user", "2020", 2)


# Case6: wrong amount
def test_get_history_with_wrong_amount():
    with pytest.raises(ValueError):
        get_history("test_user", "2020_Q4", -1)


# NOTE: test push_verify_code
# Case1: store does not exist code
def test_push_verify_code(mock_db):
    mock_db.return_value.get.return_value = None

    push_verify_code(111111, 5000.0)

    mock_db.assert_called_with("verify_code/111111")
    mock_db.return_value.set.assert_called_once_with({"status": "waiting", "exp_time": 5000.0})


# Case2: store exist code
def test_push_verify_code_exist_and_retry(mock_db, mock_verify_env):
    mock_verify_env["secrets"].randbelow.side_effect = [222222]

    mock_db.return_value.get.side_effect = [{"status": "waiting", "exp_time": 5000.0}, None]

    push_verify_code(111111, 5000.0)

    mock_db.assert_called_with("verify_code/222222")


# Case3: wrong code
def test_push_verify_code_with_wrong_code():
    with pytest.raises(ValueError):
        push_verify_code(1, 5000.0)


# Case4: wrong exp_time
def test_push_verify_code_with_wrong_exp_time():
    with pytest.raises(TypeError):
        push_verify_code(111111, "2020-01-01 23:59")


# Case5: wrong max_retries
def test_push_verify_code_with_wrong_max_retries():
    with pytest.raises(ValueError):
        push_verify_code(111111, 5000.0, -1)


# NOTE: test get_verify_code
# Case1: get valid code
def get_verify_code_valid(mock_db, mock_verify_env):
    mock_db.return_value.get.return_value = {"status": "waiting", "exp_time": 5000.0}

    status = get_verify_code(111111)

    mock_db.assert_called_once_with("verify_code/111111")
    assert status is True


# Case2: get expired code
def get_verify_code_expired(mock_db, mock_verify_env):
    mock_db.return_value.get.return_value = {"status": "waiting", "exp_time": 500.0}

    status = get_verify_code(111111)

    mock_db.assert_called_once_with("verify_code/111111")

    assert status is False


# Case3: wrong code
def get_verify_code_with_wrong_code(mock_db):
    with pytest.raises(ValueError):
        get_verify_code(1)
