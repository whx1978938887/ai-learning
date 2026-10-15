# 笔记与备忘

## 环境搭建

## 项目初始化

### 1.创建项目文件夹

```shell
mkdir 文件夹名称
cd 文件夹名称
```

### 2. 初始化uv环境

```shell
uv init
```

项目将生成：

- .venv/(Python虚拟环境)
- pyproject.toml(项目依赖管理文件)

### 3.导入python-dotenv库

```shell
uv add python-dotenv
```

### 4.创建入口文件

仅在本地项目根目录创建 `.env`，使用服务商要求的环境变量名。示例值必须替换为自己的密钥；`.env` 加入 `.gitignore`，不要提交到 Git：

```text
AI_API_KEY=replace_with_your_key
```

### 5.配置VS Code环境(可选)

1. 打开VS Code设置：按下`Ctrl+,`，点击右上角的“打开设置(JSON)”图标
2. 填入以下配置

```json
{
    // 自动选择你项目里的 uv 虚拟环境
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
    // 终端打开时自动激活虚拟环境
    "python.terminal.activateEnvironment": true,
    // 调试时从项目根目录加载本地环境变量文件
    "python.envFile": "${workspaceFolder}/.env"
}
```

### 6. 使用 uv 安装 Python 库（可选）

```bash
uv add requests
```

## 核心知识点

- [45 天每日学习讲义索引](./chats/00学习路线与复习计划.md)：从基础概念逐步进入项目实践；每篇提供术语解释、例子、易错点、阶梯练习和验收标准，优先支持 Mock/离线学习。
- [Day 1：密钥管理与模型 API](./chats/Day01-密钥管理与模型API.md)
- [Day 22：企业知识库架构与上传安全](./chats/Day22-企业知识库架构与上传安全.md)
- [Day 45：薄弱点复习与持续投递](./chats/Day45-薄弱点复习与持续投递.md)

## 注意事项

> **调用openai和requests的区别**
>
> 官方 SDK 通常封装了请求结构和响应解析；使用 requests 需要自行组装 HTTP 请求。
> 两种方式都需要设置超时、安全读取密钥并处理状态码和错误。
