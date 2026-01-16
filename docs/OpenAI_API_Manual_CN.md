# OpenAI API 使用手册 (学习指南)

这份手册旨在帮助您理解如何调用 OpenAI 的 ChatGPT API，包括核心概念、参数详解和最佳实践。

---

## 1. 核心概念 (Core Concepts)

要调用 ChatGPT，我们最常用的接口是 **Chat Completions API** (`v1/chat/completions`).

它的工作原理是：你发给 API 一个“消息列表 (Messages)”，API 返回给你一个“消息 (Message)”。

### 角色 (Roles)
消息列表中的每一条消息都有一个角色：
*   **`system`** (系统): 设定 AI 的行为模式、身份或规则。相当于“人设”或“幕后指令”。（例如：“你是一个专业的翻译官。”）
*   **`user`** (用户): 最终用户的输入问题或指令。
*   **`assistant`** (助手): AI 之前的回复。通常用于多轮对话中，把历史记录发回给 AI，让它有上下文记忆。

---

## 2. 请求参数详解 (Parameters)

调用 `client.chat.completions.create(...)` 时，主要涉及以下参数：

| 参数名 | 必填 | 描述 | 推荐值/示例 |
| :--- | :--- | :--- | :--- |
| **`model`** | 是 | 指定使用的模型ID。 | `gpt-4o`, `gpt-4o-mini`, `gpt-3.5-turbo` |
| **`messages`** | 是 | 消息列表对象。 | `[{"role": "user", "content": "你好"}]` |
| `temperature` | 否 | **随机性控制** (0.0 - 2.0)。<br>• `0.0`: 最确定、最逻辑、重复性高（适合代码、数学）。<br>• `0.7-1.0`: 默认值，有一定创意。<br>• `>1.0`: 非常随机，容易胡言乱语。 | `0.7` (聊天), `0.0` (数据提取) |
| `max_tokens` | 否 | 回复生成的最大 Token 数。防止 AI 废话连篇消耗预算。 | `500` - `4096` |
| `top_p` | 否 | 另一种随机性控制 (Nucleus Sampling)。建议只设置 `temperature` 或 `top_p` 其中之一，不要同时改。 | `1.0` (默认) |
| `stream` | 否 | **流式传输**。如果设为 `True`，回复会像打字机一样一个字一个字蹦出来，体验更好。 | `True` / `False` |
| `json_mode` / `response_format` | 否 | 强制 AI 输出合法的 JSON 格式。非常适合程序调用。 | `{"type": "json_object"}` |
| `tools` | 否 | **函数调用 (Function Calling)**。告诉 AI 它可以使用哪些工具函数。 | (高级用法，详情见后文) |

---

## 3. 请求示例 (Basic Request)

```python
from openai import OpenAI
import os

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "你是一个乐于助人的助手。"},
        {"role": "user", "content": "给我讲个笑话。"}
    ],
    temperature=0.7,
)

# 获取回复内容
print(response.choices[0].message.content)
```

---

## 4. 进阶：结构化输出 (Structured Outputs)

OpenAI 最近推出了更强大的 `beta.parse` 方法，结合 Python 的 `Pydantic` 库，可以保证 AI **100% 严格**按照你定义的数据结构返回数据。这在本项目中被用于生成简历数据。

### 代码示例：

```python
from pydantic import BaseModel
from openai import OpenAI

class Step(BaseModel):
    explanation: str
    output: str

class MathResponse(BaseModel):
    steps: list[Step]
    final_answer: str

client = OpenAI()

completion = client.beta.chat.completions.parse(
    model="gpt-4o-2024-08-06",
    messages=[
        {"role": "system", "content": "你是一个数学老师。"},
        {"role": "user", "content": "求解 8x + 7 = -23"}
    ],
    response_format=MathResponse, # 传入这个 Schema
)

# 此时 parsing 已经自动完成，直接当对象用！
result = completion.choices[0].message.parsed
print(result.final_answer) 
```

---

## 5. Token 与 计费 (Pricing)

OpenAI 不按“字数”计费，而是按 **Token** 计费。
*   Token 是文本的切片单位。
*   大约 **1000 Tokens ≈ 750 个英文单词 ≈ 400-500 个汉字**。
*   计费公式：**(输入的 Prompt Tokens + 输出的 Completion Tokens) × 单价**。
*   `GPT-4o` 比 `GPT-3.5` 贵很多，但更聪明。

---

## 6. 常见错误 (Troubleshooting)

*   `AuthenticationError (401)`: API Key 错误或过期。
*   `RateLimitError (429)`: 
    1. 你发请求太快了。
    2. **你的账户余额不足** (Free Trial 用光了，或者信用卡没扣成功)。
*   `BadRequestError (400)`: 请求格式不对（例如 `messages` 列表是空的，或者 JSON 格式错误）。
*   `context_length_exceeded`: 文本太长，超过了模型的上下文窗口（通常是 4k, 8k, 16k 或 128k tokens）。

## 7. 安全开发 (Security)

*   **永远不要** 将 API Key 提交到 GitHub。
*   使用 `.env` 文件管理密钥。
*   设置 Usage Limit (用量限额)：在 OpenAI 账户设置里设置每月花费上限（例如 $10），防止意外刷爆信用卡。

---

*希望这份手册对您的学习有所帮助！*
