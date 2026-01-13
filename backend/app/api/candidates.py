from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path
import tempfile
import os
from app.models import get_db
from app.models.candidate import Candidate, CandidateSkill, CandidateExperience, CandidateEducation, CandidateCertification, CandidateLanguage
from app.schemas.candidate import CandidateResponse, CandidateCreate, CandidateUpdate
from app.services.similarity_service import find_similar_positions
from app.services.matching_service import explain_multiple_matches

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

@router.get("/{candidate_id}/suggest-positions", response_model=List[dict])
async def suggest_positions_for_candidate(candidate_id: str, db: Session = Depends(get_db)):
    """
    Suggest top 3 positions for a candidate using semantic similarity.

    Returns positions ranked by how well they match the candidate's skills
    and experience, with AI-generated explanations for each match.
    """
    try:
        # Get candidate data
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # Get candidate as dict for LLM
        candidate_dict = format_candidate_response(candidate)

        # Find similar positions
        positions = find_similar_positions(
            candidate_id=candidate_id,
            db=db,
            limit=3,
            min_similarity=0.5  # Lower threshold for more results
        )

        # Generate explanations using LLM
        positions_with_explanations = explain_multiple_matches(
            candidate=candidate_dict,
            positions_with_scores=positions
        )

        return positions_with_explanations

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find similar positions: {str(e)}")


@router.post("/ingest", response_model=dict, status_code=201)
async def ingest_candidate_cv(
    file: UploadFile = File(...),
    name: str = Form(...),
    email: str = Form(...),
    position_id: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Ingest a candidate's CV and create candidate profile.

    Reuses Exercise 3 CV ingestion logic.
    """
    # Import here to avoid circular dependencies
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
    from ingest_cv import ingest_cv

    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = Path(tmp_file.name)

    try:
        # Ingest CV using Exercise 3 logic
        is_duplicate = False
        try:
            candidate_id = ingest_cv(tmp_path)
        except Exception as ingest_error:
            # Check if this is a duplicate candidate error
            error_msg = str(ingest_error)
            if "duplicate key value violates unique constraint" in error_msg or "UniqueViolation" in error_msg:
                # Extract email from error message
                import re
                email_match = re.search(r'Key \(email\)=\(([^)]+)\)', error_msg)
                duplicate_email = email_match.group(1) if email_match else email

                # Find existing candidate by email
                candidate = db.query(Candidate).filter(Candidate.email == duplicate_email).first()
                if candidate:
                    candidate_id = candidate.id
                    is_duplicate = True
                else:
                    raise ingest_error
            else:
                raise ingest_error

        # Get created candidate
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=500, detail="Candidate created but not found")

        # Always get position matches (regardless of position_id)
        position_matches = []
        from app.services.similarity_service import find_similar_positions
        try:
            position_matches = find_similar_positions(
                candidate_id=candidate_id,
                db=db,
                limit=3,
                min_similarity=0.5
            )
        except Exception as e:
            # Don't fail if matching fails
            pass

        return {
            "candidate_id": candidate_id,
            "candidate": format_candidate_response(candidate),
            "position_matches": position_matches,
            "message": f"Candidate already exists - retrieved existing profile" if is_duplicate else f"Candidate {name} ingested successfully",
            "duplicate": is_duplicate
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest CV: {str(e)}")
    finally:
        # Clean up temp file
        if tmp_path.exists():
            os.unlink(tmp_path)
