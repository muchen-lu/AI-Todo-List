import os
import re

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
    ref = db.reference("/")
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
        DatabaseTimeout: Raises when connect over 5 seconds.
        QuotaExceeded: Raises when writing quota reached the limitation.
        DatabaseError: Raises when unknown error occured.
    """
    if not (user_id or isinstance(user_id, str)):
        logger.error("Recieved invalid user_id", exc_info=True)
        raise ValueError("Invalid user_id")

    logger.info(f"Pushing '{data.title}' task to {user_id}'s database...")

    try:
        ref.child(user_id).child("tasks").child(data.id).set(data.model_dump())
        logger.info("Push data success.")
    except (google_exceptions.DeadlineExceeded, google_exceptions.ServiceUnavailable) as e:
        logger.debug(f"Firebase Timeout: {str(e)}")
        raise DatabaseTimeout("Database timeout, please try later.")
    except google_exceptions.ResourceExhausted:
        logger.warning("Firebase Resources exhausted.")
        raise QuotaExceeded("Database quota reaches the limitation.")
    except Exception as e:
        logger.debug(f"Unknown error occur in Firebase: {str(e)}")
        raise DatabaseError(f"Database process failed: {str(e)}")


def get_tasks(user_id: str, task_id: list[str] | None = None) -> list[TodoItem | None]:
    """Get all tasks or specific tasks from user's realtime database.

    Args:
        user_id (str): specified user id.
        task_id (list[str] | None, optional): specified task id. Defaults to None means all tasks.

    Raises:
        ValueError: Raises when does not recieve user_id or user_id is not string
        KeyError: Raises when realtime database tasks structure is different from TodoItem.
        DatabaseTimeout: Raises when connect over 5 seconds.
        QuotaExceeded: Raises when reading quota reached the limitation.
        DatabaseError: Raises when unknown error occured.

    Returns:
        list[TodoItem | None]: tasks information.
    """
    if not (user_id or isinstance(user_id, str)):
        logger.error("Recieved invalid user_id", exc_info=True)
        raise ValueError("Invalid user_id")

    logger.info(f"Start getting {str(len(task_id)) if task_id else 'all'} tasks from {user_id}'s database.")

    datas: list[TodoItem | None] = []
    try:
        match task_id:
            case None:
                data = ref.child(user_id).child("tasks").get()
                if not data.exist:
                    logger.info("Firebase get 0 task.")
                else:
                    for database_id, data in data.items():
                        estimate_data = data.pop("estimate_data")
                        subtasks = data.pop("subtasks", [])

                        item = TodoItem(
                            id=database_id,
                            estimate_data=EstimateData(**estimate_data),
                            subtasks=[
                                SubtaskItem(id=list(subtask.keys())[0], **list(subtask.items())[0])
                                for subtask in subtasks["subtasks"]
                            ],
                            **data,
                        )
                        datas.append(item)
            case _:
                for single_task_id in task_id:
                    data = ref.child(user_id).child("tasks").child(single_task_id).get()
                    if not data.exist:
                        logger.warning(f"No task id {single_task_id} found in Firebase.")
                        continue
                    for database_id, data in data.items():
                        estimate_data = data.pop("estimate_data")
                        subtasks = data.pop("subtasks", [])

                        item = TodoItem(
                            id=database_id,
                            estimate_data=EstimateData(**estimate_data),
                            subtasks=[
                                SubtaskItem(id=list(subtask.keys())[0], **list(subtask.items())[0])
                                for subtask in subtasks["subtasks"]
                            ],
                            **data,
                        )
                        datas.append(item)
        logger.info("Getting tasks success.")
        return datas
    except KeyError:
        logger.error("Firebase tasks structure is broken", exc_info=True)
        raise KeyError("Tasks structure is broken.")
    except (google_exceptions.DeadlineExceeded, google_exceptions.ServiceUnavailable) as e:
        logger.debug(f"Firebase Timeout: {str(e)}")
        raise DatabaseTimeout("Database timeout, please try later.")
    except google_exceptions.ResourceExhausted:
        logger.warning("Firebase Resources exhausted.")
        raise QuotaExceeded("Database quota reaches the limitation.")
    except Exception as e:
        logger.debug(f"Unknown error occur in Firebase: {str(e)}")
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
    if not (user_id or isinstance(user_id, str)):
        logger.error("Recieved invalid user_id", exc_info=True)
        raise ValueError("Invalid user_id")

    logger.info(f"Start deleting tasks and subtasks from {user_id}'s database")

    try:
        for item in task_and_subtask_id:
            match list(item.keys())[0]:
                case "task":
                    if not isinstance(item["task"], str):
                        logger.error("Received wrong type id when deleting task.", exc_info=True)
                        raise TypeError("Wrong id type")
                    ref.child(user_id).child("tasks").child(item["task"]).delete()
                    logger.info(f"Deleting task {item['task']} success")
                case "subtask":
                    if not isinstance(item["task"], dict):
                        logger.error("Received wrong type content when deleting subtask.", exc_info=True)
                        raise TypeError("Wrong content type")
                    ref.child(user_id).child("tasks").child(list(item["task"].keys())[0]).child(
                        list(item["task"].items())[0]
                    ).delete()
                    logger.info(f"Deleting subtask {list(item['task'].items())[0]} success")
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
        logger.debug(f"Unknown error occur in Firebase: {str(e)}")
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
    if not (user_id or isinstance(user_id, str)):
        logger.error("Recieved invalid user_id", exc_info=True)
        raise ValueError("Invalid user_id")
    if not re.fullmatch(r"^\d{4}_Q[1-4]$", file):
        logger.error("Recieved wrong file name", exc_info=True)
        raise ValueError("Invalid file name")

    try:
        ref.child(user_id).child("history").child(file).set(data.model_dump())
    except (google_exceptions.DeadlineExceeded, google_exceptions.ServiceUnavailable) as e:
        logger.debug(f"Firebase Timeout: {str(e)}")
        raise DatabaseTimeout("Database timeout, please try later.")
    except google_exceptions.ResourceExhausted:
        logger.warning("Firebase Resources exhausted.")
        raise QuotaExceeded("Database quota reaches the limitation.")
    except Exception as e:
        logger.debug(f"Unknown error occur in Firebase: {str(e)}")
        raise DatabaseError(f"Database process failed: {str(e)}")


def get_history(user_id: str, start_file: str, amount: int) -> list[CompleteItem | None]:
    def _change_file(now_file: str) -> str:
        year = now_file.split("_")[0]
        int_year = int(year) - 1
        quarter = now_file.split("_Q")[-1]
        int_quarter = int(quarter) - 1 if int(quarter) - 1 > 0 else 4
        return f"{int_year}_Q{int_quarter}"

    if not (user_id or isinstance(user_id, str)):
        logger.error("Recieved invalid user_id", exc_info=True)
        raise ValueError("Invalid user_id")

    logger.info(f"Strat reading {amount} histories from {user_id}'s database. (start from {start_file})")

    histories: list[CompleteItem | None] = []
    try:
        while True:
            logger.debug(f"Reading {start_file}")
            history = ref.child(user_id).child("history").child(start_file).get()
            if not history.exist:
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
        logger.debug(f"Unknown error occur in Firebase: {str(e)}")
        raise DatabaseError(f"Database process failed: {str(e)}")
