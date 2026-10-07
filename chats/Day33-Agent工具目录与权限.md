# Day 33：Agent 工具目录与权限设计

**今天的目标：**把 Agent 能力限制在清楚的白名单工具内，并明确每项权限、输入和副作用。

## 工具到底是什么

**Agent**是能根据目标多次调用模型和工具的程序。工具是它可请求应用代为执行的受限功能，例如查天气或创建待办。模型生成的是“建议调用哪个工具及参数”，不是已经发生的现实操作。实际执行必须由应用代码决定。

如果把模型输出的任意函数名直接传给 Python 执行，就等于让不可信文本选择任意代码，范围远超需求。**白名单**是明确批准的一组工具：程序只接受目录中注册的名称；未知名称必须拒绝。目录描述帮助模型选择；执行端仍需做 schema（输入/输出结构）校验、权限校验和业务规则校验。

## 每个目录条目要写什么

至少记录：稳定的名称、用途、参数和返回格式、所需权限、超时、是否幂等、审计字段、副作用等级、是否需人工确认。**幂等**表示同一请求重复执行不会造成额外效果；查天气通常可重复，创建待办或发邮件则可能重复产生副作用。

| 工具 | 权限/影响 | 关键保护 |
|---|---|---|
| `get_weather(city)` | 只读、低影响 | 城市长度/枚举校验、超时 |
| `create_todo(title)` | 写入、可重复创建 | 用户身份、长度校验、去重键 |
| `send_email(to, subject, body)` | 对外发送、高影响 | 收件人授权、内容预览、明确确认、审计 |

权限要遵循**最小权限**：只给完成任务必需的能力。用户可创建待办，不代表可代表用户发邮件。工具返回值也要视作不可信数据；不能把网页/邮件中的指令当成授权。

## 简化的本地白名单示例

```python
TOOLS = {
    "get_weather": {"permission": "weather:read", "side_effect": "none"},
    "create_todo": {"permission": "todo:write", "side_effect": "write"},
}

def authorize_call(name, granted_permissions):
    tool = TOOLS.get(name)
    if tool is None:
        raise ValueError("Unknown tool")
    if tool["permission"] not in granted_permissions:
        raise PermissionError("Not authorized")
    return "allowed"

print(authorize_call("get_weather", {"weather:read"}))
# allowed
```

这是概念示例。真实应用必须在这里调用固定实现，进行参数验证、记录请求 ID，并对高影响操作增加确认；不要通过模型提供的字符串拼接代码或命令。

## 常见错误

- 只在 Prompt 里说“不要越权”，没有在执行端拒绝不合法的调用。
- 把模型的工具调用当作已授权命令。
- 只检查工具名，不检查用户、资源归属和参数。
- 工具目录描述很严格，执行端却允许任意收件人/路径。
- 对非幂等的写入操作自动重试，导致重复创建或重复发送。
- 忽略审计记录，事后不知道是谁在何时触发了什么。

## 深入理解：一次工具调用的四道门

将模型的建议看成一张“待审批工单”，执行器至少检查四件事：

1. **工具注册：**名字必须与应用目录中的名称完全一致；拒绝诸如 `run_shell`、`delete_all` 的任意新名称。
2. **输入结构：**参数类型、长度、格式和允许值都满足 schema；例如邮箱格式有效、标题不超过限制。
3. **调用者授权：**当前身份拥有所需权限，并且目标资源确实属于此用户或其可管理空间。
4. **副作用策略：**只读调用可直接执行；写入操作要考虑去重；高影响操作先展示具体参数并等待确认。

任何一道门失败，都不调用外部实现。错误应告知“你没有权限创建提醒”或“参数格式不正确”，而不是返回另一个用户的资料或内部堆栈。模型可能会因为上下文而提出不合规调用，这不等于恶意，也不影响应用必须拒绝它。

## 参数约束比类型检查更具体

schema 不只是说 `city` 是字符串。要限制字符串长度、字符范围、必填字段、枚举值、日期是否在未来、目标 ID 是否属于当前用户。避免用模型提供的路径、SQL 片段或 Shell 命令直接执行。若工具允许查询文档，接收一个文档 ID 后在服务端按用户权限读取；不要让模型自由指定磁盘路径。

目录也应描述工具的能力边界，例如“查询当前用户自己的提醒”比“查询提醒”更不易误用；同时描述无权时可能出现的结果和超时特性。描述有助于模型挑选合适工具，但真正授权仍由服务端代码决定。

## 审计日志与隐私

对重要调用可记录调用者/租户 ID、工具名、时间、请求 ID、允许/拒绝、操作结果 ID 和确认版本。避免记录 API 密钥、完整邮件正文、密码或不必要的用户输入。高风险审计日志应有访问控制、保留期限和删除规则；审计不是“把所有内容永久保存”。

## 更完整的白名单伪实现

```python
TOOLS = {
    "create_todo": {
        "permission": "todo:write",
        "required": {"title"},
        "max_title_length": 120,
    }
}

def validate_request(name, args, permissions):
    tool = TOOLS.get(name)
    if tool is None:
        raise ValueError("Unknown tool")
    if tool["permission"] not in permissions:
        raise PermissionError("Not authorized")
    if set(args) != tool["required"]:
        raise ValueError("Invalid arguments")
    if not isinstance(args["title"], str) or not args["title"].strip():
        raise ValueError("Invalid title")
    if len(args["title"]) > tool["max_title_length"]:
        raise ValueError("Title too long")
    return True
```

这仍然只是规则演示：生产执行器还需身份来自可信认证、数据存储隔离、速率限制、超时、错误映射和审计；不能相信客户端自己传来的 `permissions`。

## 动手练习

1. **热身：**把天气查询、创建待办、发送邮件分别标为只读/写入/高影响。验收：说明重复执行的不同后果。
2. **引导：**为这三种工具填写用途、schema、权限、超时、幂等性和确认策略。验收：邮件必须展示收件人/正文并获得确认。
3. **独立：**写一个白名单检查器并模拟未知工具与越权调用。验收：两种情况都拒绝；授权用户的只读调用通过；审计不记录密码或完整敏感正文。

## 复习与词汇

- **复习：**模型侧描述帮助模型选对工具；应用侧授权保护真实数据与动作。两者都需要，因为模型输出不能作为权限依据。
- **schema：**字段、类型和限制组成的数据契约；**副作用：**改变外部状态的操作；**最小权限：**只授予完成任务所需的能力。
- 工具循环与安全执行边界可参考 [Day 40：Agent 面试复习](Day40-Agent工具调用与框架面试复习.md)。
