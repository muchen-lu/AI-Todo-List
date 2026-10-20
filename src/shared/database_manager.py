import datetime
import os
import re
import secrets
import uuid

import firebase_admin
from firebase_admin import credentials, db
from google.api_core import exceptions as google_exceptions

from src.shared.config import get_settings
from src.shared.logger import logger
from src.shared.models import ActualData, CompleteItem, EstimateData, SubtaskItem, TodoItem

settings = get_settings()


class DatabaseError(Exception):
    pass


class DatabaseTimeout(DatabaseError):
    pass


class QuotaExceeded(DatabaseError):
    pass


if os.path.exists("firebase_key.json"):
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred, {"databaseURL": settings.database_url})
    logger.info("Initialize Firebase Database Success.")
else:
    logger.error("Initialize Firebase Database failed: firebase_key.json file does not exist.")


def push_task(user_id: str, data: TodoItem):  # TODO: 未來要做新增子任務的功能
    """Push data to user's realtime database

    Args:
        user_id (str): specified user id.
        data (TodoItem): task data.

    Raises:
        ValueError: Raises when does not receive user_id or user_id is not string.
        TypeError: Raises when data is not TodoItem
        DatabaseTimeout: Raises when connect over 5 seconds.
        QuotaExceeded: Raises when writing quota reached the limitation.
        DatabaseError: Raises when unknown error occured.
    """
    if not user_id or not isinstance(user_id, str):
        logger.error("Recieved invalid user_id")
        raise ValueError("Invalid user_id")
    if not isinstance(data, TodoItem):
        logger.error("Recieved invalid data")
        raise TypeError("Data must be a TodoItem")

    logger.info(f"Pushing '{data.title}' task to {user_id}'s database...")

    try:
        db.reference(f"{user_id}/tasks/{data.id}").set(data.model_dump(mode="json", exclude={"id"}))
        logger.info("Push data success.")
    except (google_exceptions.DeadlineExceeded, google_exceptions.ServiceUnavailable) as e:
        logger.debug(f"Firebase Timeout: {str(e)}")
        raise DatabaseTimeout("Database timeout, please try later.")
    except google_exceptions.ResourceExhausted:
        logger.warning("Firebase Resources exhausted.")
        raise QuotaExceeded("Database quota reaches the limitation.")
    except Exception as e:
        logger.opt(exception=True).debug(f"Unknown error occur in Firebase: {str(e)}")
        raise DatabaseError(f"Database process failed: {str(e)}")


def get_tasks(user_id: str, task_id: list[str] | None = None) -> list[TodoItem | None]:
    """Get all tasks or specific tasks from user's realtime database.

    Args:
        user_id (str): specified user id.
        task_id (list[str] | None, optional): specified task id. Defaults to None means all tasks.

    Raises:
        ValueError: Raises when does not recieve user_id or user_id is not string.
        TypeError: Raises when task id does not fit format.
        KeyError: Raises when realtime database tasks structure is different from TodoItem.
        DatabaseTimeout: Raises when connect over 5 seconds.
        QuotaExceeded: Raises when reading quota reached the limitation.
        DatabaseError: Raises when unknown error occured.

    Returns:
        list[TodoItem | None]: tasks information.
    """
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Recieved invalid user_id: {user_id}")
        raise ValueError("Invalid user_id")
    if task_id is not None and (not isinstance(task_id, list) or not all(isinstance(item, str) for item in task_id)):
        logger.error("Recieved invalid task ids")
        raise TypeError("task_id must be list[str] type.")

    logger.info(f"Start getting {str(len(task_id)) if task_id else 'all'} tasks from {user_id}'s database.")

    datas: list[TodoItem | None] = []
    try:
        match task_id:
            case None:
                data = db.reference(f"{user_id}/tasks").get()
                # logger.debug(data)
                if data is None:
                    logger.info("Firebase get 0 task.")
                else:
                    for database_id, task_data in data.items():
                        estimate_data = task_data.pop("estimate_data")
                        subtasks = task_data.pop("subtasks", {})

                        item = TodoItem(
                            id=database_id,
                            estimate_data=EstimateData(**estimate_data),
                            subtasks=[
                                SubtaskItem(id=subtask_id, **subtask) for subtask_id, subtask in subtasks.items()
                            ],
                            **task_data,
                        )
                        datas.append(item)
            case _:
                for single_task_id in task_id:
                    data = db.reference(f"{user_id}/tasks/{single_task_id}").get()
                    if data is None:
                        logger.warning(f"No task id {single_task_id} found in Firebase.")
                        continue
                    estimate_data = data.pop("estimate_data")
                    subtasks = data.pop("subtasks", {})

                    item = TodoItem(
                        id=uuid.UUID(single_task_id),
                        estimate_data=EstimateData(**estimate_data),
                        subtasks=[SubtaskItem(id=subtask_id, **subtask) for subtask_id, subtask in subtasks.items()],
                        **data,
                    )
                    datas.append(item)
        logger.info("Getting tasks success.")
        return datas
    except KeyError:
        logger.error("Firebase tasks structure is broken")
        raise KeyError("Tasks structure is broken.")
    except (google_exceptions.DeadlineExceeded, google_exceptions.ServiceUnavailable) as e:
        logger.debug(f"Firebase Timeout: {str(e)}")
        raise DatabaseTimeout("Database timeout, please try later.")
    except google_exceptions.ResourceExhausted:
        logger.warning("Firebase Resources exhausted.")
        raise QuotaExceeded("Database quota reaches the limitation.")
    except Exception as e:
        logger.opt(exception=True).debug(f"Unknown error occur in Firebase: {str(e)}")
        raise DatabaseError(f"Database process failed: {str(e)}")


