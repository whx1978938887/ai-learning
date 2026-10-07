# Day 9：聊天重构、PromptTemplate 与 OutputParser

**今天的目标：**理解模板变量、会话历史与结构化输出；让程序区分“格式坏了”和“内容不符合规则”。

## 1. PromptTemplate：可重复填写的说明书

Prompt（提示）是发给模型的任务说明。PromptTemplate（提示模板）把固定说明和会变化的值分开，例如同一个反馈分类任务可以反复传入不同文本。花括号中的名字就是变量：

```text
请把下面反馈归类。只允许输出 JSON。
反馈：{feedback}
```

渲染（render，填入变量形成最终文本）时必须提供所有变量。少给变量通常是程序错误，应在调用模型前报告，而不是发一个残缺 Prompt。用户提供的 `feedback` 是**待分析数据**，不是可信的系统指令；不要把用户内容拼接成可覆盖应用规则的指令。

可用 Python 标准库 `format` 演示：

```python
template = "请分类反馈：{feedback}"
prompt = template.format(feedback="物流很快，包装完好")
print(prompt)
```

输出：`请分类反馈：物流很快，包装完好`。

## 2. Parser 与 Schema：两层检查

模型常返回文本。OutputParser（输出解析器）把文本转成程序能处理的值，例如把 JSON 字符串变成字典。Schema（结构规则）定义字段、类型和允许值。两者是不同检查：

1. **语法检查：**文本是否为有效 JSON？
2. **结构检查：**解析后是不是对象？必需字段是否齐全？类型对不对？
3. **业务检查：**`sentiment` 是否是本程序允许的值？`evidence` 是否为非空字符串？

因此，“JSON 能解析”不等于“JSON 满足业务要求”。下面用标准库演示这三层：

```python
import json

ALLOWED_SENTIMENTS = {"positive", "neutral", "negative"}

def parse_feedback(raw: str) -> dict[str, str]:
    value = json.loads(raw)  # 无效 JSON 会抛出 JSONDecodeError
    if not isinstance(value, dict):
        raise ValueError("顶层必须是 JSON 对象")

    required = {"category", "sentiment", "evidence"}
    if set(value) != required:
        raise ValueError(f"字段必须恰好为：{sorted(required)}")
    if not all(isinstance(value[key], str) for key in required):
        raise ValueError("所有字段都必须是字符串")
    if value["sentiment"] not in ALLOWED_SENTIMENTS:
        raise ValueError("sentiment 不在允许范围")
    if not value["evidence"].strip():
        raise ValueError("evidence 不能为空")
    return value

print(parse_feedback(
    '{"category":"delivery","sentiment":"positive","evidence":"物流很快"}'
))
```

输出是字典：`{'category': 'delivery', 'sentiment': 'positive', 'evidence': '物流很快'}`。实际项目可以用 schema 校验库，但在安装或采用前要确认版本与项目需求。

**失败要明确：**JSON 错误、缺字段、类型不对、业务值非法最好有不同错误信息；不要用 `{}`、空字符串或默认类别冒充成功。若选择重试生成，也要有限次，并保留失败原因。

## 3. 多轮历史与会话隔离

Session（会话）/thread（对话线程）是一次独立的聊天上下文标识。每个 session 只能读写自己的历史。即使模型框架提供历史管理，也要明确历史保存在哪里、保存多久、是否跨程序重启保留，以及用户如何清除。

简单实现可用字典（只在当前进程中，重启会消失）：

```python
histories: dict[str, list[str]] = {}

def add_message(session_id: str, text: str) -> None:
    histories.setdefault(session_id, []).append(text)

add_message("alice", "我喜欢绿茶")
add_message("bob", "我喜欢咖啡")
print(histories["alice"])
```

输出：`['我喜欢绿茶']`。生产环境不能只相信用户传来的 session ID 来授权访问；服务端需要确认当前用户有权访问该会话。

## 常见初学错误

- 模板变量漏填或名字拼错，结果到调用模型时才出错。
- 只调用 `json.loads`，却没查字段、类型、允许值和长度。
- 解析失败时静默返回空对象，令下游误以为操作成功。
- 把多个用户历史放到一个列表，导致串话或隐私泄露。
- 无限增加对话历史。上下文（模型本次能看到的输入）有限，应制定裁剪/摘要规则，且不要删掉任务所需信息。

## 练习（由浅入深）

1. **热身：填写模板。**把 `"请分类：{feedback}"` 填入 `"服务态度很好"`。验收：结果含完整原文；故意漏传 `feedback` 时能看到明确模板错误。
2. **跟做：校验三种输出。**将示例函数用于合法 JSON、缺少 `evidence` 的 JSON、`sentiment:"great"`。预期第一个返回字典，后两个分别因缺字段、非法取值而拒绝。
3. **独立完成：会话隔离测试。**创建 `alice`、`bob` 两个 session，各加入一条不同历史。验收：读取 Alice 只能得到 Alice 内容；测试缺字段、无效 JSON、非对象顶层及重启持久化策略；在 README/注释中说明历史是内存保存还是持久化。

## 今日验收与复习

- 能分别定位模板渲染错误、JSON 解析错误和业务校验错误。
- 每个会话有独立历史，且持久化与清除规则明确。
- 所有无效输出都有可观察的失败，不会假装成功。

**复习卡片：**请用自己的话区分“JSON 能解析”和“JSON 满足业务要求”。

**小词典：**模板变量＝待填入的变化值；Parser＝把文本解析成程序值的组件；Schema＝数据形状与约束；Session＝彼此隔离的一段会话；上下文＝本次送给模型的输入内容。
