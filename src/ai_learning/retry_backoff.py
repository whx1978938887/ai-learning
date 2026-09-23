import time
import random


def retry_with_backoff(func, max_retries=3, base_delay=1.0, max_delay=60):
    """带指数退避和随机抖动的重试函数"""
    retryable_status = {429, 500, 502, 503, 504}

    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            status_code = getattr(e, "status_code", None)
            if status_code not in retryable_status:
                raise  # 不可重试错误直接抛出

            if attempt == max_retries:
                raise  # 重试耗尽，触发降级

            delay = min(base_delay * (2**attempt), max_delay)
            jitter = random.uniform(0, delay * 0.5)  # 随机抖动避免惊群效应
            time.sleep(delay + jitter)
