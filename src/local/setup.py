import sys
from typing import Final

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QClipboard, QGuiApplication, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

# ==============================================================================
# 樣式定義 (全域抑制 QLabel 邊框繼承、僅保留必要卡片與按鈕外框)
# ==============================================================================
STYLE_SHEET: Final[str] = """
/* 主視窗背景：暖米白 */
QMainWindow, QWidget#rootWidget {
    background-color: #F9F8F5;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans TC", "Microsoft JhengHei", sans-serif;
}

/* 預設所有 QLabel 無邊框且背景透明，防止繼承父層容器樣式 */
QLabel {
    border: none;
    background-color: transparent;
}

/* 核心主卡片表面 */
QFrame#mainCard {
    background-color: #FFFFFF;
    border: 1px solid #E6E2D8;
    border-radius: 14px;
}

/* 第二頁與第三頁的米白內容區塊容器 */
QFrame#connectBox, QFrame#codeCard {
    background-color: #F9F8F5;
    border: 1px solid #E6E2D8;
    border-radius: 12px;
}

/* 標題與引導說明文字 */
QLabel#titleLabel {
    color: #2D2A26;
    font-size: 20px;
    font-weight: 700;
}

QLabel#descLabel {
    color: #7D776F;
    font-size: 13px;
    line-height: 1.5;
}

QLabel#fieldLabel {
    color: #2D2A26;
    font-size: 12px;
    font-weight: 600;
}

QLabel#subTextLabel {
    color: #8C867E;
    font-size: 12px;
}

/* 單行輸入框 */
QLineEdit {
    background-color: #F9F8F5;
    border: 1px solid #E2DED4;
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 14px;
    color: #2D2A26;
}
QLineEdit:focus {
    background-color: #FFFFFF;
    border: 1px solid #2D2A26;
}

/* 獨立 6 位驗證碼方塊 (唯此 Label 保留獨立邊框與白色背景) */
QLabel.digitBox {
    background-color: #FFFFFF;
    border: 1.5px solid #D8D3C5;
    border-radius: 8px;
    color: #1C1917;
    font-size: 24px;
    font-weight: 700;
    font-family: "Courier New", Courier, monospace;
}

/* 主要操作按鈕 (沉穩黑) */
QPushButton#primaryBtn {
    background-color: #1C1917;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 600;
}
QPushButton#primaryBtn:hover {
    background-color: #332F2B;
}
QPushButton#primaryBtn:pressed {
    background-color: #000000;
}

/* 次要 / 外框按鈕 (如：複製 ID、複製代碼) */
QPushButton#secondaryBtn {
    background-color: #FFFFFF;
    color: #2D2A26;
    border: 1px solid #DAD5C9;
    border-radius: 8px;
    padding: 7px 14px;
    font-size: 12px;
    font-weight: 500;
}
QPushButton#secondaryBtn:hover {
    background-color: #F4F1EA;
}

/* 返回文字連結按鈕 */
QPushButton#textLinkBtn {
    background-color: transparent;
    color: #7D776F;
    border: none;
    font-size: 13px;
    padding: 6px;
}
QPushButton#textLinkBtn:hover {
    color: #2D2A26;
}

/* 服務整合項目外框 */
QFrame#serviceBox {
    background-color: #FFFFFF;
    border: 1px solid #EAE6DC;
    border-radius: 10px;
    padding: 10px;
}
QFrame#serviceBox:hover {
    border: 1px solid #C8C3B6;
}
"""


