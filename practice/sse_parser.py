import json


class SSEParser:
    buffer = ""
    chunk_list = []

    def feed(self, data: bytes):
        self.buffer += data.decode("utf-8")
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            if line.startswith("data: ") and line.strip() != "data:[DONE]":
                try:
                    chunk = json.load(line[:6])
                    self.chunk_list.append(chunk)
                except json.JSONDecodeError:
                    pass
        return self.chunk_list

    def close(self):
        if not self.buffer.strip():
            raise BufferError
        return self.chunk_list


if __name__ == "__main__":
    ss = SSEParser()
    print(ss.feed())
