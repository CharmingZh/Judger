# Resume Builder (FastAPI + OpenAI)

A minimal full-stack (server-rendered) web app:
- User registration + login (session cookie)
- Detailed form input + free-text "fuzzy input"
- Calls OpenAI Responses API with Structured Outputs (Pydantic schema)
- Renders resume preview and supports PDF export (ReportLab, CJK-friendly font)

## 1) Install
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## 2) Configure
Copy `.env.example` -> `.env` and set:
- `OPENAI_API_KEY`
- `SESSION_SECRET` (use a long random string)

Optional (development only):
- `TEST_USER_ENABLED` (default: true)
- `TEST_USER_EMAIL` (default: test@example.com)
- `TEST_USER_PASSWORD` (default: test123456)

## 3) Run
```bash
uvicorn app.main:app --reload
```
Open: http://127.0.0.1:8000

## Test account (dev)
When `TEST_USER_ENABLED=true`, the app will auto-create a test account at startup (if it doesn't already exist):
- Email: `test@example.com`
- Password: `test123456`

Disable in production by setting `TEST_USER_ENABLED=false` and change the password if you keep it enabled.

## 4) PyCharm
- Open this folder as a project
- Set interpreter to `.venv`
- Run configuration: Module `uvicorn`, parameters: `app.main:app --reload`

## 5) Production notes
- Use HTTPS (important for cookies)
- Put reverse proxy (nginx) in front
- Rotate keys, monitor usage
- Consider server-side sessions (Redis) for larger apps
