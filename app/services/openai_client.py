from __future__ import annotations

import json
from typing import Any, Dict

from openai import OpenAI
from ..core.config import settings
from ..core.schemas import ResumeOut

# 初始化 OpenAI 客户端 (使用 core/config 中的配置)
# Initialize OpenAI Client using core/config settings
client = OpenAI(api_key=settings.openai_api_key)

SYSTEM_PROMPT = """\
你是资深职业规划师与简历写作专家。
你将基于用户提供的资料（可能包含“结构化字段 + 模糊/自由文本 + JD”）生成一份可投递的简历。
硬性规则：
1) 绝对不编造经历、公司、学校、日期、项目；如果缺失信息就留空或省略该条目。
2) 尽量量化成果（如果用户给了数字才用数字；没有数字就用更稳健的描述）。
3) 语言风格专业、干练。
4) 输出必须严格符合提供的 JSON Schema。
"""

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
    
    # 构建用户输入 Prompt
    # Build User Prompt
    user_content = f"""
    用户信息：
    Name: {user_name}
    Email: {user_email}
    Phone: {user_phone}

    用户原始输入材料：
    {raw_text}
    """

    # 调用 ChatCompletion (使用 tool_calls/function_calling 的 Structured Outputs 或者是 json_object)
    # 本例使用最新的 beta.parse (Structured Outputs)
    try:
        completion = client.beta.chat.completions.parse(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
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
