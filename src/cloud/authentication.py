import datetime
import secrets

from fastapi import APIRouter

from src.shared.database_manager import delete_verify_code, get_verify_code, push_verify_code
from src.shared.logger import logger

router = APIRouter()


@router.post("/api/pair/generate")
def generate_code():
    code = f"{secrets.randbelow(1000000):06d}"
    exp_time = (datetime.datetime.now() + datetime.timedelta(minutes=15)).timestamp()
    push_verify_code(code, exp_time)

    return {"code": code, "exp_time": exp_time}


def pairing_code(code: str, user_id: str) -> bool:
    data = get_verify_code(int(code))

    if data == {}:
        logger.warning("Verify code not found.")
        return False

    if data["exp_time"] < datetime.datetime.now().timestamp():
        logger.warning(f"Verify code {code} hase been expired.")
        delete_verify_code(int(code))
        return False
    else:
        logger.info("Verify success.")
        return True
