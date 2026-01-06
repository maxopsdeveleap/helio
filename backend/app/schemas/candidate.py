from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# Nested schemas for related data
class CandidateSkillSchema(BaseModel):
    skill_name: str

    class Config:
        from_attributes = True

class CandidateExperienceSchema(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    responsibilities: Optional[List[str]] = []
    order_index: int = 0

    class Config:
        from_attributes = True

class CandidateEducationSchema(BaseModel):
    degree: str
    field_of_study: Optional[str] = None
    institution: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None
    order_index: int = 0

    class Config:
        from_attributes = True

class CandidateCertificationSchema(BaseModel):
    name: str
    issuer: str
    year: Optional[int] = None

    class Config:
        from_attributes = True

class CandidateLanguageSchema(BaseModel):
    language: str
    proficiency: str

    class Config:
        from_attributes = True

class CVDocumentSchema(BaseModel):
    file_path: str
    file_name: str
    file_type: Optional[str] = None
    version: int = 1
    is_current: bool = True
    uploaded_at: datetime

    class Config:
        from_attributes = True

# Main Candidate schema (matches Exercise 1 JSON format)
class CandidateResponse(BaseModel):
    id: str
    status: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = []  # Flattened list of skill names
    experience: List[CandidateExperienceSchema] = []
    education: List[CandidateEducationSchema] = []
    certifications: List[CandidateCertificationSchema] = []
    languages: List[CandidateLanguageSchema] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Schema for creating/updating candidates
class CandidateCreate(BaseModel):
    id: str
    status: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    summary: Optional[str] = None

class CandidateUpdate(BaseModel):
    status: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    summary: Optional[str] = None
