import datetime
import secrets

from fastapi import APIRouter

from src.shared.database_manager import get_verify_code, push_verify_code

router = APIRouter()


@router.post("/api/pair/generate")
def generate_code():
    code = f"{secrets.randbelow(1000000):06d}"
    exp_time = (datetime.datetime.now() + datetime.timedelta(minutes=15)).timestamp()
    push_verify_code(code, exp_time)

    return {"code": code, "exp_time": exp_time}


@router.get("/api/pair/pairing")
def pairing_code(code: str):
    if get_verify_code(int(code)):
        return {"user"}
