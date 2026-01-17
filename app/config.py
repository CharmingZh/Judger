from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-2024-08-06")
SESSION_SECRET = os.getenv("SESSION_SECRET", "change-me")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
