from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# Nested schemas for related data
class PositionRequirementSchema(BaseModel):
    requirement: str
    is_required: bool = True
    order_index: int = 0

    class Config:
        from_attributes = True

class PositionResponsibilitySchema(BaseModel):
    responsibility: str
    order_index: int = 0

    class Config:
        from_attributes = True

class PositionSkillSchema(BaseModel):
    skill_name: str

    class Config:
        from_attributes = True

class ContactPersonSchema(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None

# Main Position schema (matches Exercise 1 JSON format)
class PositionResponse(BaseModel):
    id: str
    status: str
    title: str
    company: str
    location: Optional[str] = None
    work_arrangement: Optional[str] = None
    experience: Optional[str] = None
    description: str
    compensation: Optional[str] = None
    timeline: Optional[str] = None
    urgency: Optional[str] = None
    contact_person_name: Optional[str] = None
    contact_person_title: Optional[str] = None
    contact_person_email: Optional[str] = None
    notes: Optional[str] = None
    requirements: List[str] = []  # Flattened list of requirement texts
    nice_to_have: List[str] = []  # Optional requirements
    responsibilities: List[str] = []  # Flattened list of responsibility texts
    skills: List[str] = []  # Flattened list of skill names
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Schema for creating positions
class PositionCreate(BaseModel):
    id: str
    status: str
    title: str
    company: str
    location: Optional[str] = None
    work_arrangement: Optional[str] = None
    experience: Optional[str] = None
    description: str
    compensation: Optional[str] = None
    timeline: Optional[str] = None
    urgency: Optional[str] = None
    contact_person_name: Optional[str] = None
    contact_person_title: Optional[str] = None
    contact_person_email: Optional[str] = None
    notes: Optional[str] = None

# Schema for updating positions
class PositionUpdate(BaseModel):
    status: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    work_arrangement: Optional[str] = None
    experience: Optional[str] = None
    description: Optional[str] = None
    compensation: Optional[str] = None
    timeline: Optional[str] = None
    urgency: Optional[str] = None
    contact_person_name: Optional[str] = None
    contact_person_title: Optional[str] = None
    contact_person_email: Optional[str] = None
    notes: Optional[str] = None
