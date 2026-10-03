# 笔记与备忘

## 环境搭建

## 项目初始化

### 1.创建项目文件夹

```shell
mkdir 文件夹名称
cd 文件夹`
```

### 2. 初始化uv环境

```shell
uv init
```

项目将生成：

- .venv/(Python虚拟环境)
- pyproject.toml(项目依赖管理文件)

### 3.创建入口文件

在src文件夹新建一个.env文件，把密钥写进去，格式如下：

```text
OPENAI_API_KEY=sk-xxxxxx
AUTHROIC_API_KAY=sk-xxxxxx
```

### 4.配置VS Code环境(可选)

1. 打开VS Code设置：按下`Ctrl+,`，点击右上角的“打开设置(JSON)”图标
2. 填入以下配置

```json
{
    // 自动选择你项目里的 uv 虚拟环境
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
    // 终端打开时自动激活虚拟环境
    "python.terminal.activateEnvironment": true,
    // 调试时自动加载 src 目录下的 .env 文件
    "python.envFile": "${workspaceFolder}/src/.env"
}
```

### 4.使用uv安装Python库

```bash
uv add requests
```

## 核心知识点

### 1.[掌握流式输出与参数调优](./chats/01掌握流式输出和参数调优md)

- [流式输出](./chats/02HTTP请求与响应的流式处理.md)
- [指数退避重试实现](./chats/03指数退避重试实现.md)
- [对比不同模型的输出质量、响应速度和成本](./chats/04对比不同模型的输出质量响应速度和成本.md)
- [编程练习题](./chats/05编程题.md)
- [结构化 Prompt 设计](./chats/06结构化Prompt设计.md)
- [CoT、零样本/少样本学习与 Negative Prompting](./chats/07CoT零样本少样本与NegativePrompting.md)
- [练习模型输出 JSON 与 Markdown 表格](./chats/08练习模型输出JSON与Markdown表格.md)
- [编写 Prompt 模板库：文案生成、代码生成与数据提取](./chats/09编写Prompt模板库.md)

## 注意事项

> **调用openai和requests的区别**
>
> openai内部封装了请求
> 调用requests需要自己封装请求
