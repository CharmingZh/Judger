from __future__ import annotations

from passlib.context import CryptContext
from sqlalchemy.orm import Session
from . import models_

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

def get_user_by_email(db: Session, email: str) -> models_.User | None:
    return db.query(models_.User).filter(models_.User.email == email.lower().strip()).first()

def create_user(db: Session, email: str, password: str) -> models_.User:
    user = models_.User(email=email.lower().strip(), password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
