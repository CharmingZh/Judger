from __future__ import annotations

import json
from typing import Any, Dict
from pathlib import Path

from openai import OpenAI
from ..core.config import settings
from ..core.schemas import ResumeOut

# 加载 Prompt 文件
PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "resume_generator_v2.txt"

def load_system_prompt() -> str:
    """Read system prompt from file"""
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error loading prompt: {e}")
        # Fallback prompt if file missing
        return "You are a helpful resume assistant."

# 初始化 OpenAI 客户端 (使用 core/config 中的配置)
# Initialize OpenAI Client using core/config settings
client = OpenAI(api_key=settings.openai_api_key)

def test_api_connection() -> Dict[str, Any]:
    """
    测试 OpenAI API 连接
    Test OpenAI API Connection
    """
    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "user", "content": "Say 'Health check passed' if you can hear me."}
            ],
            max_tokens=20
        )
        return {
            "success": True, 
            "message": response.choices[0].message.content,
            "model": response.model,
            "usage": response.usage.model_dump()
        }
    except Exception as e:
        return {
            "success": False, 
            "error": str(e)
        }

def generate_resume(
    name: str,
    email: str,
    phone: str,
    location: str,
    linkedin: str,
    github: str,
    website: str,
    headline: str,
    skills: str,
    experience_text: str,
    education_text: str,
    free_text: str,
    job_desc: str,
    language: str,
    model_name: str = "gpt-4o-2024-08-06"
) -> tuple[ResumeOut, dict]:
    """
    调用 OpenAI API 生成简历数据结构
    Call OpenAI API to generate resume data structure
    Returns: (ResumeOut, usage_dict)
    """
    
    system_prompt = load_system_prompt()

    # 构建用户输入 Prompt
    # Build User Prompt
    user_content = f"""
    # Prefer Output Language
    {language}

    # User Basic Info
    Name: {name}
    Email: {email}
    Phone: {phone}
    Location: {location}
    LinkedIn: {linkedin}
    GitHub: {github}
    Website: {website}
    Headline: {headline}

    # Skills Input
    {skills}

    # Experience Input
    {experience_text}

    # Education Input
    {education_text}

    # Additional / Free Text Input
    {free_text}

    # Target Job JD
    {job_desc}
    """


    # 调用 ChatCompletion (使用 tool_calls/function_calling 的 Structured Outputs 或者是 json_object)
    # 本例使用最新的 beta.parse (Structured Outputs)
    # Use selected model or fallback to default
    target_model = model_name if model_name else settings.openai_model
    try:
        completion = client.beta.chat.completions.parse(
            model=target_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            response_format=ResumeOut,
        )
        
        message = completion.choices[0].message
        usage = completion.usage.model_dump() if completion.usage else {}
        
        if message.parsed:
            return message.parsed, usage
        else:
            # Fallback (Refusal)
            print("Refusal:", message.refusal)
            return ResumeOut(
                contact={"name": name, "email": email, "phone": phone},
                summary="AI无法生成简历，请检查输入。(AI failed to generate resume)",
                education=[], experience=[], skills=[]
            ), usage

    except Exception as e:
        print(f"OpenAI API Error: {e}")
        # 返回空对象以防崩溃
        return ResumeOut(
            contact={"name": name, "email": email, "phone": phone},
            summary=f"Error generating resume: {e}",
            education=[], experience=[], skills=[]
        ), {}
