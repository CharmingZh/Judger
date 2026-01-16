from __future__ import annotations

import json
from typing import Any, Dict
from pathlib import Path

from openai import OpenAI
from ..core.config import settings
from ..core.schemas import ResumeOut

# 加载 Prompt 文件
PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "resume_generator_v1.txt"

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

def generate_resume(raw_text: str, user_name: str, user_email: str, user_phone: str) -> ResumeOut:
    """
    调用 OpenAI API 生成简历数据结构
    Call OpenAI API to generate resume data structure
    
    :param raw_text: 用户输入的原始文本 (User raw input)
    :param user_name: 用户姓名 (User name)
    :param user_email: 用户邮箱 (User email)
    :param user_phone: 用户电话 (User phone)
    :return: ResumeOut Pydantic model
    """
    
    system_prompt = load_system_prompt()

    # 构建用户输入 Prompt
    # Build User Prompt
    user_content = f"""
    用户信息 (User Info)：
    Name: {user_name}
    Email: {user_email}
    Phone: {user_phone}

    用户原始输入材料 (Raw Input)：
    {raw_text}
    """


    # 调用 ChatCompletion (使用 tool_calls/function_calling 的 Structured Outputs 或者是 json_object)
    # 本例使用最新的 beta.parse (Structured Outputs)
    try:
        completion = client.beta.chat.completions.parse(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            response_format=ResumeOut,
        )
        
        message = completion.choices[0].message
        if message.parsed:
            return message.parsed
        else:
            # Fallback (Refusal)
            print("Refusal:", message.refusal)
            return ResumeOut(
                personal_info={"name": user_name, "email": user_email, "phone": user_phone},
                summary="AI无法生成简历，请检查输入。(AI failed to generate resume)",
                education=[], work_experience=[], skills=[]
            )

    except Exception as e:
        print(f"OpenAI API Error: {e}")
        # 返回空对象以防崩溃
        return ResumeOut(
            personal_info={"name": user_name, "email": user_email, "phone": user_phone},
            summary=f"Error generating resume: {e}",
            education=[], work_experience=[], skills=[]
        )
