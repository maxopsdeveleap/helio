from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.models import get_db
from app.models.candidate import Candidate, CandidateSkill, CandidateExperience, CandidateEducation, CandidateCertification, CandidateLanguage
from app.schemas.candidate import CandidateResponse, CandidateCreate, CandidateUpdate

router = APIRouter()

def format_candidate_response(candidate: Candidate) -> dict:
    """Convert database candidate to JSON format matching Exercise 1"""
    return {
        "id": candidate.id,
        "status": candidate.status,
        "first_name": candidate.first_name,
        "last_name": candidate.last_name,
        "email": candidate.email,
        "phone": candidate.phone,
        "location": candidate.location,
        "linkedin": candidate.linkedin,
        "github": candidate.github,
        "summary": candidate.summary,
        "skills": [skill.skill_name for skill in candidate.skills],
        "experience": [
            {
                "title": exp.title,
                "company": exp.company,
                "location": exp.location,
                "start_date": exp.start_date,
                "end_date": exp.end_date,
                "responsibilities": exp.responsibilities or []
            }
            for exp in sorted(candidate.experience, key=lambda x: x.order_index)
        ],
        "education": [
            {
                "degree": edu.degree,
                "field_of_study": edu.field_of_study,
                "institution": edu.institution,
                "start_date": edu.start_date,
                "end_date": edu.end_date,
                "status": edu.status
            }
            for edu in sorted(candidate.education, key=lambda x: x.order_index)
        ],
        "certifications": [
            {
                "name": cert.name,
                "issuer": cert.issuer,
                "year": cert.year
            }
            for cert in candidate.certifications
        ],
        "languages": [
            {
                "language": lang.language,
                "proficiency": lang.proficiency
            }
            for lang in candidate.languages
        ],
        "created_at": candidate.created_at,
        "updated_at": candidate.updated_at
    }

@router.get("/", response_model=List[dict])
async def get_all_candidates(db: Session = Depends(get_db)):
    """Get all candidates"""
    candidates = db.query(Candidate).all()
    return [format_candidate_response(candidate) for candidate in candidates]

@router.get("/{candidate_id}", response_model=dict)
async def get_candidate(candidate_id: str, db: Session = Depends(get_db)):
    """Get a single candidate by ID"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return format_candidate_response(candidate)

@router.post("/", response_model=dict, status_code=201)
async def create_candidate(candidate_data: CandidateCreate, db: Session = Depends(get_db)):
    """Create a new candidate"""
    # Check if candidate already exists
    existing = db.query(Candidate).filter(Candidate.id == candidate_data.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Candidate with this ID already exists")

    # Create candidate
    candidate = Candidate(**candidate_data.dict())
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    return format_candidate_response(candidate)

@router.put("/{candidate_id}", response_model=dict)
async def update_candidate(candidate_id: str, candidate_data: CandidateUpdate, db: Session = Depends(get_db)):
    """Update an existing candidate"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Update only provided fields
    update_data = candidate_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(candidate, key, value)

    db.commit()
    db.refresh(candidate)

    return format_candidate_response(candidate)

@router.delete("/{candidate_id}", status_code=204)
async def delete_candidate(candidate_id: str, db: Session = Depends(get_db)):
    """Delete a candidate"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    db.delete(candidate)
    db.commit()

    return None
