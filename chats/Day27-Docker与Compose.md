# Day 27：Docker 与 Compose

**今天的目标：**看懂镜像、容器、卷和 Compose，并能规划一个不把秘密打包进去的本地服务。

## 先建立直觉

应用在“我的电脑能运行”，不代表在别人的电脑也能运行：Python 版本、依赖、系统库都可能不同。Docker 把应用与运行环境描述为可重复构建的**镜像**（image）；启动镜像得到一个正在运行的**容器**（container）。可以把镜像想成菜谱和备料，把容器想成按菜谱做出的一锅菜。同一镜像可以启动多个容器。

容器通常可随时删除重建，因此容器内部文件不适合作为唯一数据副本。**卷**（volume）是容器外部、可在容器重建后保留的数据位置。`docker compose` 用一个 YAML 文件一起启动应用及其依赖服务，适合本地开发或小型部署；它不是自动的生产级高可用平台。

## 构建时与运行时

`Dockerfile`描述怎样构建镜像；`compose.yaml`描述启动时如何连接服务、映射端口、挂载卷和传入配置。构建时复制进镜像的文件会留在镜像层；所以不能用 `COPY . .` 把 `.env`、Git 历史或大数据集打进去。`.dockerignore` 用来排除构建上下文（Docker 构建时能看到的文件集合）。

下面用 Python 标准库做一个无外部依赖的 Mock API，因此不需要安装包。把代码保存为 `main.py`：

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY main.py .
RUN useradd --create-home appuser && mkdir /app/data && chown appuser:appuser /app/data
USER appuser
EXPOSE 8000
CMD ["python", "main.py"]
```

```python
# main.py
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            body = json.dumps({"status": "ok"}).encode("utf-8")
        elif self.path == "/notes":
            notes_file = Path("/app/data/notes.txt")
            notes = notes_file.read_text(encoding="utf-8") if notes_file.exists() else ""
            body = json.dumps({"notes": notes.splitlines()}).encode("utf-8")
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/notes":
            self.send_error(404)
            return
        size = int(self.headers.get("Content-Length", "0"))
        note = self.rfile.read(size).decode("utf-8").strip()
        with Path("/app/data/notes.txt").open("a", encoding="utf-8") as notes_file:
            notes_file.write(note + "\n")
        self.send_response(201)
        self.end_headers()

HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
```

```text
# .dockerignore
.git
.env
__pycache__/
*.log
data/
```

`.env` 不进入镜像，但若服务运行时确实需要密钥，应通过受控的运行环境变量或 Secret 注入；不要把真实值写进 Dockerfile、命令历史或版本库。容器进程也尽量用非 root 用户运行，减少意外获得的系统权限。

## Compose 与健康检查

健康检查（health check）是容器按间隔询问服务“是否能正常响应”。它不同于进程还活着：进程存在但 API 卡死时，探测仍可能失败。数据卷则解决重建后仍需保留的数据问题。

```yaml
services:
  api:
    build: .
    ports: ["8000:8000"]
    volumes: ["app-data:/app/data"]
    env_file: .env
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 3s
      retries: 3
volumes:
  app-data:
```

保存代码和 Docker 文件后，创建一个空的 `.env`（或从 Compose 文件中删去 `env_file`），在项目目录执行 `docker compose up --build`，再访问 `http://localhost:8000/health`，应得到 `{"status":"ok"}`。要检查持久化，可向 `/notes` 发送一段 POST 文本，再 GET `/notes`；重建容器后，记录仍应存在，因为它在 `/app/data` 命名卷中。上例 Compose 通过 `env_file` 读取 `.env`，所以仍需把 `.env` 放进 `.gitignore`；这个不依赖秘密的 Mock 服务不需要在文件中填写任何变量。提交只有变量名的 `.env.example`。正式环境的秘密管理方式要按平台配置。删除容器和删除卷是不同操作：卷通常独立于容器保留，`docker compose down -v` 会请求删除卷，执行前确认其中数据是否可丢弃。

## 常见错误

- 误把镜像当容器，或以为容器删除后数据必然还在。
- 忘记 `.dockerignore`，把 `.env`、`.git`、缓存和私有数据发送给构建器。
- 在 Dockerfile `ENV API_KEY=...`：秘密会进入镜像元数据/历史。
- 将容器端口和主机端口混淆；`8000:8000` 左边是主机，右边是容器。
- 认为有 health check 就代表服务安全、备份完整或可扩容。

## 动手练习

1. **热身：**说出镜像、容器、卷各自的作用。验收：能解释容器可重建而卷用于保留数据。
2. **引导：**为一个 Mock API 补齐 Dockerfile、`.dockerignore` 和 Compose 健康检查。验收：非 root 用户运行、端口可访问、`.env` 不在构建上下文。
3. **独立：**启动服务，在卷中写一份虚构数据后重建容器。验收：服务健康、数据是否保留符合设计；检查镜像层/仓库中没有秘密。

## 复习与词汇

- **复习：**删除容器和删除持久化卷总是同一件事吗？不是；容器是运行实例，卷是独立数据存储，具体清理命令要小心确认。
- **构建上下文：**Docker 构建可读取的文件范围；**非 root：**用普通用户身份运行应用；**持久化：**在进程/容器结束后仍保存数据。
