from __future__ import annotations
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from ..core import models

# 密码哈希上下文
# Password Hashing Context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    加密密码
    Hash Password
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    Verify Password
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_user_by_email(db: Session, email: str) -> models.User | None:
    """
    通过邮箱查找用户
    Find user by email
    """
    return db.query(models.User).filter(models.User.email == email.lower().strip()).first()

def create_user(db: Session, email: str, password: str) -> models.User:
    """
    创建新用户
    Create new user
    """
    user = models.User(email=email.lower().strip(), password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
