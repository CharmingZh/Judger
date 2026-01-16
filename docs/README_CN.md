# 项目开发文档 (Developer Documentation)

## 1. 项目简介 (Introduction)
这是一个基于 FastAPI 和 OpenAI (ChatGPT) 的智能简历生成器应用。用户可以输入杂乱的个人信息文本，应用将调用 GPT 模型将其整理为结构化的简历数据，并支持导出 PDF。

## 2. 目录结构 (Directory Structure)

```
CV_Helper/
├── .env                # [机密] 环境变量配置文件 (包含 API Key，不要提交到 Git)
├── .gitignore          # Git 忽略规则
├── requirements.txt    # Python 依赖列表
├── run_server.ps1      # 启动服务器的脚本
├── README.md           # 本文档
├── static/             # [前端] 静态文件 (CSS, JS, Images)
├── templates/          # [前端] HTML 模板 (Jinja2)
├── app/                # [后端] 应用核心代码
│   ├── main.py             # 入口文件 (Web Server, Routes)
│   ├── api/                # API 接口层
│   │   └── auth.py         # 认证相关接口 (登录注册)
│   ├── core/               # 核心配置与数据层
│   │   ├── config.py       # 全局配置 (读取 .env)
│   │   ├── db.py           # 数据库连接 (SQLAlchemy)
│   │   ├── models.py       # 数据库模型 (ORM Users, Resumes 等)
│   │   └── schemas.py      # Pydantic 数据模式 (OpenAI 结构化输出定义)
│   ├── services/           # 业务逻辑服务层 (Agent)
│   │   ├── openai_client.py   # [Agent] OpenAI 客户端封装 (调用 GPT 生成简历)
│   │   └── pdf_export.py      # PDF 导出服务 (ReportLab)
```

## 3. 关键模块说明 (Key Modules)

### 3.1 核心配置 (`app/core/config.py`)
- 使用 `pydantic-settings` 库安全加载 `.env` 中的环境变量。
- **机密管理**：`OPENAI_API_KEY` 和 `SESSION_SECRET` 均从此处读取，不在代码中硬编码。

### 3.2 Agent 服务 (`app/services/openai_client.py`)
- **Agent 角色**：封装了与 ChatGPT 的交互逻辑。
- **调用方式**：使用 `client.beta.chat.completions.parse` (Structured Outputs)，这意味着 GPT 返回的必定是符合 `ResumeOut` 这个 JSON Schema 的数据，无需复杂的正则解析。

### 3.3 数据库 (`app/core`)
- `db.py`: 管理 SQLite 连接 Session。
- `models.py`: 定义 SQL 表结构。如果是开发环境，每次重启主程序会自动建表 (`Base.metadata.create_all`)。

## 4. 如何运行 (How to Run)

1. **环境配置**：
   确保 `.env` 文件存在，并填入了正确的 `OPENAI_API_KEY`。
   
   ```ini
   OPENAI_API_KEY=sk-proj-...
   ```

2. **启动命令**：
   在终端运行：
   ```powershell
   .\run_server.ps1
   ```
   或者直接：
   ```bash
   uvicorn app.main:app --reload
   ```

3. **访问**：
   打开浏览器访问 [http://127.0.0.1:8000](http://127.0.0.1:8000)

## 5. 安全注意事项 (Security Notes)

- **API Key**: 绝对不要提交 `.env` 文件到 GitHub。
- **Passlib**: 生产环境建议使用更复杂的 Session 存储 (如 Redis) 而非 Cookie。
