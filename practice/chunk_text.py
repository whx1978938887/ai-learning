def chunk_text(text: str, chunk_size: int):
    if not isinstance(chunk_size, int):
        raise ValueError("分块大小必须为正整数")
    print(text)
    yield text[:len(text)/chunk_size]

if __name__ == "__main__":
    for str in chunk_text("我们在一起！",2):
        print(str,end=' ')