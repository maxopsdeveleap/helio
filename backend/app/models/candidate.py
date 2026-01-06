from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, ForeignKey, ARRAY, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String(50), primary_key=True)
    status = Column(String(20), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(50))
    location = Column(String(255))
    linkedin = Column(String(255))
    github = Column(String(255))
    summary = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    skills = relationship("CandidateSkill", back_populates="candidate", cascade="all, delete-orphan")
    experience = relationship("CandidateExperience", back_populates="candidate", cascade="all, delete-orphan")
    education = relationship("CandidateEducation", back_populates="candidate", cascade="all, delete-orphan")
    certifications = relationship("CandidateCertification", back_populates="candidate", cascade="all, delete-orphan")
    languages = relationship("CandidateLanguage", back_populates="candidate", cascade="all, delete-orphan")
    cv_documents = relationship("CVDocument", back_populates="candidate", cascade="all, delete-orphan")
    positions = relationship("CandidatePosition", back_populates="candidate")


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(String(50), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name = Column(String(100), nullable=False, index=True)

    # Relationship
    candidate = relationship("Candidate", back_populates="skills")


class CandidateExperience(Base):
    __tablename__ = "candidate_experience"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(String(50), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255))
    start_date = Column(String(50))
    end_date = Column(String(50))
    responsibilities = Column(ARRAY(Text))
    order_index = Column(Integer, default=0)

    # Relationship
    candidate = relationship("Candidate", back_populates="experience")


class CandidateEducation(Base):
    __tablename__ = "candidate_education"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(String(50), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    degree = Column(String(255), nullable=False)
    field_of_study = Column(String(255))
    institution = Column(String(255), nullable=False)
    start_date = Column(String(50))
    end_date = Column(String(50))
    status = Column(String(50))
    order_index = Column(Integer, default=0)

    # Relationship
    candidate = relationship("Candidate", back_populates="education")


class CandidateCertification(Base):
    __tablename__ = "candidate_certifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(String(50), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    issuer = Column(String(255), nullable=False)
    year = Column(Integer)

    # Relationship
    candidate = relationship("Candidate", back_populates="certifications")


class CandidateLanguage(Base):
    __tablename__ = "candidate_languages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(String(50), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    language = Column(String(100), nullable=False)
    proficiency = Column(String(50), nullable=False)

    # Relationship
    candidate = relationship("Candidate", back_populates="languages")


class CVDocument(Base):
    __tablename__ = "cv_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(String(50), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(Text, nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50))
    version = Column(Integer, default=1)
    is_current = Column(Boolean, default=True)
    uploaded_at = Column(TIMESTAMP, server_default=func.now())

    # Relationship
    candidate = relationship("Candidate", back_populates="cv_documents")
