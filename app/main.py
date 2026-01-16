from __future__ import annotations

import json
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.responses import Response as FastAPIResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from .config import SESSION_SECRET
from .db import Base, engine, get_db
from . import models_
from .auth import get_user_by_email, create_user, verify_password
from .openai_client import generate_resume
from .schemas import ResumeOut
from .pdf_export import build_resume_pdf

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Resume Builder")

# Cookie-based session. Stores session data inside cookie (signed).
# Do NOT store secrets in request.session.
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie="resume_builder_session",
    same_site="lax",
    https_only=False,  # set True in production with HTTPS
)
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent  # 指向项目根目录
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
def require_login(request: Request) -> int | None:
    return request.session.get("user_id")
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    if require_login(request):
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "title": "Register"})

@app.post("/register", response_class=HTMLResponse)
def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    existing = get_user_by_email(db, email)
    if existing:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "该邮箱已注册。请直接登录。", "title": "Register"},
        )
    if len(password) < 6:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "密码至少 6 位。", "title": "Register"},
        )

    user = create_user(db, email, password)
    request.session["user_id"] = user.id
    return RedirectResponse(url="/dashboard", status_code=302)

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "title": "Login"})

@app.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "邮箱或密码错误。", "title": "Login"},
        )
    request.session["user_id"] = user.id
    return RedirectResponse(url="/dashboard", status_code=302)

@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user_id = require_login(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    resumes = (
        db.query(models_.Resume)
        .filter(models_.Resume.user_id == user_id)
        .order_by(models_.Resume.created_at.desc())
        .limit(20)
        .all()
    )
    rendered_resumes = [{"id": r.id, "created_at": r.created_at.strftime("%Y-%m-%d %H:%M")} for r in resumes]

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "resumes": rendered_resumes, "title": "Dashboard"},
    )

@app.post("/generate")
def generate(
    request: Request,
    db: Session = Depends(get_db),
    language: str = Form("zh"),
    headline: str = Form(""),
    name: str = Form(""),
    location: str = Form(""),
    contact_email: str = Form(""),
    phone: str = Form(""),
    linkedin: str = Form(""),
    github: str = Form(""),
    website: str = Form(""),
    skills: str = Form(""),
    experience_text: str = Form(""),
    education_text: str = Form(""),
    free_text: str = Form(""),
    job_desc: str = Form(""),
):
    user_id = require_login(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    profile_fields = {
        "headline": headline,
        "contact": {
            "name": name,
            "location": location,
            "email": contact_email,
            "phone": phone,
            "linkedin": linkedin,
            "github": github,
            "website": website,
        },
        "skills_raw": skills,
        "experience_text": experience_text,
        "education_text": education_text,
    }

    try:
        resume_obj = generate_resume(
            profile_fields=profile_fields,
            free_text=free_text,
            job_desc=job_desc,
            language=language,
        )
    except Exception as e:
        # Re-render dashboard with error
        return templates.TemplateResponse(
            "dashboard.html",
            {"request": request, "error": f"生成失败：{e}", "resumes": [], "title": "Dashboard"},
        )

    record = models_.Resume(
        user_id=user_id,
        input_json=json.dumps(
            {"profile_fields": profile_fields, "free_text": free_text, "job_desc": job_desc, "language": language},
            ensure_ascii=False,
        ),
        output_json=resume_obj.model_dump_json(ensure_ascii=False),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return RedirectResponse(url=f"/resume/{record.id}", status_code=302)

@app.get("/resume/{resume_id}", response_class=HTMLResponse)
def resume_view(resume_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = require_login(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    r = db.query(models_.Resume).filter(models_.Resume.id == resume_id, models_.Resume.user_id == user_id).first()
    if not r:
        return RedirectResponse(url="/dashboard", status_code=302)

    resume = ResumeOut.model_validate_json(r.output_json)
    return templates.TemplateResponse(
        "resume.html",
        {"request": request, "resume": resume, "resume_id": resume_id, "title": "Resume"},
    )

@app.get("/resume/{resume_id}/pdf")
def resume_pdf(resume_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = require_login(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    r = db.query(models_.Resume).filter(models_.Resume.id == resume_id, models_.Resume.user_id == user_id).first()
    if not r:
        return RedirectResponse(url="/dashboard", status_code=302)

    resume = ResumeOut.model_validate_json(r.output_json)
    pdf_bytes = build_resume_pdf(resume)

    headers = {"Content-Disposition": f'attachment; filename="resume_{resume_id}.pdf"'}
    return FastAPIResponse(content=pdf_bytes, media_type="application/pdf", headers=headers)
