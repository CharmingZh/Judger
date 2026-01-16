from __future__ import annotations

import json
import os
import re
from typing import Any, Dict

from openai import OpenAI
import httpx

from .config import OPENAI_MODEL, OPENAI_API_KEY
from .schemas import ResumeOut

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """\
你是资深职业规划师与简历写作专家。
你将基于用户提供的资料（可能包含“结构化字段 + 模糊/自由文本 + JD”）生成一份可投递的简历。
硬性规则：
1) 绝对不编造经历、公司、学校、日期、项目；如果缺失信息就留空或省略该条目。
2) 尽量量化成果（如果用户给了数字才用数字；没有数字就用更稳健的描述）。
3) 用岗位JD的关键词做贴合，但不要堆砌。
4) 最终只输出 JSON（不要输出多余解释文字）。
JSON 必须符合 ResumeOut 结构。
"""

def _extract_json(text: str) -> str:
    """
    兜底：有些模型可能会在 JSON 前后加说明文字，这里把第一个 {...} 抠出来。
    """
    if not text:
        return "{}"
    m = re.search(r"\{.*\}", text, flags=re.S)
    return m.group(0) if m else text

def generate_resume(*, profile_fields: Dict[str, Any], free_text: str, job_desc: str, language: str = "zh") -> ResumeOut:
    user_payload = {
        "language": language,
        "profile_fields": profile_fields,
        "free_text": free_text,
        "job_description": job_desc,
        "note": "如果结构化字段与自由文本冲突，以结构化字段为准。",
    }

    # 用 Chat Completions 生成 JSON
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
    ]

    # 尽量让模型输出纯 JSON
    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.2,
            # 有些 SDK/模型支持这个；不支持也不会影响大逻辑（会走 except 或仍返回文本）
            response_format={"type": "json_object"},
        )
    except Exception:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.2,
        )

    content = resp.choices[0].message.content or "{}"
    content = _extract_json(content)
    return ResumeOut.model_validate_json(content)