def delete_task(user_id: str, task_and_subtask_id: list[dict[str, str | dict[str, str]]]):
    """Delete specified tasks from user's realtime database.

    Args:
        user_id (str): specified user id.
        task_and_subtask_id (list[dict[str, str | dict[str, str]]]): specified tasks and subtasks ids.
                                                                     Key must be "task" or "subtask"

    Raises:
        ValueError: Raises when does no recieve user_id or user_id is not string.
        TypeError: Raises when task_and_subtask_id value is not string while deleting task or
                   not dictionary while deleting subtask.
        KeyError: Raises when recieved unknown task_and_subtask_id key.
        DatabaseTimeout: Raises when connect over 5 seconds.
        QuotaExceeded: Raises when deleting quota reached the limitation.
        DatabaseError: Raises when unknown error occured.
    """
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Recieved invalid user_id: {user_id}")
        raise ValueError("Invalid user_id")
    if task_and_subtask_id is not None and (
        not isinstance(task_and_subtask_id, list) or not all(isinstance(item, dict) for item in task_and_subtask_id)
    ):
        logger.error("Recieved invalid task_and_subtask ids")
        raise TypeError("task_and_subtask_id must be list[dict] type.")

    logger.info(f"Start deleting tasks and subtasks from {user_id}'s database")

    try:
        for item in task_and_subtask_id:
            match list(item.keys())[0]:
                case "task":
                    if not isinstance(item["task"], str):
                        logger.error(f"Received wrong type id when deleting task: {item['task']}")
                        raise TypeError("Wrong id type")
                    db.reference(f"{user_id}/tasks/{item['task']}").delete()
                    logger.info(f"Deleting task {item['task']} success")
                case "subtask":
                    if not isinstance(item["task"], dict):
                        logger.error(f"Received wrong type content when deleting subtask: {item['task']}")
                        raise TypeError("Wrong content type")
                    db.reference(
                        f"{user_id}/tasks/{list(item['task'].keys())[0]}/{list(item['task'].items())[0]}"
                    ).delete()
                    logger.info(f"Deleting subtask {list(item['task'].items())[0]} success")
                case _:
                    logger.error("Recieved invalid key while deleting task or subtask.")
                    raise KeyError("Recieved invalid key, must be task or subtask.")
    except TypeError as e:
        raise TypeError(e)
    except KeyError:
        logger.error("Recieved unknown key in task_and_subtask_id. It must be task or subtask.")
        raise KeyError("Recieved unknown key")
    except (google_exceptions.DeadlineExceeded, google_exceptions.ServiceUnavailable) as e:
        logger.debug(f"Firebase Timeout: {str(e)}")
        raise DatabaseTimeout("Database timeout, please try later.")
    except google_exceptions.ResourceExhausted:
        logger.warning("Firebase Resources exhausted.")
        raise QuotaExceeded("Database quota reaches the limitation.")
    except Exception as e:
        logger.opt(exception=True).debug(f"Unknown error occur in Firebase: {str(e)}")
        raise DatabaseError(f"Database process failed: {str(e)}")


