def chunk_text(text: str, chunk_size: int):
    if not isinstance(chunk_size, int) or chunk_size < 0:
        raise ValueError("分块大小必须为正整数")
    sta = 0
    while sta <= len(text):
        if sta + chunk_size <= len(text):
            yield text[sta : sta + chunk_size]
        else:
            yield text[sta:]
        sta += chunk_size


if __name__ == "__main__":
    gen = chunk_text("你好", 1)
    print(next(gen))
    print(next(gen))
