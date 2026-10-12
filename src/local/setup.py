# setup_gui.py
import os
import sys
import json
import time
import requests
from dotenv import load_dotenv

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QWidget,
    QFrame,
    QMessageBox,
)

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest

load_dotenv()

# 檔案路徑與環境變數設定
CONFIG_FILE = "config.json"
TOKEN_FILE = "local_token.json"
CREDENTIALS_FILE = "credentials.json"  # 從 GCP 下載的 Desktop 憑證檔
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:5000").rstrip("/")

# 必須與雲端 cloud_auth.py 的 SCOPES 完全一致
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.student-submissions.me.readonly",
]


# =========================================================
# 背景執行緒 1：負責向雲端領取 6 位數綁定碼，並每 2 秒輪詢狀態
# =========================================================
class PairingWorker(QThread):
    code_received = pyqtSignal(str)          # 成功拿到 6 位數驗證碼
    paired_success = pyqtSignal(dict)        # 使用者在 Line 輸入完成，拿到 user_id
    error_occurred = pyqtSignal(str)         # 發生網路或伺服器錯誤

    def __init__(self, server_url: str):
        super().__init__()
        self.server_url = server_url
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        try:
            # 1. 向雲端請求產生 6 位數綁定碼
            resp = requests.post(f"{self.server_url}/api/pair/init", timeout=10)
            if not resp.ok:
                self.error_occurred.emit(
                    f"無法連線至雲端伺服器取得綁定碼 (HTTP {resp.status_code})：\n"
                    f"網址：{resp.url}\n"
                    f"回應內容：{resp.text[:300]}"
                )
                return
            code = resp.json()["code"]
            self.code_received.emit(code)
        except Exception as e:
            self.error_occurred.emit(f"無法連線至雲端伺服器取得綁定碼：\n{e}")
            return

        # 2. 每 2 秒輪詢檢查使用者是否在 Line 輸入了綁定碼
        while self._is_running:
            time.sleep(2)
            if not self._is_running:
                break
            try:
                status_resp = requests.get(
                    f"{self.server_url}/api/pair/status",
                    params={"code": code},
                    timeout=10,
                )
                if status_resp.status_code == 200:
                    data = status_resp.json()
                    if data.get("status") == "success":
                        self.paired_success.emit({
                            "user_id": data["user_id"],
                            "client_token": data["client_token"],
                        })
                        return
                elif status_resp.status_code == 404:
                    self.error_occurred.emit("綁定碼已過期，請點擊重新取得。")
                    return
            except Exception as e:
                print(f"輪詢等待中... ({e})")


# =========================================================
# 背景執行緒 2：負責啟動本機瀏覽器跑 Google OAuth 並加密上傳雲端
# =========================================================
class GoogleOAuthWorker(QThread):
    auth_success = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, server_url: str, config_data: dict):
        super().__init__()
        self.server_url = server_url
        self.config_data = config_data

    def run(self):
        try:
            if not os.path.exists(CREDENTIALS_FILE):
                self.error_occurred.emit(
                    f"找不到 '{CREDENTIALS_FILE}'！\n請確認已將 GCP OAuth 憑證檔放在專案目錄下。"
                )
                return

            # 1. 在背景執行緒彈出瀏覽器進行 Google OAuth 授權
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(
                port=0,
                prompt="consent",
                access_type="offline",
            )

            # 2. 儲存一份 Token 在本機（供本機抓 Classroom 用）
            with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                f.write(creds.to_json())

            # 3. 將 Token 自動上傳至雲端，由雲端進行 AES 加密存入 Firebase
            upload_resp = requests.post(
                f"{self.server_url}/api/auth/save-token",
                json={
                    "user_id": self.config_data["user_id"],
                    "client_token": self.config_data["client_token"],
                    "token_json": creds.to_json(),
                },
                timeout=15,
            )
            if not upload_resp.ok:
                self.error_occurred.emit(
                    f"上傳 Token 至雲端失敗 (HTTP {upload_resp.status_code})：\n{upload_resp.text[:300]}"
                )
                return

            # 4. 全部成功後才正式寫入 config.json
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=2)

            self.auth_success.emit()

        except Exception as e:
            self.error_occurred.emit(f"Google 授權或上傳雲端時發生錯誤：\n{e}")


