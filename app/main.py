from __future__ import annotations

from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from pathlib import Path
import json

# 更新模块引用 to core, api, services
# Updated imports to core, api, services
from .core.config import settings
from .core.db import Base, engine, get_db, SessionLocal
from .core import models
from .core.schemas import ResumeOut

from .api.auth import get_user_by_email, create_user, verify_password
from .api.openai_test import router as openai_test_router
from .services.openai_client import generate_resume, test_api_connection
from .services.pdf_export import build_resume_pdf

# 创建数据库表
# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Resume Builder")
app.include_router(openai_test_router)

def ensure_test_user() -> None:
    """
    创建测试账号 (开发环境)
    Create a test account (development only)
    """
    if not settings.test_user_enabled:
        return
    email = settings.test_user_email.strip()
    password = settings.test_user_password
    if not email or not password:
        return
    db = SessionLocal()
    try:
        if not get_user_by_email(db, email):
            create_user(db, email, password)
    finally:
        db.close()

@app.on_event("startup")
def startup_seed_test_user() -> None:
    ensure_test_user()
# 配置 Session 中间件
# Session Middleware Configuration
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    session_cookie="resume_builder_session",
    same_site="lax",
    https_only=False,  # 生产环境请设为 True
)

# 挂载静态文件和模板
# Mount static files and templates
BASE_DIR = Path(__file__).resolve().parent.parent  # 项目根目录 Project Root
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

def require_login(request: Request) -> int | None:
    """
    检查用户是否登录
    Check if user is logged in
    """
    return request.session.get("user_id")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """
    首页重定向
    Home Redirect
    """
    if require_login(request):
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    """
    注册页面
    Register Page
    """
    return templates.TemplateResponse("register.html", {"request": request, "title": "注册 Register"})

@app.post("/register", response_class=HTMLResponse)
def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    用户注册处理
    User Registration Logic
    """
    user_exist = get_user_by_email(db, email)
    if user_exist:
        return templates.TemplateResponse("register.html", {
            "request": request, 
            "error": "该邮箱已被注册 Email already registered",
            "title": "注册 Register"
        })
    
    user = create_user(db, email, password)
    request.session["user_id"] = user.id
    return RedirectResponse(url="/dashboard", status_code=302)

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """
    登录页面
    Login Page
    """
    return templates.TemplateResponse("login.html", {"request": request, "title": "登录 Login"})

@app.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    用户登录处理
    User Login Logic
    """
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": "用户名或密码错误 Invalid credentials",
            "title": "登录 Login"
        })
    request.session["user_id"] = user.id
    return RedirectResponse(url="/dashboard", status_code=302)

@app.get("/logout")
def logout(request: Request):
    """
    退出登录
    Logout
    """
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    """
    用户仪表盘（简历列表）
    User Dashboard (Resume List)
    """
    user_id = require_login(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    resumes = db.query(models.Resume).filter(models.Resume.user_id == user_id).all()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "resumes": resumes,
        "title": "仪表盘 Dashboard"
    })

@app.get("/resume/new", response_class=HTMLResponse)
def new_resume_page(request: Request):
    """
    新建简历页面
    New Resume Page
    """
    if not require_login(request):
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("resume.html", {"request": request, "title": "创建简历 Create Resume"})

