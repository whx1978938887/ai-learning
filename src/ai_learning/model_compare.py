"""Compare compatible chat models on quality, latency, and estimated cost.

Run without --live to inspect the benchmark cases and pricing configuration.
Set MODEL_COMPARE_MODELS to a JSON list before using --live, for example:
[
  {"name": "glm", "base_url": "https://open.bigmodel.cn/api/paas/v4/", "api_key_env": "ZHIPU_API_KEY", "model": "glm-5.3-flash", "input_price": 0, "output_price": 0},
  {"name": "qwen", "base_url": "https://api.siliconflow.cn/v1", "api_key_env": "SILICONFLOW_API_KEY", "model": "Qwen/Qwen2.5-7B-Instruct", "input_price": 0, "output_price": 0}
]
"""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from typing import Any

import requests


CASES = [
    {
        "id": "reasoning",
        "prompt": "一个水箱每分钟注入 8 升水，同时每分钟漏出 3 升水。原有 25 升水，10 分钟后有多少升？请列出计算式。",
        "rubric": "结果正确（5分），计算式清楚（3分），解释简洁（2分）",
    },
    {
        "id": "factual",
        "prompt": "请用不超过 80 字解释 HTTP 状态码 429 的含义，并给出一个客户端处理建议。",
        "rubric": "含义准确（5分），建议可执行（3分），不超过字数且表达清楚（2分）",
    },
    {
        "id": "structured",
        "prompt": '把“用户登录失败，请检查密码并在 5 分钟后重试”转换成严格 JSON，只允许字段 "message" 和 "retry_after_minutes"。',
        "rubric": "JSON 可解析（4分），字段完全符合要求（3分），值正确（3分）",
    },
]


@dataclass(frozen=True)
class ModelConfig:
    name: str
    base_url: str
    api_key_env: str
    model: str
    input_price: float = 0.0
    output_price: float = 0.0


def load_models() -> list[ModelConfig]:
    raw = os.getenv("MODEL_COMPARE_MODELS", "[]")
    try:
        configs = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("MODEL_COMPARE_MODELS 必须是合法 JSON") from exc
    return [ModelConfig(**config) for config in configs]


def estimate_cost(usage: dict[str, Any], config: ModelConfig) -> float:
    input_tokens = usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0
    output_tokens = usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0
    return (input_tokens * config.input_price + output_tokens * config.output_price) / 1_000_000


def call_model(config: ModelConfig, prompt: str) -> dict[str, Any]:
    api_key = os.getenv(config.api_key_env)
    if not api_key:
        raise RuntimeError(f"缺少环境变量 {config.api_key_env}")

    payload = {
        "model": config.model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "top_p": 1,
        "max_tokens": 256,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    started = time.perf_counter()
    response = requests.post(
        config.base_url.rstrip("/") + "/chat/completions",
        headers=headers,
        json=payload,
        stream=True,
        timeout=60,
    )
    response.raise_for_status()

    content: list[str] = []
    usage: dict[str, Any] = {}
    first_token_at: float | None = None
    for line in response.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: ") or line == "data: [DONE]":
            continue
        chunk = json.loads(line[6:])
        if chunk.get("usage"):
            usage = chunk["usage"]
        delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
        if delta:
            first_token_at = first_token_at or time.perf_counter()
            content.append(delta)

    finished = time.perf_counter()
    output = "".join(content)
    output_tokens = usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0
    return {
        "model": config.name,
        "output": output,
        "ttft_seconds": round((first_token_at or finished) - started, 3),
        "total_seconds": round(finished - started, 3),
        "output_tokens_per_second": round(output_tokens / (finished - (first_token_at or started)), 2) if output_tokens else None,
        "usage": usage,
        "estimated_cost_usd": round(estimate_cost(usage, config), 8),
    }


def print_plan() -> None:
    print("模型对比实验（默认不发起网络请求）")
    print("固定参数：temperature=0, top_p=1, max_tokens=256, stream=true")
    for case in CASES:
        print(f"\n[{case['id']}] {case['prompt']}\n质量评分标准：{case['rubric']}")
    print("\n质量建议：每个模型每题运行 3 次，盲评后取平均分；速度和成本不要混成质量分。")


def main() -> None:
    parser = argparse.ArgumentParser(description="比较兼容 OpenAI Chat Completions 的模型")
    parser.add_argument("--live", action="store_true", help="实际调用 MODEL_COMPARE_MODELS 中的模型")
    args = parser.parse_args()
    if not args.live:
        print_plan()
        return

    models = load_models()
    if not models:
        raise SystemExit("请先设置 MODEL_COMPARE_MODELS，格式见脚本顶部示例")
    for case in CASES:
        for config in models:
            result = call_model(config, case["prompt"])
            print(json.dumps({"case": case["id"], **result}, ensure_ascii=False))


if __name__ == "__main__":
    main()