# =========================================================
# PyQt6 主設定精靈視窗 (三步驟切換)
# =========================================================
class SetupWizardDialog(QDialog):
    def __init__(self, server_url: str = SERVER_URL):
        super().__init__()
        self.server_url = server_url
        self.config_data: dict = {}
        self.pairing_worker: PairingWorker | None = None
        self.oauth_worker: GoogleOAuthWorker | None = None

        self.setWindowTitle("AI 任務助理 — 初次設定精靈")
        self.setFixedSize(520, 400)
        self._apply_styles()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 28, 28, 28)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        self.page1_pairing = self._build_page1_pairing()
        self.page2_oauth = self._build_page2_oauth()
        self.page3_done = self._build_page3_done()

        self.stack.addWidget(self.page1_pairing)
        self.stack.addWidget(self.page2_oauth)
        self.stack.addWidget(self.page3_done)

        self.start_pairing()

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog, QMessageBox {
                background-color: #F8FAFC;
                color: #0F172A;
            }
            QLabel {
                color: #0F172A;
                font-size: 14px;
            }
            QMessageBox QLabel {
                color: #0F172A;
                font-size: 14px;
                min-width: 300px;
            }
            QMessageBox QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 6px 20px;
                font-size: 13px;
                font-weight: bold;
                min-width: 70px;
            }
            QMessageBox QPushButton:hover {
                background-color: #1D4ED8;
            }
            QLabel#StepBadge {
                color: #2563EB;
                font-weight: bold;
                font-size: 13px;
            }
            QLabel#Title {
                color: #0F172A;
                font-size: 22px;
                font-weight: bold;
            }
            QLabel#Subtitle {
                color: #475569;
                font-size: 14px;
                line-height: 1.5;
            }
            QFrame#DigitBox {
                background-color: #FFFFFF;
                border: 2px solid #CBD5E1;
                border-radius: 12px;
            }
            QLabel#DigitLabel {
                color: #1E293B;
                font-size: 32px;
                font-weight: bold;
            }
            QLabel#StatusHint {
                color: #64748B;
                font-size: 13px;
            }
            QPushButton#PrimaryBtn {
                background-color: #2563EB;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton#PrimaryBtn:hover {
                background-color: #1D4ED8;
            }
            QPushButton#PrimaryBtn:disabled {
                background-color: #94A3B8;
                color: #F1F5F9;
            }
            QPushButton#SecondaryBtn {
                background-color: #E2E8F0;
                color: #1E293B;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton#SecondaryBtn:hover {
                background-color: #CBD5E1;
            }
        """)

    # -----------------------------------------------------
    # 頁面 1：顯示 6 位數驗證碼並等待 Line 輸入
    # -----------------------------------------------------
    def _build_page1_pairing(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        badge = QLabel("STEP 1 OF 2  •  帳號綁定")
        badge.setObjectName("StepBadge")

        title = QLabel("綁定您的 Line 帳號")
        title.setObjectName("Title")

        subtitle = QLabel("請打開手機上的 Line 機器人聊天室，\n直接輸入下方顯示的 6 位數綁定碼：")
        subtitle.setObjectName("Subtitle")

        digits_layout = QHBoxLayout()
        digits_layout.setSpacing(10)
        self.digit_labels: list[QLabel] = []

        for _ in range(6):
            box = QFrame()
            box.setObjectName("DigitBox")
            box.setFixedSize(62, 76)
            box_layout = QVBoxLayout(box)
            box_layout.setContentsMargins(0, 0, 0, 0)

            lbl = QLabel("•")
            lbl.setObjectName("DigitLabel")
            lbl.setFont(QFont("Courier New", 28, QFont.Weight.Bold))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            box_layout.addWidget(lbl)

            self.digit_labels.append(lbl)
            digits_layout.addWidget(box)

        bottom_layout = QHBoxLayout()
        self.lbl_pair_status = QLabel("⏳ 正在向雲端伺服器領取綁定碼...")
        self.lbl_pair_status.setObjectName("StatusHint")

        self.btn_retry_pair = QPushButton("重新取得綁定碼")
        self.btn_retry_pair.setObjectName("SecondaryBtn")
        self.btn_retry_pair.setVisible(False)
        self.btn_retry_pair.clicked.connect(self.start_pairing)

        bottom_layout.addWidget(self.lbl_pair_status)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_retry_pair)

        layout.addWidget(badge)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)
        layout.addLayout(digits_layout)
        layout.addStretch()
        layout.addLayout(bottom_layout)
        return page

    # -----------------------------------------------------
    # 頁面 2：Google Calendar & Classroom 授權
    # -----------------------------------------------------
    def _build_page2_oauth(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)

        badge = QLabel("STEP 2 OF 2  •  Google 服務授權")
        badge.setObjectName("StepBadge")

        title = QLabel("✅ Line 綁定成功！")
        title.setObjectName("Title")

        self.lbl_user_info = QLabel("已成功連結您的 Line 帳號。")
        self.lbl_user_info.setObjectName("Subtitle")

        desc = QLabel(
            "最後一步：請點擊下方按鈕，系統將開啟瀏覽器進行 Google 授權。\n"
            "授權完成後，憑證將自動以 AES 加密同步至雲端，供日曆與 Classroom 使用。"
        )
        desc.setObjectName("Subtitle")
        desc.setWordWrap(True)

        self.btn_start_oauth = QPushButton("🌐 開啟瀏覽器進行 Google 授權")
        self.btn_start_oauth.setObjectName("PrimaryBtn")
        self.btn_start_oauth.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start_oauth.clicked.connect(self.start_google_oauth)

        self.lbl_oauth_status = QLabel("")
        self.lbl_oauth_status.setObjectName("StatusHint")
        self.lbl_oauth_status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(badge)
        layout.addWidget(title)
        layout.addWidget(self.lbl_user_info)
        layout.addWidget(desc)
        layout.addStretch()
        layout.addWidget(self.lbl_oauth_status)
        layout.addWidget(self.btn_start_oauth)
        return page

    # -----------------------------------------------------
    # 頁面 3：設定全部完成
    # -----------------------------------------------------
    def _build_page3_done(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)

        badge = QLabel("SETUP COMPLETE  •  設定完成")
        badge.setObjectName("StepBadge")

        title = QLabel("🎉 歡迎使用 AI 任務助理！")
        title.setObjectName("Title")

        desc = QLabel(
            "您的電腦端已與 Line 帳號完成綁定，\n"
            "且 Google Calendar 與 Classroom 憑證已安全加密入庫。\n\n"
            "現在您可以開始同步課程作業與管理行程了！"
        )
        desc.setObjectName("Subtitle")

        btn_finish = QPushButton("🚀 開始使用")
        btn_finish.setObjectName("PrimaryBtn")
        btn_finish.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_finish.clicked.connect(self.accept)

        layout.addWidget(badge)
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addStretch()
        layout.addWidget(btn_finish)
        return page

    # =====================================================
    # 事件與邏輯控制
    # =====================================================
    def start_pairing(self):
        if self.pairing_worker and self.pairing_worker.isRunning():
            self.pairing_worker.stop()
            self.pairing_worker.wait()

        for lbl in self.digit_labels:
            lbl.setText("•")
        self.lbl_pair_status.setText("⏳ 正在向雲端伺服器領取綁定碼...")
        self.btn_retry_pair.setVisible(False)

        self.pairing_worker = PairingWorker(self.server_url)
        self.pairing_worker.code_received.connect(self._on_code_received)
        self.pairing_worker.paired_success.connect(self._on_paired_success)
        self.pairing_worker.error_occurred.connect(self._on_pair_error)
        self.pairing_worker.start()

    def _on_code_received(self, code: str):
        for i, ch in enumerate(code[:6]):
            self.digit_labels[i].setText(ch)
        self.lbl_pair_status.setText("⏳ 等待您在手機 Line 聊天室輸入此綁定碼 (輸入後將自動跳轉)...")

    def _on_paired_success(self, data: dict):
        self.config_data = data
        masked_id = data["user_id"][:10] + "..."
        self.lbl_user_info.setText(f"已成功綁定您的 Line 帳號（ID: {masked_id}）")
        self.stack.setCurrentWidget(self.page2_oauth)

    def _on_pair_error(self, err_msg: str):
        self.lbl_pair_status.setText("❌ 連線失敗，請確認伺服器網址與網路狀態。")
        self.btn_retry_pair.setVisible(True)
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("配對連線錯誤")
        msg_box.setText(err_msg)
        msg_box.exec()

    def start_google_oauth(self):
        self.btn_start_oauth.setEnabled(False)
        self.btn_start_oauth.setText("⏳ 請在彈出的瀏覽器視窗中點擊「允許」...")
        self.lbl_oauth_status.setText("授權完成後，此視窗將自動完成設定並同步至雲端...")

        self.oauth_worker = GoogleOAuthWorker(self.server_url, self.config_data)
        self.oauth_worker.auth_success.connect(self._on_oauth_success)
        self.oauth_worker.error_occurred.connect(self._on_oauth_error)
        self.oauth_worker.start()

    def _on_oauth_success(self):
        self.stack.setCurrentWidget(self.page3_done)

    def _on_oauth_error(self, err_msg: str):
        self.btn_start_oauth.setEnabled(True)
        self.btn_start_oauth.setText("🌐 重新開啟瀏覽器進行 Google 授權")
        self.lbl_oauth_status.setText("❌ 授權未完成，請重試。")
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Google 授權失敗")
        msg_box.setText(err_msg)
        msg_box.exec()

    def closeEvent(self, event):
        if self.pairing_worker and self.pairing_worker.isRunning():
            self.pairing_worker.stop()
            self.pairing_worker.wait()
        super().closeEvent(event)


def ensure_setup() -> dict:
    if os.path.exists(CONFIG_FILE) and os.path.exists(TOKEN_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    app = QApplication.instance() or QApplication(sys.argv)
    dialog = SetupWizardDialog()
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.config_data
    else:
        sys.exit("使用者取消了初次設定，程式結束。")


def get_local_google_creds() -> Credentials:
    ensure_setup()
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds.valid and creds.expired and creds.refresh_token:
        creds.refresh(GoogleAuthRequest())
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return creds


if __name__ == "__main__":
    config = ensure_setup()
    print("✅ 設定完成！目前綁定的使用者資訊：", config)