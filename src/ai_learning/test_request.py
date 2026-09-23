import requests
import json
import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# 1.配置接口地址和密钥
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY")
ZHIPU_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

# 2.准备请求头
headers = {
    "Authorization": f"Bearer {ZHIPU_API_KEY}",
    "Content-Type": "application/json",
}

# 3.准备问题（消息体）
data = {
    "model": "glm-5.3-flash",  # 免费模型
    "messages": [
        {"role": "system", "content": "你是一个乐于助人的AI助手。"},
        {"role": "user", "content": "你好，请用一句话介绍一下你自己"},
    ],
    "temperature": 0.7,
}

# 4. 发送请求并获取结果
try:
    response = requests.post(ZHIPU_API_URL, headers=headers, data=json.dumps(data))
    response.raise_for_status()  # 如果请求出错，这里会报提醒

    # 5.解析并打印AI的回答
    result = response.json()
    ai_reply = result["choices"][0]["message"]["content"]
    print("AI回答：", ai_reply)

except Exception as e:
    print("出错了：", e)