def push_history(user_id: str, file: str, data: CompleteItem):
    """Push user history to user's realtime database.

    Args:
        user_id (str): specified user id
        file (str): history file, must be YYYY_Q1/2/3/4
        data (CompleteItem): complete task data

    Raises:
        ValueError: Raises when does not receive user_id or user_id is not string or file does not follow the format.
        DatabaseTimeout: Raises when connect over 5 seconds.
        QuotaExceeded: Raises when writing quota reached the limitation.
        DatabaseError: Raises when unknown error occured.
    """
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Recieved invalid user_id: {user_id}")
        raise ValueError("Invalid user_id")
    if not re.fullmatch(r"^\d{4}_Q[1-4]$", file):
        logger.error(f"Recieved wrong file name: {file}")
        raise ValueError("Invalid file name")
    if not isinstance(data, CompleteItem):
        logger.error("Recieved wrong data type")
        raise TypeError("data must be CompleteItem")

    try:
        db.reference(f"{user_id}/history/{file}/{str(data.id)}").set(data.model_dump(mode="json", exclude={"id"}))
    except (google_exceptions.DeadlineExceeded, google_exceptions.ServiceUnavailable) as e:
        logger.debug(f"Firebase Timeout: {str(e)}")
        raise DatabaseTimeout("Database timeout, please try later.")
    except google_exceptions.ResourceExhausted:
        logger.warning("Firebase Resources exhausted.")
        raise QuotaExceeded("Database quota reaches the limitation.")
    except Exception as e:
        logger.opt(exception=True).debug(f"Unknown error occur in Firebase: {str(e)}")
        raise DatabaseError(f"Database process failed: {str(e)}")


def get_history(user_id: str, start_file: str, amount: int = 50) -> list[CompleteItem | None]:
    """Get specific amount of history from user's database

    Args:
        user_id (str): specified user id
        start_file (str): Assign which file start to inquiry history. Must be YYYY_Q1/2/3/4
        amount (int): Set max amount of history.

    Raises:
        ValueError: Raises when does not receive user_id or user_id is not string or file does not follow the format.
        DatabaseTimeout: Raises when connect over 5 seconds.
        QuotaExceeded: Raises when reading quota reached the limitation.
        DatabaseError: Raises when unknown error occured.

    Returns:
        list[CompleteItem | None]: Histories. Return empty list if no histories was found.
    """

    def _change_file(now_file: str) -> str:
        year = now_file.split("_Q")[0]
        quarter = now_file.split("_Q")[-1]
        int_quarter = int(quarter) - 1 if int(quarter) - 1 > 0 else 4
        if int_quarter == 4:
            int_year = int(year) - 1
        else:
            int_year = int(year)
        return f"{int_year}_Q{int_quarter}"

    if not user_id or not isinstance(user_id, str):
        logger.error(f"Recieved invalid user_id: {user_id}")
        raise ValueError("Invalid user_id")
    if not re.fullmatch(r"^\d{4}_Q[1-4]$", start_file):
        logger.error(f"Recieved wrong file name: {start_file}")
        raise ValueError("Invalid file name")
    if amount <= 0:
        logger.warning(f"Recieved invalid amount: {amount}")
        raise ValueError("amount must over 0.")

    logger.info(f"Strat reading {amount} histories from {user_id}'s database. (start from {start_file})")

    histories: list[CompleteItem | None] = []
    try:
        while True:
            logger.debug(f"Reading {start_file}")
            history = db.reference(f"{user_id}/history/{start_file}").get()
            if history is None:
                logger.info(f"{start_file} does not exist, stop getting histories.")
                return histories

            for history_id, data in history.items():
                actual_data = data.pop("actual_data")

                item = CompleteItem(id=history_id, actual_data=ActualData(**actual_data), **data)
                histories.append(item)

                if len(histories) == amount:
                    logger.info(f"History data reach {amount} amount, stop getting histories.")
                    return histories
            start_file = _change_file(start_file)

    except KeyError:
        logger.error("Firebase history structure is broken", exc_info=True)
        raise KeyError("History structure is broken.")
    except (google_exceptions.DeadlineExceeded, google_exceptions.ServiceUnavailable) as e:
        logger.debug(f"Firebase Timeout: {str(e)}")
        raise DatabaseTimeout("Database timeout, please try later.")
    except google_exceptions.ResourceExhausted:
        logger.warning("Firebase Resources exhausted.")
        raise QuotaExceeded("Database quota reaches the limitation.")
    except Exception as e:
        logger.opt(exception=True).debug(f"Unknown error occur in Firebase: {str(e)}")
        raise DatabaseError(f"Database process failed: {str(e)}")


