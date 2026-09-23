import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("ZHIPU_API_KEY"), base_url="https://open.bigmodel.cn/api/paas/v4/"
)

response = client.chat.completions.create(
    model="glm-5.3-flash",
    messages=[{"role": "user", "content": "写一首关于春天的七言绝句"}],
    stream=True,  # 开启流式输出
)

print("=== 流式输出 ===")
for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
print()
