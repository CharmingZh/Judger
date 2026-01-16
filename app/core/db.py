from __future__ import annotations
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import settings

# 数据库连接参数
# SQLite 需要 check_same_thread=False，其他数据库不需要
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

# 创建数据库引擎
# echo=False 表示不打印每条 SQL 语句
engine = create_engine(settings.database_url, echo=False, connect_args=connect_args)

# 创建会话工厂
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    """
    SQLAlchemy 声明式基类
    Declarative Base Class
    """
    pass

def get_db():
    """
    获取数据库会话生成器 (Dependency)
    Get Database Session Generator
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
