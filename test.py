import google.generativeai as genai
import os
from dotenv import load_dotenv

# 讀取你的 .env 檔案取得 API Key
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("--- 正在獲取可用模型清單 ---")

try:
    # 列出所有模型
    for m in genai.list_models():
        # 篩選出支援 'generateContent' 的模型（這是我們最常用的功能）
        if 'generateContent' in m.supported_generation_methods:
            print(f"模型名稱: {m.name}")
            print(f"顯示名稱: {m.display_name}")
            print(f"描述: {m.description}")
            print(f"支援功能: {m.supported_generation_methods}")
            print("-" * 30)
except Exception as e:
    print(f"發生錯誤: {e}")