class SetupWizardWindow(QMainWindow):
    """帳號初始化導引精靈視窗."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("帳號初始設定")
        self.setFixedSize(600, 650)

        # 狀態控制
        self.current_step: int = 1
        self.total_steps: int = 4
        self.current_code: str = "739104"
        self.is_calendar_connected: bool = False
        self.is_classroom_connected: bool = False
        self.remaining_seconds: int = 900  # 15 分鐘倒數

        # 元件引用初始化
        self.digit_boxes: list[QLabel] = []

        self._init_ui()
        self._init_timer()
        self._update_step_ui()

    # ==========================================================================
    # 畫面骨架構建 (Main Layout & Step Indicator)
    # ==========================================================================
    def _init_ui(self) -> None:
        self.setStyleSheet(STYLE_SHEET)

        root_widget = QWidget(self)
        root_widget.setObjectName("rootWidget")
        self.setCentralWidget(root_widget)
        main_layout = QVBoxLayout(root_widget)
        main_layout.setContentsMargins(40, 26, 40, 22)
        main_layout.setSpacing(16)

        # 1. 頂部標頭與步驟進度提示
        top_header_layout = QHBoxLayout()
        header_title = QLabel("系統初始化導引")
        header_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #2D2A26;")  # noqa: E501
        self.step_indicator_label = QLabel("步驟 1 / 4")
        self.step_indicator_label.setStyleSheet("font-size: 12px; color: #7D776F;")  # noqa: E501

        top_header_layout.addWidget(header_title)
        top_header_layout.addStretch()
        top_header_layout.addWidget(self.step_indicator_label)
        main_layout.addLayout(top_header_layout)

        # 4 段式平滑進度條
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(6)
        self.step_bars: list[QFrame] = []
        for _ in range(self.total_steps):
            bar = QFrame()
            bar.setFixedHeight(3)
            bar.setStyleSheet("border-radius: 1px; background-color: #E6E2D8;")
            self.step_bars.append(bar)
            progress_layout.addWidget(bar)
        main_layout.addLayout(progress_layout)

        # 2. 核心卡片容器
        self.main_card = QFrame()
        self.main_card.setObjectName("mainCard")
        card_layout = QVBoxLayout(self.main_card)
        card_layout.setContentsMargins(32, 28, 32, 28)

        self.stack = QStackedWidget()
        self.page_step_1 = self._build_step_1_page()
        self.page_step_2 = self._build_step_2_page()
        self.page_step_3 = self._build_step_3_page()
        self.page_step_4 = self._build_step_4_page()

        self.stack.addWidget(self.page_step_1)
        self.stack.addWidget(self.page_step_2)
        self.stack.addWidget(self.page_step_3)
        self.stack.addWidget(self.page_step_4)

        card_layout.addWidget(self.stack)
        main_layout.addWidget(self.main_card)

        # 3. 底部隱私微註
        footer_label = QLabel("資料存取皆透過安全憑證處理，不另作商業用途")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_label.setStyleSheet("color: #A09A90; font-size: 11px;")
        main_layout.addWidget(footer_label)

    # --------------------------------------------------------------------------
    # 步驟一：設定稱呼 (Username)
    # --------------------------------------------------------------------------
    def _build_step_1_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        title = QLabel("設定你的稱呼")
        title.setObjectName("titleLabel")
        desc = QLabel("這會用於每日排程提醒與訊息開頭。之後隨時可以在帳號設定中修改。")
        desc.setObjectName("descLabel")
        desc.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addSpacing(6)

        field_title = QLabel("顯示名稱")
        field_title.setObjectName("fieldLabel")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("例如：Alex、小名")
        self.username_input.setMaxLength(20)
        self.username_input.textChanged.connect(self._clear_step_1_error)

        hint = QLabel("建議使用 2 至 10 個字元以內的簡潔暱稱。")
        hint.setObjectName("subTextLabel")

        self.step1_error_label = QLabel("")
        self.step1_error_label.setStyleSheet("color: #B91C1C; font-size: 12px; font-weight: 500;")  # noqa: E501
        self.step1_error_label.hide()

        layout.addWidget(field_title)
        layout.addWidget(self.username_input)
        layout.addWidget(self.step1_error_label)
        layout.addWidget(hint)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        next_btn = QPushButton("下一步：加入官方帳號")
        next_btn.setObjectName("primaryBtn")
        next_btn.clicked.connect(self._handle_step_1_submit)
        btn_layout.addWidget(next_btn)

        layout.addLayout(btn_layout)
        return page

    # --------------------------------------------------------------------------
    # 步驟二：加入 LINE 官方帳號好友 (QR Code / Search ID)
    # --------------------------------------------------------------------------
    def _build_step_2_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("加入 LINE 官方帳號")
        title.setObjectName("titleLabel")
        desc = QLabel("在開始綁定前，請先將隨身助理加入 LINE 好友。你可以使用手機掃描條碼，或直接搜尋 ID。")  # noqa: E501
        desc.setObjectName("descLabel")
        desc.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addSpacing(6)

        # 外層整合容器 (透過 ObjectName 套用樣式，不直接用 inline CSS 避免繼承)
        connect_box = QFrame()
        connect_box.setObjectName("connectBox")
        box_layout = QHBoxLayout(connect_box)
        box_layout.setContentsMargins(24, 22, 24, 22)
        box_layout.setSpacing(24)

        # QR Code 容器
        self.qr_placeholder = QLabel("QR Code\n影像預留區")
        self.qr_placeholder.setFixedSize(116, 116)
        self.qr_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_placeholder.setStyleSheet(
            "background-color: #FFFFFF; border: 1px solid #DAD5C9; border-radius: 8px; color: #8C867E; font-size: 11px;"  # noqa: E501
        )
        # 👉 嘗試載入專屬 QR Code 圖檔（找不到時會顯示預設文字）
        self.set_qr_image("assets/line_qr.png")
        box_layout.addWidget(self.qr_placeholder)

        # 右側加入方式與 ID 區域（完全去除多餘內框）
        info_layout = QVBoxLayout()
        info_layout.setSpacing(12)

        id_guide = QLabel("加入方式：\n1. 手機掃描左側條碼加入\n2. 或搜尋下方 ID")
        id_guide.setStyleSheet("font-size: 12px; color: #6E685F; line-height: 1.5;")  # noqa: E501

        # ID 與複製按鈕水平排列 (無外框容器)
        id_row = QHBoxLayout()
        id_row.setSpacing(12)

        self.bot_id_label = QLabel("@line_assistant_bot")
        self.bot_id_label.setStyleSheet("font-size: 14px; font-weight: 700; color: #1C1917; font-family: monospace;")  # noqa: E501

        self.copy_id_btn = QPushButton("複製 ID")
        self.copy_id_btn.setObjectName("secondaryBtn")
        self.copy_id_btn.clicked.connect(self._handle_copy_bot_id)

        id_row.addWidget(self.bot_id_label)
        id_row.addWidget(self.copy_id_btn)
        id_row.addStretch()

        info_layout.addWidget(id_guide)
        info_layout.addLayout(id_row)
        info_layout.addStretch()
        box_layout.addLayout(info_layout)

        layout.addWidget(connect_box)

        tips = QLabel("確認手機 LINE 已經成功將機器人加入好友後，請點擊下方按鈕取得個人綁定碼。")
        tips.setStyleSheet("font-size: 12px; color: #8C867E; margin-top: 4px;")
        tips.setWordWrap(True)
        layout.addWidget(tips)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        back_btn = QPushButton("返回上一步")
        back_btn.setObjectName("textLinkBtn")
        back_btn.clicked.connect(lambda: self._go_to_step(1))

        next_btn = QPushButton("已加入好友，下一步")
        next_btn.setObjectName("primaryBtn")
        next_btn.clicked.connect(self._handle_step_2_submit)

        btn_layout.addWidget(back_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(next_btn)
        layout.addLayout(btn_layout)

        return page

    # --------------------------------------------------------------------------
    # 步驟三：獨立 6 位數字驗證碼 (6 Digit Boxes)
    # --------------------------------------------------------------------------
    def _build_step_3_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("連結你的 LINE 帳號")
        title.setObjectName("titleLabel")
        desc = QLabel("請開啟剛才加入的 LINE 聊天室，發送下方這組 6 位數驗證碼，即可完成裝置綁定。")  # noqa: E501
        desc.setObjectName("descLabel")
        desc.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addSpacing(6)

        # 驗證碼卡片容器
        code_card = QFrame()
        code_card.setObjectName("codeCard")
        code_card_layout = QVBoxLayout(code_card)
        code_card_layout.setContentsMargins(28, 22, 28, 22)
        code_card_layout.setSpacing(16)

        # 「個人綁定碼」純文字標題 (無框)
        card_hint = QLabel("個人綁定碼")
        card_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_hint.setStyleSheet("font-size: 13px; color: #5C574F; font-weight: 600; letter-spacing: 0.5px;")  # noqa: E501
        code_card_layout.addWidget(card_hint)

        # 6 個獨立數位方塊 (保留清楚方塊邊框)
        digits_row = QHBoxLayout()
        digits_row.setSpacing(10)
        digits_row.addStretch()
        self.digit_boxes = []

        for _ in range(6):
            box = QLabel("-")
            box.setProperty("class", "digitBox")
            box.setFixedSize(46, 56)
            box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.digit_boxes.append(box)
            digits_row.addWidget(box)

        digits_row.addStretch()
        code_card_layout.addLayout(digits_row)

        # 倒數計時與操作按鈕列 (有效時間為純文字、無框)
        action_row = QHBoxLayout()
        action_row.setContentsMargins(8, 4, 8, 2)
        action_row.addStretch()

        self.timer_label = QLabel("有效時間剩餘 15:00")
        self.timer_label.setStyleSheet("font-size: 12px; color: #6E685F; padding-right: 6px;")  # noqa: E501

        self.copy_code_btn = QPushButton("複製代碼")
        self.copy_code_btn.setObjectName("secondaryBtn")
        self.copy_code_btn.clicked.connect(self._handle_copy_code)

        action_row.addWidget(self.timer_label)
        action_row.addSpacing(8)
        action_row.addWidget(self.copy_code_btn)
        action_row.addStretch()
        code_card_layout.addLayout(action_row)

        layout.addWidget(code_card)

        instructions = QLabel(
            "1. 打開手機 LINE，進入剛剛加入的助理聊天室。\n"
            "2. 直接送出上方 6 位數字。\n"
            "3. 收到機器人確認回覆後，點選下方按鈕繼續。"
        )
        instructions.setStyleSheet(
            "background-color: #F4F1EA; border-radius: 8px; padding: 12px; font-size: 12px; color: #666159; line-height: 1.5;"  # noqa: E501
        )
        layout.addWidget(instructions)
        layout.addStretch()

        self.step3_error_label = QLabel("")
        self.step3_error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.step3_error_label.setStyleSheet("color: #B91C1C; font-size: 12px; font-weight: 500;")  # noqa: E501
        self.step3_error_label.hide()
        layout.addWidget(self.step3_error_label)

        btn_layout = QHBoxLayout()
        back_btn = QPushButton("返回上一步")
        back_btn.setObjectName("textLinkBtn")
        back_btn.clicked.connect(lambda: self._go_to_step(2))

        verify_btn = QPushButton("我已在 LINE 完成發送")
        verify_btn.setObjectName("primaryBtn")
        verify_btn.clicked.connect(self._handle_step_3_verify)

        btn_layout.addWidget(back_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(verify_btn)
        layout.addLayout(btn_layout)

        self.set_binding_code(self.current_code)
        return page

    # --------------------------------------------------------------------------
    # 步驟四：登入 Calendar & Classroom
    # --------------------------------------------------------------------------
    def _build_step_4_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("同步排程與課程")
        title.setObjectName("titleLabel")
        desc = QLabel("連結你的學校或個人 Google 帳號，作業截止日與行事曆將自動納入每日提醒。")  # noqa: E501
        desc.setObjectName("descLabel")
        desc.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addSpacing(4)

        # Google Calendar
        cal_frame = QFrame()
        cal_frame.setObjectName("serviceBox")
        cal_layout = QHBoxLayout(cal_frame)
        cal_layout.setContentsMargins(12, 10, 12, 10)

        cal_badge = QLabel("CAL")
        cal_badge.setStyleSheet(
            "background-color: #F4F1EA; color: #2D2A26; font-weight: 700; font-size: 10px; border-radius: 6px; padding: 8px 10px;"  # noqa: E501
        )
        cal_info_layout = QVBoxLayout()
        cal_info_layout.setSpacing(2)
        cal_title = QLabel("Google 日曆 (Calendar)")
        cal_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #2D2A26;")  # noqa: E501
        cal_sub = QLabel("同步個人排程與會議提醒")
        cal_sub.setStyleSheet("font-size: 11px; color: #7D776F;")
        cal_info_layout.addWidget(cal_title)
        cal_info_layout.addWidget(cal_sub)

        self.btn_cal_connect = QPushButton("連結帳號")
        self.btn_cal_connect.setObjectName("secondaryBtn")
        self.btn_cal_connect.clicked.connect(lambda: self._handle_toggle_service("calendar"))  # noqa: E501

        cal_layout.addWidget(cal_badge)
        cal_layout.addSpacing(10)
        cal_layout.addLayout(cal_info_layout)
        cal_layout.addStretch()
        cal_layout.addWidget(self.btn_cal_connect)
        layout.addWidget(cal_frame)

        # Google Classroom
        cls_frame = QFrame()
        cls_frame.setObjectName("serviceBox")
        cls_layout = QHBoxLayout(cls_frame)
        cls_layout.setContentsMargins(12, 10, 12, 10)

        cls_badge = QLabel("CLS")
        cls_badge.setStyleSheet(
            "background-color: #F4F1EA; color: #2D2A26; font-weight: 700; font-size: 10px; border-radius: 6px; padding: 8px 10px;"  # noqa: E501
        )
        cls_info_layout = QVBoxLayout()
        cls_info_layout.setSpacing(2)
        cls_title = QLabel("Google 課堂 (Classroom)")
        cls_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #2D2A26;")  # noqa: E501
        cls_sub = QLabel("自動讀取作業繳交期限與課程公告")
        cls_sub.setStyleSheet("font-size: 11px; color: #7D776F;")
        cls_info_layout.addWidget(cls_title)
        cls_info_layout.addWidget(cls_sub)

        self.btn_cls_connect = QPushButton("連結帳號")
        self.btn_cls_connect.setObjectName("secondaryBtn")
        self.btn_cls_connect.clicked.connect(lambda: self._handle_toggle_service("classroom"))  # noqa: E501

        cls_layout.addWidget(cls_badge)
        cls_layout.addSpacing(10)
        cls_layout.addLayout(cls_info_layout)
        cls_layout.addStretch()
        cls_layout.addWidget(self.btn_cls_connect)
        layout.addWidget(cls_frame)

        notice = QLabel("僅以唯讀權限讀取公開事項，不會更動或刪除你的原始資料。")
        notice.setStyleSheet("font-size: 11px; color: #8C867E;")
        layout.addWidget(notice)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        back_btn = QPushButton("返回上一步")
        back_btn.setObjectName("textLinkBtn")
        back_btn.clicked.connect(lambda: self._go_to_step(3))

        self.finish_btn = QPushButton("完成設定並開始使用")
        self.finish_btn.setObjectName("primaryBtn")
        self.finish_btn.clicked.connect(self._handle_finish_setup)

        btn_layout.addWidget(back_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.finish_btn)
        layout.addLayout(btn_layout)

        return page

    # ==========================================================================
    # 步驟切換與動態填入邏輯
    # ==========================================================================
    def _go_to_step(self, step: int) -> None:
        self.current_step = step
        self.stack.setCurrentIndex(step - 1)
        self._update_step_ui()

    def _update_step_ui(self) -> None:
        self.step_indicator_label.setText(f"步驟 {self.current_step} / {self.total_steps}")  # noqa: E501
        active_color = "#1C1917"
        inactive_color = "#E6E2D8"

        for idx, bar in enumerate(self.step_bars, start=1):
            color = active_color if self.current_step >= idx else inactive_color
            bar.setStyleSheet(f"border-radius: 1px; background-color: {color};")

    def set_binding_code(self, code: str) -> None:
        """動態將 6 位數純文字填入獨立的 6 個方塊."""
        clean_code = code.replace("-", "").strip()[:6].ljust(6, " ")
        self.current_code = clean_code
        for i, ch in enumerate(clean_code):
            if i < len(self.digit_boxes):
                self.digit_boxes[i].setText(ch)

    def set_qr_image(self, image_path: str) -> None:
        """設定 QR Code 圖片，支援平滑縮放與防呆後備文字."""
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                100,
                100,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.qr_placeholder.setPixmap(scaled_pixmap)
        else:
            self.qr_placeholder.setText("QR Code\n影像預留區")

    def _init_timer(self) -> None:
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._on_timer_tick)
        self.timer.start()

    def _on_timer_tick(self) -> None:
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            mins, secs = divmod(self.remaining_seconds, 60)
            self.timer_label.setText(f"有效時間剩餘 {mins:02d}:{secs:02d}")
        else:
            self.timer_label.setText("代碼已過期，請重新整理")
            self.timer_label.setStyleSheet("font-size: 12px; color: #B91C1C;")

    def _clear_step_1_error(self) -> None:
        if self.step1_error_label.isVisible():
            self.step1_error_label.hide()

    def _handle_copy_bot_id(self) -> None:
        clipboard: QClipboard | None = QGuiApplication.clipboard()
        if clipboard:
            clipboard.setText(self.bot_id_label.text())
            self.copy_id_btn.setText("已複製 ✓")
            QTimer.singleShot(2000, lambda: self.copy_id_btn.setText("複製 ID"))

    def _handle_copy_code(self) -> None:
        clipboard: QClipboard | None = QGuiApplication.clipboard()
        if clipboard:
            clipboard.setText(self.current_code)
            self.copy_code_btn.setText("已複製 ✓")
            QTimer.singleShot(2000, lambda: self.copy_code_btn.setText("複製代碼"))  # noqa: E501

    # ==========================================================================
    # 後端掛鉤插槽 (Backend Integration Slots)
    # ==========================================================================
    def _handle_step_1_submit(self) -> None:
        username = self.username_input.text().strip()
        if not username:
            self.step1_error_label.setText("請先輸入你想使用的暱稱。")
            self.step1_error_label.show()
            return

        # ----------------------------------------------------------------------
        # TODO: 【後端串接點 1】向你的 FastAPI 儲存暱稱
        # backend_api.save_username(username)
        # ----------------------------------------------------------------------
        self._go_to_step(2)

    def _handle_step_2_submit(self) -> None:
        self._go_to_step(3)
        self._request_new_binding_code()

    def _request_new_binding_code(self) -> None:
        # ----------------------------------------------------------------------
        # TODO: 【後端串接點 2】向 FastAPI 請求產生 6 位數純數字綁定碼
        # new_code = backend_api.generate_code()
        # self.set_binding_code(new_code)
        # ----------------------------------------------------------------------
        self.set_binding_code("739104")

    def _handle_step_3_verify(self) -> None:
        # ----------------------------------------------------------------------
        # TODO: 【後端串接點 3】檢查該 6 位代碼是否已被 LINE Webhook 認領
        # is_bound = backend_api.check_binding_status()
        # if not is_bound:
        #     self.step3_error_label.setText("尚未偵測到 LINE 訊息，請確認已在聊天室送出代碼。")  # noqa: E501
        #     self.step3_error_label.show()
        #     return
        # ----------------------------------------------------------------------
        self.step3_error_label.hide()
        self._go_to_step(4)

    def _handle_toggle_service(self, service_type: str) -> None:
        if service_type == "calendar":
            # ------------------------------------------------------------------
            # TODO: 【後端串接點 4A】呼叫 Google Calendar OAuth
            # ------------------------------------------------------------------
            self.is_calendar_connected = not self.is_calendar_connected
            self._update_service_btn(self.btn_cal_connect, self.is_calendar_connected)  # noqa: E501
        elif service_type == "classroom":
            # ------------------------------------------------------------------
            # TODO: 【後端串接點 4B】呼叫 Google Classroom OAuth
            # ------------------------------------------------------------------
            self.is_classroom_connected = not self.is_classroom_connected
            self._update_service_btn(self.btn_cls_connect, self.is_classroom_connected)  # noqa: E501

    def _update_service_btn(self, btn: QPushButton, is_connected: bool) -> None:
        if is_connected:
            btn.setText("已連結 ✓")
            btn.setStyleSheet(
                "background-color: #EAE6DC; color: #5C574F; border: none; font-size: 12px; border-radius: 8px; padding: 7px 14px;"  # noqa: E501
            )
        else:
            btn.setText("連結帳號")
            btn.setStyleSheet("")

    def _handle_finish_setup(self) -> None:
        # ----------------------------------------------------------------------
        # TODO: 【後端串接點 5】將完成狀態註記回系統
        # backend_api.mark_setup_complete()
        # ----------------------------------------------------------------------
        self.finish_btn.setText("設定就緒 ✓")
        self.finish_btn.setEnabled(False)
        QTimer.singleShot(800, self.close)


def main() -> None:
    app = QApplication(sys.argv)
    window = SetupWizardWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
