from __future__ import annotations

import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
import os

from ..core.schemas import ResumeOut

def register_fonts():
    """
    注册中文字体 (防止乱码)
    Register Chinese Fonts
    注意：在非 Windows 环境可能需要调整字体路径或下载字体文件
    """
    # Windows 默认字体路径
    # Default Windows font path
    font_path = "C:/Windows/Fonts/msyh.ttc"  # 微软雅黑 (Microsoft YaHei)
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('msyh', font_path))
        return "msyh"
    
    # 尝试其他，或回退
    # Fallback
    return "Helvetica"

def build_resume_pdf(resume: ResumeOut) -> bytes:
    """
    生成简历 PDF 二进制流
    Generate Resume PDF bytes
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    font_name = register_fonts()
    
    # 标题 (姓名)
    c.setFont(font_name, 20)
    name = resume.personal_info.get("name", "Unknown Name")
    c.drawString(20 * mm, height - 20 * mm, name)
    
    # 联系方式
    c.setFont(font_name, 10)
    email = resume.personal_info.get("email", "")
    phone = resume.personal_info.get("phone", "")
    contact_info = f"Email: {email} | Phone: {phone}"
    c.drawString(20 * mm, height - 30 * mm, contact_info)
    
    y = height - 45 * mm
    
    # Summary
    if resume.summary:
        c.setFont(font_name, 12)
        c.drawString(20 * mm, y, "Summary / 个人总结")
        y -= 6 * mm
        c.setFont(font_name, 10)
        # 简单换行处理
        # Simple text wrapping
        text_object = c.beginText(20 * mm, y)
        text_object.setFont(font_name, 10)
        # 这里只是演示，不支持长字符串自动换行。实际可用 reportlab.platypus
        # Just demo, reportlab.platypus is better for wrapping
        lines = resume.summary.split('\n')
        for line in lines:
            text_object.textLine(line)
        c.drawText(text_object)
        y -= (len(lines) * 5 * mm + 10 * mm)

    # 技能 Skills
    if resume.skills:
        c.setFont(font_name, 12)
        c.drawString(20 * mm, y, "Skills / 技能")
        y -= 6 * mm
        c.setFont(font_name, 10)
        skills_str = ", ".join(resume.skills)
        c.drawString(20 * mm, y, skills_str)
        y -= 15 * mm

    # 工作经历 Work Experience
    if resume.work_experience:
        c.setFont(font_name, 12)
        c.drawString(20 * mm, y, "Work Experience / 工作经历")
        y -= 8 * mm
        
        c.setFont(font_name, 10)
        for job in resume.work_experience:
            c.setFont(font_name, 10) # bold?
            title_line = f"{job.role} at {job.company} ({job.start_date} - {job.end_date})"
            c.drawString(20 * mm, y, title_line)
            y -= 5 * mm
            
            # Details
            for detail in job.description:
                c.drawString(25 * mm, y, f"- {detail}")
                y -= 5 * mm
            y -= 5 * mm

    # 教育 Education
    if resume.education:
        # Check space
        if y < 50 * mm:
            c.showPage()
            y = height - 20 * mm
            c.setFont(font_name, 10)

        c.setFont(font_name, 12)
        c.drawString(20 * mm, y, "Education / 教育经历")
        y -= 8 * mm
        c.setFont(font_name, 10)
        for edu in resume.education:
            line = f"{edu.degree} in {edu.field_of_study}, {edu.school} ({edu.year})"
            c.drawString(20 * mm, y, line)
            y -= 6 * mm

    c.save()
    buffer.seek(0)
    return buffer.read()