def push_verify_code(code: int, exp_time: float, max_retries: int = 10):
    """Push verify code to database.

    Args:
        code (int): verify code
        exp_time (float): timestamp
        max_retries (int, optional): Max retries if verify code already exist. Defaults to 10.

    Raises:
        TypeError: Raises if code is not an integer.
        ValueError: Raises if code is not 6 number.
        RuntimeError: Raises if cannot generate code successfully.
        DatabaseTimeout: Raises when connect over 5 seconds.
        QuotaExceeded: Raises when writing quota reached the limitation.
        DatabaseError: Raises when unknown error occured.
    """
    if not isinstance(code, int):
        logger.error(f"Variable 'code' must be an integer: {code}")
        raise TypeError("Does not recieved an integer variable.")
    if not (100000 <= code and code <= 999999):
        logger.error(f"Recieved invalid verify code: {code}")
        raise ValueError("code does not fit the format.")
    if not isinstance(exp_time, float):
        logger.error("exp_time must be a float")
        raise TypeError("Doesn't recieved a timestamp.")
    if max_retries < 0:
        logger.error(f"Recieved invalid max_retries: {max_retries}")
        raise ValueError("max_retries must over 0.")

    logger.info(f"Start pushing verify code {code} to database.")

    try:
        for _ in range(max_retries + 1):
            data = db.reference(f"verify_code/{code}").get()
            if not (data is None or data["exp_time"] < datetime.datetime.now().timestamp()):
                logger.warning(f"Verify code {code} already exist, try again.")
                code = int(f"{secrets.randbelow(1000000):06d}")
                continue
            db.reference(f"verify_code/{code}").set({"status": "waiting", "exp_time": exp_time})
            logger.info("Verify code write success.")
            return
        logger.warning(f"Verify code retry {max_retries} times but still failed.")
        raise RuntimeError("Cannot generate verify code, please try again later.")
    except (google_exceptions.DeadlineExceeded, google_exceptions.ServiceUnavailable) as e:
        logger.debug(f"Firebase Timeout: {str(e)}")
        raise DatabaseTimeout("Database timeout, please try later.")
    except google_exceptions.ResourceExhausted:
        logger.warning("Firebase Resources exhausted.")
        raise QuotaExceeded("Database quota reaches the limitation.")
    except Exception as e:
        logger.opt(exception=True).debug(f"Unknown error occur in Firebase: {str(e)}")
        raise DatabaseError(f"Database process failed: {str(e)}")


def get_verify_code(code: int) -> bool:
    """Get specified verify code. And delete

    Args:
        code (int): specified verify code

    Raises:
        TypeError: Raises if recieved code is not integer.
        DatabaseTimeout: Raises when connect over 5 seconds.
        QuotaExceeded: Raises when reading quota reached the limitation.
        DatabaseError: Raises when unknown error occured.

    Returns:
        bool: Return True if verify success else return False
    """
    if not isinstance(code, int):
        logger.error(f"Variable 'code' must be an integer: {code}")
        raise TypeError("Does not recieved an integer variable.")
    if not (100000 <= code and code <= 999999):
        logger.error(f"Recieved invalid verify code: {code}")
        raise ValueError("code does not fit the format.")

    try:
        data = db.reference(f"verify_code/{code}").get()
        if data is None:
            logger.error(f"Verify code {code} does not exist.")
            return False
        elif data["exp_time"] < datetime.datetime.now().timestamp():
            logger.warning(f"Verify code {code} hase been expired.")
            db.reference(f"verify_code/{code}").delete()
            return False
        else:
            logger.info("Verify success.")
            return True
    except (google_exceptions.DeadlineExceeded, google_exceptions.ServiceUnavailable) as e:
        logger.debug(f"Firebase Timeout: {str(e)}")
        raise DatabaseTimeout("Database timeout, please try later.")
    except google_exceptions.ResourceExhausted:
        logger.warning("Firebase Resources exhausted.")
        raise QuotaExceeded("Database quota reaches the limitation.")
    except Exception as e:
        logger.opt(exception=True).debug(f"Unknown error occur in Firebase: {str(e)}")
        raise DatabaseError(f"Database process failed: {str(e)}")
