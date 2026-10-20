import json
import sys
import traceback

from loguru import logger

from src.shared.config import CURRENT_ENV

logger.remove()


def gcp_json_sink(message):
    record = message.record
    level_name = record["level"].name

    # 確保符合 GCP 標準 Severity（避免 SUCCESS 被當成未分類）
    severity = "INFO" if level_name in ("SUCCESS", "INFO") else level_name

    log_entry = {
        "severity": severity,
        "message": f"[{record['file'].name}:{record['line']}] {record['message']}",
        "timestamp": record["time"].isoformat(),
        "logging.googleapis.com/sourceLocation": {
            "file": record["file"].path,
            "line": record["line"],
            "function": record["function"],
        },
    }

    # 轉成 GCP Error Reporting 認得的標準 Traceback 格式
    if record["exception"]:
        exc_type, exc_val, exc_tb = record["exception"]
        formatted_tb = "".join(traceback.format_exception(exc_type, exc_val, exc_tb))
        log_entry["message"] += f"\n{formatted_tb}"

    sys.stderr.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


if CURRENT_ENV == "production":
    logger.add(gcp_json_sink, level="INFO")
else:
    logger.add(
        sys.stdout,
        level="DEBUG",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",  # noqa
    )

    logger.add(
        "logs/ai-todo-list.log",
        level="INFO",
        rotation="10 MB",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        encoding="utf-8",
    )

__all__ = ["logger"]
