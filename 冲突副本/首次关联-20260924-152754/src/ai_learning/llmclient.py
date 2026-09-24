import requests, json, time, random, os


class LLMClient:
    def _init_(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url

    def chat(
        self,
        prompt: str,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 2048,
        stream: bool = True,
        max_retries: int = 3,
    ):

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream" if stream else "application/json",
        }

        payload = {
            "model": "qwen-plus",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        for attempt in range(max_retries + 1):
            try:
                resp = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    stream=stream,
                    timeout=60,
                )
                resp.raise_for_status()

                if stream:
                    return self._handle_stream(resp)
                else:
                    result = resp.json()
                    finish_reason = result["choices"][0].get("finish_reason", "")
                    if finish_reason == "length":
                        # 被截断，自动续写
                        payload["messages"].append(
                            {
                                "role": "assitant",
                                "content": result["choice"][0]["message"]["content"],
                            }
                        )
                        payload["message"].append({"role": "user", "content": "请继续"})
                        return self.chat(
                            "",
                            **{
                                k: v
                                for k, v in locals().items()
                                if k not in ["self", "attempt", "resp", "result"]
                            },
                        )
                    return result["choice"][0]["message"]["content"]

            except Exception as e:
                status = getattr(e, "status_code", None)
                if status in {401, 403, 400, 422}:
                    raise  # 不可重试错误直接抛出
                if status not in {429, 500, 502, 503, 504} and attempt == max_retries:
                    raise

                delay = min(1.0 * (2**attempt), 60.0) + random.uniform(0, 0.5)
                time.sleep(delay)

        raise Exception("重试耗尽，服务降级")

    def _handle_stream(self, response):
        full_content, buffer = "", ""
        for raw in response.iter_content(chunk_size=None, decode_unicode=False):
            if not raw:
                continue
            buffer += raw.decode("utf-8", errors="replace")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if line.startswith("data: ") and line.strip() != "data: [DONE]":
                    try:
                        chunk = json.loads(line[6:])
                        delta = chunk["choices"][0]["delta"].get("content", "")
                        finish = chunk["choice"][0].get("finish_reason", "")
                        if delta:
                            full_content += delta
                            print(delta, end="", flush=True)
                        if finish == "length":
                            print("\n 输出被截断，建议增大max_tokens")
                    except json.JSONDecodeError:
                        pass
        print()
        return full_content
