from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from .database import Base

class Position(Base):
    __tablename__ = "positions"

    id = Column(String(50), primary_key=True)
    status = Column(String(20), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False, index=True)
    location = Column(String(255))
    work_arrangement = Column(String(100))
    experience = Column(String(100))
    description = Column(Text, nullable=False)
    compensation = Column(String(255))
    timeline = Column(String(100))
    urgency = Column(String(20), index=True)
    contact_person_name = Column(String(255))
    contact_person_title = Column(String(255))
    contact_person_email = Column(String(255))
    notes = Column(Text)
    embedding = Column(Vector(1024))
    embedding_text = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    requirements = relationship("PositionRequirement", back_populates="position", cascade="all, delete-orphan")
    responsibilities = relationship("PositionResponsibility", back_populates="position", cascade="all, delete-orphan")
    skills = relationship("PositionSkill", back_populates="position", cascade="all, delete-orphan")
    candidates = relationship("CandidatePosition", back_populates="position")


class PositionRequirement(Base):
    __tablename__ = "position_requirements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    position_id = Column(String(50), ForeignKey("positions.id", ondelete="CASCADE"), nullable=False, index=True)
    requirement = Column(Text, nullable=False)
    is_required = Column(Boolean, default=True)
    order_index = Column(Integer, default=0)

    # Relationship
    position = relationship("Position", back_populates="requirements")


class PositionResponsibility(Base):
    __tablename__ = "position_responsibilities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    position_id = Column(String(50), ForeignKey("positions.id", ondelete="CASCADE"), nullable=False, index=True)
    responsibility = Column(Text, nullable=False)
    order_index = Column(Integer, default=0)

    # Relationship
    position = relationship("Position", back_populates="responsibilities")


class PositionSkill(Base):
    __tablename__ = "position_skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    position_id = Column(String(50), ForeignKey("positions.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name = Column(String(100), nullable=False, index=True)

    # Relationship
    position = relationship("Position", back_populates="skills")


class CandidatePosition(Base):
    __tablename__ = "candidate_positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(String(50), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    position_id = Column(String(50), ForeignKey("positions.id", ondelete="CASCADE"), nullable=False, index=True)
    application_status = Column(String(50))
    applied_at = Column(TIMESTAMP, server_default=func.now())
    notes = Column(Text)

    # Relationships
    candidate = relationship("Candidate", back_populates="positions")
    position = relationship("Position", back_populates="candidates")