@app.post("/resume/generate", response_class=HTMLResponse)
def generate_resume_endpoint(
    request: Request,
    # 结构化字段
    name: str = Form(..., alias="name"),
    contact_email: str = Form(..., alias="contact_email"),
    phone: str = Form(""),
    location: str = Form(""),
    linkedin: str = Form(""),
    github: str = Form(""),
    website: str = Form(""),
    headline: str = Form(""),
    skills: str = Form(""),
    language: str = Form("zh"),
    # 大文本块
    experience_text: str = Form("", alias="experience_text"),
    education_text: str = Form("", alias="education_text"),
    free_text: str = Form("", alias="free_text"),
    job_desc: str = Form("", alias="job_desc"),
    openai_model: str = Form("gpt-4o-2024-08-06", alias="openai_model"),
    db: Session = Depends(get_db)
):
    """
    生成简历 API (调用 AI Agent)
    Generate Resume API (Calls AI Agent)
    """
    user_id = require_login(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    # 1. 组合所有信息调用 Agent
    # Combine all inputs and call Agent
    resume_out, ai_usage = generate_resume(
        name=name,
        email=contact_email,
        phone=phone,
        location=location,
        linkedin=linkedin,
        github=github,
        website=website,
        headline=headline,
        skills=skills,
        experience_text=experience_text,
        education_text=education_text,
        free_text=free_text,
        job_desc=job_desc,
        language=language,
        model_name=openai_model
    )

    # 2. 保存到数据库
    # Save to DB
    input_data = {
       "name": name,
       "email": contact_email,
       "phone": phone,
       "headline": headline,
       "skills": skills,
       "experience_text": experience_text,
       "education_text": education_text,
       "free_text": free_text,
       "job_desc": job_desc,
       "language": language
    }
    
    new_resume = models.Resume(
        user_id=user_id,
        input_json=json.dumps(input_data, ensure_ascii=False),
        output_json=resume_out.model_dump_json(), # Pydantic v2
        ai_usage=json.dumps(ai_usage, ensure_ascii=False)
    )
    db.add(new_resume)
    db.commit()
    db.refresh(new_resume)

    return RedirectResponse(url=f"/resume/{new_resume.id}", status_code=302)

@app.get("/resume/{resume_id}", response_class=HTMLResponse)
def view_resume(request: Request, resume_id: int, db: Session = Depends(get_db)):
    """
    查看简历详情
    View Resume Details
    """
    user_id = require_login(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    resume = db.query(models.Resume).filter(
        models.Resume.id == resume_id, 
        models.Resume.user_id == user_id
    ).first()
    
    if not resume:
        return Response("Resume not found", status_code=404)

    # 解析 JSON
    # Parse JSON
    data = json.loads(resume.output_json)
    usage = json.loads(resume.ai_usage) if resume.ai_usage else {}

    return templates.TemplateResponse("resume.html", {
        "request": request, 
        "resume": data,
        "usage": usage,
        "resume_id": resume.id,
        "title": "简历预览 Resume Preview"
    })

@app.get("/resume/{resume_id}/pdf")
def download_pdf(request: Request, resume_id: int, db: Session = Depends(get_db)):
    """
    导出 PDF
    Export PDF
    """
    user_id = require_login(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    resume = db.query(models.Resume).filter(
        models.Resume.id == resume_id, 
        models.Resume.user_id == user_id
    ).first()
    
    if not resume:
        return Response("Resume not found", status_code=404)

    data_dict = json.loads(resume.output_json)
    # 转换为 Schema
    try:
        resume_schema = ResumeOut(**data_dict)
    except Exception:
        # 异常处理：返回空结构
        resume_schema = ResumeOut(
            personal_info={"name": "Error", "email": ""},
            summary="Data validation error",
            education=[],
            work_experience=[],
            skills=[]
        )

    pdf_bytes = build_resume_pdf(resume_schema)
    
    return Response(
        content=pdf_bytes, 
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=resume_{resume_id}.pdf"}
    )

@app.get("/test-openai", response_class=HTMLResponse)
def test_openai_page(request: Request):
    """
    OpenAI 测试页面
    Test OpenAI Page
    """
    if not require_login(request):
        return RedirectResponse(url="/login", status_code=302)
        
    return templates.TemplateResponse("test_api.html", {
        "request": request, 
        "title": "测试 Test OpenAI API",
        "model_name": settings.openai_model
    })

@app.post("/test-openai-run", response_class=HTMLResponse)
def test_openai_run(request: Request):
    """
    执行 OpenAI 连接测试
    Execute OpenAI Connection Test
    """
    if not require_login(request):
        return RedirectResponse(url="/login", status_code=302)
    
    result = test_api_connection()
    
    return templates.TemplateResponse("test_api.html", {
        "request": request, 
        "title": "测试结果 Test Result",
        "result": result,
        "model_name": settings.openai_model
    })
