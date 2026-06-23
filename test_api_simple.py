import os
from openai import OpenAI

# 直接填入你的密钥（临时测试）
API_KEY = "sk-95024d8ac044415da8d92479755a8fb7"

client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.deepseek.com"
)

try:
    response = client.chat.completions.create(
        model="deepseek-v4-flash",  # 先用 Flash 测试
        messages=[{"role": "user", "content": "你好，请用一句话介绍你自己"}],
        max_tokens=50,
        timeout=10
    )
    print("✅ API 调用成功！")
    print("回复：", response.choices[0].message.content)
except Exception as e:
    print("❌ API 调用失败：", e)