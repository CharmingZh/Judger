from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field

class Contact(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    website: str = ""

class ExperienceItem(BaseModel):
    company: str = ""
    role: str = ""
    location: str = ""
    start: str = ""
    end: str = ""
    bullets: List[str] = Field(default_factory=list)

class EducationItem(BaseModel):
    school: str = ""
    degree: str = ""
    major: str = ""
    start: str = ""
    end: str = ""

class ProjectItem(BaseModel):
    name: str = ""
    role: str = ""
    start: str = ""
    end: str = ""
    bullets: List[str] = Field(default_factory=list)
    link: str = ""

class ResumeOut(BaseModel):
    language: str = Field(default="zh", description="zh or en")
    contact: Contact = Field(default_factory=Contact)
    headline: str = ""
    summary: str = ""
    skills: List[str] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    additional: List[str] = Field(default_factory=list)
