from ai_client import suggest_tasks
from models import ONOItem

calendar = [
    {
      "title": "跨部門每週進度同步會議",
      "start": "09:00",
      "end": "10:15"
    },
    {
      "title": "午餐與休息散步",
      "start": "12:00",
      "end": "13:30"
    },
    {
      "title": "客戶線上需求對齊會議",
      "start": "15:00",
      "end": "16:00"
    },
    {
      "title": "晚餐與家庭時間",
      "start": "18:30",
      "end": "19:30"
    }
  ]
tasks = [
  {
    "title": "送審 Q3 專案進度摘要報告",
    "deadline": "2026-09-11 18:00",
    "task_category": "writing",
    "congnitive_load": 3,
    "estimated_time": 60,
    "suggest_work_mode": "deep"
  },
  {
    "title": "回覆外部合作廠商技術規格確認信件",
    "deadline": "2026-09-12 12:00",
    "task_category": "communication",
    "congnitive_load": 2,
    "estimated_time": 25,
    "suggest_work_mode": "shallow"
  },
  {
    "title": "重構用戶認證模組 API 與單元測試撰寫",
    "deadline": "2026-09-14 18:00",
    "task_category": "development",
    "congnitive_load": 5,
    "estimated_time": 150,
    "suggest_work_mode": "deep"
  },
  {
    "title": "更新後台資料庫讀取權限與存取稽核名單",
    "deadline": "2026-09-15 17:00",
    "task_category": "admin",
    "congnitive_load": 2,
    "estimated_time": 30,
    "suggest_work_mode": "shallow"
  },
  {
    "title": "撰寫並發布下週系統維護升級公告",
    "deadline": "2026-09-16 11:30",
    "task_category": "writing",
    "congnitive_load": 2,
    "estimated_time": 30,
    "suggest_work_mode": "shallow"
  },
  {
    "title": "彙整跨部門產品需求規格書（PRD）初稿",
    "deadline": "2026-09-16 18:00",
    "task_category": "planning",
    "congnitive_load": 4,
    "estimated_time": 120,
    "suggest_work_mode": "deep"
  },
  {
    "title": "製作經營層雙週策略會議簡報投影片",
    "deadline": "2026-09-18 17:00",
    "task_category": "design",
    "congnitive_load": 4,
    "estimated_time": 90,
    "suggest_work_mode": "deep"
  },
  {
    "title": "排查系統日誌異常並整理監控告警白名單",
    "deadline": "2026-09-19 15:00",
    "task_category": "review",
    "congnitive_load": 3,
    "estimated_time": 45,
    "suggest_work_mode": "deep"
  },
  {
    "title": "規劃團隊 Q4 內部技術培訓大綱與預算",
    "deadline": "2026-09-22 18:00",
    "task_category": "planning",
    "congnitive_load": 3,
    "estimated_time": 60,
    "suggest_work_mode": "deep"
  },
  {
    "title": "競品新功能架構分析與市場定位調研報告",
    "deadline": "2026-09-25 18:00",
    "task_category": "research",
    "congnitive_load": 5,
    "estimated_time": 180,
    "suggest_work_mode": "deep"
  },
  {
    "title": "研讀分散式系統快取失效策略技術文件",
    "deadline": "2026-09-17 18:00",
    "task_category": "learning",
    "congnitive_load": 4,
    "estimated_time": 90,
    "suggest_work_mode": "deep"
  },
  {
    "title": "統整團隊出差單據並送交財務系統簽核",
    "deadline": "2026-09-18 12:00",
    "task_category": "admin",
    "congnitive_load": 1,
    "estimated_time": 20,
    "suggest_work_mode": "shallow"
  },
  {
    "title": "重新設計行動端結帳流程 UI/UX 互動原型",
    "deadline": "2026-09-21 17:00",
    "task_category": "design",
    "congnitive_load": 4,
    "estimated_time": 120,
    "suggest_work_mode": "deep"
  },
  {
    "title": "召開微服務架構拆分前期技術對齊會議",
    "deadline": "2026-09-23 15:30",
    "task_category": "meeting",
    "congnitive_load": 3,
    "estimated_time": 60,
    "suggest_work_mode": "deep"
  },
  {
    "title": "審查前端核心模組 Pull Request 程式碼品質",
    "deadline": "2026-09-24 16:00",
    "task_category": "review",
    "congnitive_load": 3,
    "estimated_time": 40,
    "suggest_work_mode": "deep"
  },
  {
    "title": "開發推播通知佇列（Queue）非同步處理模組",
    "deadline": "2026-09-28 18:00",
    "task_category": "development",
    "congnitive_load": 5,
    "estimated_time": 180,
    "suggest_work_mode": "deep"
  },
  {
    "title": "電話聯繫金流服務商確認扣款手續費異動細節",
    "deadline": "2026-09-29 11:00",
    "task_category": "communication",
    "congnitive_load": 2,
    "estimated_time": 15,
    "suggest_work_mode": "shallow"
  },
  {
    "title": "分析近一季用戶流失漏斗與留存率異動歸因",
    "deadline": "2026-10-02 18:00",
    "task_category": "research",
    "congnitive_load": 4,
    "estimated_time": 100,
    "suggest_work_mode": "deep"
  },
  {
    "title": "清理雲端測試伺服器閒置資源並釋放硬碟空間",
    "deadline": "2026-10-05 17:00",
    "task_category": "other",
    "congnitive_load": 2,
    "estimated_time": 30,
    "suggest_work_mode": "shallow"
  },
  {
    "title": "撰寫 API 錯誤代碼定義手冊與開發者 FAQ",
    "deadline": "2026-10-08 18:00",
    "task_category": "writing",
    "congnitive_load": 3,
    "estimated_time": 75,
    "suggest_work_mode": "deep"
  }
]
result = suggest_tasks(tasks, calendar)
print(result)