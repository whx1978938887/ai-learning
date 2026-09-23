import requests
import json
import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

API_KEY = os.getenv("ZHIPU_API_KEY")
API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"


def stream_chat(prompt: str, max_tokens: int = 2048):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    payload = {
        "model": "glm-5.3-flash",
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "max_tokens": max_tokens,
    }

    response = requests.post(
        API_URL, headers=headers, json=payload, stream=True, timeout=60
    )
    response.raise_for_status()

    full_content = ""
    buffer = ""
    for raw_bytes in response.iter_content(chunk_size=1024, decode_unicode=False):
        buffer += raw_bytes.decode("utf-8")
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            if line.startswith("data: ") and line.strip() != "data: [DONE]":
                try:
                    chunk = json.loads(line[6:])
                    delta = chunk["choices"][0]["delta"].get("content", "")
                    if delta:
                        full_content += delta
                        print(delta, end="", flush=True)  # 打字机效果
                except json.JSONDecodeError:
                    pass  # 跳过不完整JSON片段
    print("\n\n【完整输出】", full_content)
    return full_content


if __name__ == "__main__":
    prompt = "你好，请用一句话介绍一下你自己"
    stream_chat(prompt)
