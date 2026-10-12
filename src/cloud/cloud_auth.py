# cloud_auth.py
import os
import json
import random
import secrets
from pydantic import BaseModel
from cryptography.fernet import Fernet
from fastapi import APIRouter, HTTPException
from firebase_admin import db
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest

router = APIRouter()

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.me.readonly",
]

def _get_cipher() -> Fernet:
    key = os.environ.get("ENCRYPTION_KEY")
    if not key:
        raise RuntimeError("缺少 ENCRYPTION_KEY 環境變數！")
    return Fernet(key.encode())

# ==========================================
# 1. 本機 setup 領取與檢查 6 位數綁定碼
# ==========================================
@router.post("/api/pair/init")
def init_pairing():
    code = f"{random.randint(100000, 999999)}"
    db.reference(f"pairing_codes/{code}").set({"status": "waiting"})
    return {"code": code}

@router.get("/api/pair/status")
def check_pairing_status(code: str):
    code_ref = db.reference(f"pairing_codes/{code}")
    data = code_ref.get()
    if not data:
        raise HTTPException(status_code=404, detail="綁定碼不存在或已過期")
    if data.get("status") == "waiting":
        return {"status": "waiting"}

    # 本機讀取成功後，立即刪除暫存綁定碼
    code_ref.delete()
    return {
        "status": "success",
        "user_id": data["user_id"],
        "client_token": data["client_token"]
    }

# ==========================================
# 2. 給 Line Webhook 呼叫：攔截使用者輸入的 6 位數綁定碼
# ==========================================
def try_handle_pairing_code(user_id: str, text: str) -> str | None:
    """
    若使用者在 Line 輸入的是 6 位數綁定碼，記錄 user_id 並回傳提示文字；
    若只是一般聊天指令，則回傳 None。
    """
    clean_text = text.strip()
    if clean_text.isdigit() and len(clean_text) == 6:
        code_ref = db.reference(f"pairing_codes/{clean_text}")
        data = code_ref.get()
        if data and data.get("status") == "waiting":
            client_token = secrets.token_urlsafe(32)
            
            # 更新狀態，讓正在每 2 秒輪詢的電腦拿到 user_id
            code_ref.update({
                "status": "success",
                "user_id": user_id,
                "client_token": client_token
            })
            # 在該使用者的節點下存好這台電腦的通行金鑰
            db.reference(f"users/{user_id}/profile").update({
                "client_token": client_token
            })
            return "🎉 電腦綁定成功！請看回電腦螢幕，在自動彈出的瀏覽器視窗中點擊「允許」完成 Google 授權。"
    return None

# ==========================================
# 3. 接收本機 setup.py 傳上來的 Google Token 並加密入庫
# ==========================================
class TokenUploadRequest(BaseModel):
    user_id: str
    client_token: str
    token_json: str

@router.post("/api/auth/save-token")
def save_token_from_pc(req: TokenUploadRequest):
    profile = db.reference(f"users/{req.user_id}/profile").get() or {}
    if profile.get("client_token") != req.client_token:
        raise HTTPException(status_code=403, detail="無效的電腦端金鑰")

    raw_info = json.loads(req.token_json)
    clean_payload = json.dumps({
        "token": raw_info.get("token"),
        "refresh_token": raw_info.get("refresh_token"),
        "scopes": raw_info.get("scopes", SCOPES),
    })
    encrypted_str = _get_cipher().encrypt(clean_payload.encode()).decode()

    db.reference(f"users/{req.user_id}/google_oauth").set({
        "encrypted_data": encrypted_str
    })
    return {"status": "ok"}

# ==========================================
# 4. 雲端操作 Google Calendar 時呼叫的憑證讀取器
# ==========================================
def get_cloud_google_creds(user_id: str) -> Credentials:
    """從 Firebase 解密讀取該使用者的 Token，若過期則自動刷新"""
    token_ref = db.reference(f"users/{user_id}/google_oauth")
    record = token_ref.get()
    if not record or "encrypted_data" not in record:
        raise RuntimeError(f"使用者 {user_id} 尚未完成 Google 授權！請先在本機執行 setup.py。")

    cipher = _get_cipher()
    token_data = json.loads(cipher.decrypt(record["encrypted_data"].encode()).decode())

    creds = Credentials(
        token=token_data["token"],
        refresh_token=token_data["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        scopes=token_data.get("scopes", SCOPES),
    )

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(GoogleAuthRequest())
            token_data["token"] = creds.token
            new_encrypted = cipher.encrypt(json.dumps(token_data).encode()).decode()
            token_ref.set({"encrypted_data": new_encrypted})
        else:
            raise RuntimeError("Google 憑證已失效，請在本機重新執行 setup.py。")

    return creds