import os
from openai import OpenAI
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

def test_zhipu():
    """测试智谱GLM API"""
    client = OpenAI(
        api_key=os.getenv("ZHIPU_API_KEY"),
        base_url="https://open.bigmodel.cn/api/paas/v4/"
    )
    
    response = client.chat.completions.create(
        model="glm-5.3-flash",  # 免费模型
        messages=[
            {"role": "user", "content": "你好，请用一句话介绍你自己"}
        ],
        temperature=0.7,
        max_tokens=128
    )
    
    print("=== 智谱GLM 回复 ===")
    print(response.choices[0].message.content)
    print(f"Token消耗: {response.usage.total_tokens}\n")


def test_siliconflow():
    """测试硅基流动API"""
    client = OpenAI(
        api_key=os.getenv("SILICONFLOW_API_KEY"),
        base_url="https://api.siliconflow.cn/v1"
    )
    
    response = client.chat.completions.create(
        model="Qwen/Qwen2.5-7B-Instruct",  # 或 Qwen/Qwen2.5-7B-Instruct（免费）
        messages=[
            {"role": "user", "content": "你好，请用一句话介绍你自己"}
        ],
        temperature=0.7,
        max_tokens=128
    )
    
    print("=== 硅基流动 回复 ===")
    print(response.choices[0].message.content)
    print(f"Token消耗: {response.usage.total_tokens}\n")


if __name__ == "__main__":
    test_zhipu()
    test_siliconflow()